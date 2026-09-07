"""Support for MIMO ASR speech-to-text with local VAD."""
from __future__ import annotations

import asyncio
import base64
import logging
import math
import struct
from array import array
from collections.abc import AsyncIterable

from openai import AsyncOpenAI

from homeassistant.components.stt import (
    AudioBitRates,
    AudioChannels,
    AudioCodecs,
    AudioFormats,
    AudioSampleRates,
    SpeechMetadata,
    SpeechResult,
    SpeechResultState,
    SpeechToTextEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    DEFAULT_BASE_URL,
    CONF_LANGUAGE,
    DEFAULT_LANGUAGE,
    CONF_MODEL,
    DEFAULT_MODEL,
    CONF_SILENCE_SECONDS,
    CONF_REQUEST_TIMEOUT,
    DEFAULT_SILENCE_SECONDS,
    DEFAULT_REQUEST_TIMEOUT,
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE_CODE,
    FRAME_BYTES,
    SPEECH_RMS_THRESHOLD,
    SPEECH_START_SECONDS,
    MIN_COMMAND_SECONDS,
    MAX_AUDIO_SECONDS,
    SILENCE_PAD_SECONDS,
)

_LOGGER = logging.getLogger(__name__)

_SAMPLE_RATE = 16000
_SAMPLE_WIDTH = 2  # 16-bit
_FRAME_SECONDS = FRAME_BYTES / (_SAMPLE_RATE * _SAMPLE_WIDTH)


def create_wav_header(sample_rate: int, channels: int, bits_per_sample: int, data_size: int) -> bytes:
    """生成标准 WAV 文件头 (44 字节)。"""
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    fmt_chunk_size = 16
    audio_format = 1  # PCM

    header = b""
    # RIFF 块
    header += b"RIFF"
    header += struct.pack("<I", 36 + data_size)  # 总长度 (不包括 RIFF 和 size 字段)
    header += b"WAVE"
    # fmt 块
    header += b"fmt "
    header += struct.pack("<I", fmt_chunk_size)
    header += struct.pack("<H", audio_format)
    header += struct.pack("<H", channels)
    header += struct.pack("<I", sample_rate)
    header += struct.pack("<I", byte_rate)
    header += struct.pack("<H", block_align)
    header += struct.pack("<H", bits_per_sample)
    # data 块
    header += b"data"
    header += struct.pack("<I", data_size)
    return header


def _frame_rms(frame: bytes) -> float:
    """计算 16-bit PCM 帧的均方根（能量）。"""
    samples = array("h")
    samples.frombytes(frame)
    if not samples:
        return 0.0
    return math.sqrt(sum(sample * sample for sample in samples) / len(samples))


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up MIMO ASR entity from a config entry."""
    _LOGGER.info("Setting up MIMO ASR entity")
    async_add_entities([MimoASR(hass, config_entry)])


class MimoASR(SpeechToTextEntity):
    """Representation of a MIMO ASR entity."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize the MIMO ASR entity."""
        self.hass = hass
        self._config_entry = config_entry
        self._api_key: str = config_entry.data[CONF_API_KEY]
        self._base_url: str = config_entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL)
        self._language: str = config_entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
        self._model: str = config_entry.data.get(CONF_MODEL, DEFAULT_MODEL)

        self._client: AsyncOpenAI | None = None

        self._attr_name = "小米 MIMO ASR"
        self._attr_unique_id = f"{config_entry.entry_id}"

        _LOGGER.debug("MIMO ASR entity initialized")

    async def _async_get_client(self) -> AsyncOpenAI:
        """异步获取客户端，在 executor 中创建以避免阻塞事件循环。"""
        if self._client is None:
            _LOGGER.debug("Creating AsyncOpenAI client in executor")
            api_key = self._api_key
            base_url = self._base_url

            def _create_client():
                return AsyncOpenAI(
                    api_key=api_key,
                    base_url=base_url,
                )

            self._client = await self.hass.async_add_executor_job(_create_client)
        return self._client

    @property
    def supported_languages(self) -> list[str]:
        return SUPPORTED_LANGUAGES

    @property
    def default_language(self) -> str:
        return DEFAULT_LANGUAGE_CODE

    @property
    def supported_formats(self) -> list[AudioFormats]:
        return [AudioFormats.WAV]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        return [AudioCodecs.PCM]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        return [AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        return [AudioSampleRates.SAMPLERATE_16000]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        return [AudioChannels.CHANNEL_MONO]

    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> SpeechResult:
        _LOGGER.debug(
            "Processing audio stream. Language: %s, Format: %s, Codec: %s",
            metadata.language,
            metadata.format,
            metadata.codec,
        )

        if metadata.language not in SUPPORTED_LANGUAGES:
            _LOGGER.error("Unsupported language: %s", metadata.language)
            return SpeechResult("", SpeechResultState.ERROR)

        if metadata.format != AudioFormats.WAV:
            _LOGGER.error("Unsupported format: %s. Only WAV is supported.", metadata.format)
            return SpeechResult("", SpeechResultState.ERROR)

        options = self._config_entry.options
        silence_seconds = float(
            options.get(CONF_SILENCE_SECONDS, DEFAULT_SILENCE_SECONDS)
        )
        request_timeout = float(
            options.get(CONF_REQUEST_TIMEOUT, DEFAULT_REQUEST_TIMEOUT)
        )

        # 流式消费音频（实际为 PCM 裸流），逐帧做能量检测
        chunks: list[bytes] = []
        pending = bytearray()
        frames: list[bool] = []  # 每帧是否为语音
        first_speech_frame: int | None = None
        last_speech_frame: int | None = None
        speech_seconds = 0.0
        trailing_silence_seconds = 0.0
        stop_early = False

        try:
            async for chunk in stream:
                chunks.append(chunk)
                pending.extend(chunk)
                while len(pending) >= FRAME_BYTES:
                    frame = bytes(pending[:FRAME_BYTES])
                    pending = pending[FRAME_BYTES:]

                    rms = _frame_rms(frame)
                    is_speech = rms >= SPEECH_RMS_THRESHOLD
                    frames.append(is_speech)

                    if is_speech:
                        last_speech_frame = len(frames) - 1
                        if first_speech_frame is None:
                            first_speech_frame = len(frames) - 1
                            _LOGGER.debug("Speech detected at frame %d (RMS=%.1f)", first_speech_frame, rms)
                        trailing_silence_seconds = 0.0
                    else:
                        if first_speech_frame is not None:
                            trailing_silence_seconds += _FRAME_SECONDS

                    # 计算已录制的语音时长
                    if first_speech_frame is not None:
                        speech_seconds = (len(frames) - first_speech_frame) * _FRAME_SECONDS

                    # 提前结束条件
                    if (
                        first_speech_frame is not None
                        and speech_seconds >= MIN_COMMAND_SECONDS
                        and trailing_silence_seconds >= silence_seconds
                    ):
                        _LOGGER.debug(
                            "Early stop: speech=%.2fs, trailing_silence=%.2fs",
                            speech_seconds,
                            trailing_silence_seconds,
                        )
                        stop_early = True
                        break

                    # 最大时长限制
                    if len(frames) * _FRAME_SECONDS >= MAX_AUDIO_SECONDS:
                        _LOGGER.debug("Max audio duration reached: %.2fs", MAX_AUDIO_SECONDS)
                        stop_early = True
                        break

                if stop_early:
                    break

        except Exception as err:
            _LOGGER.error("Error reading audio stream: %s", err)
            return SpeechResult("", SpeechResultState.ERROR)

        # 计算总音频时长
        total_seconds = len(frames) * _FRAME_SECONDS
        _LOGGER.debug(
            "Audio stats: total=%.2fs, speech=%.2fs, frames=%d",
            total_seconds,
            speech_seconds,
            len(frames),
        )

        # 如果没有检测到语音，返回空结果
        if first_speech_frame is None:
            _LOGGER.warning("No speech detected in audio stream")
            return SpeechResult("", SpeechResultState.SUCCESS)

        # 裁剪音频：只保留语音部分（带静音余量）
        pad_frames = int(SILENCE_PAD_SECONDS / _FRAME_SECONDS)
        start_frame = max(0, first_speech_frame - pad_frames)
        end_frame = min(len(frames), (last_speech_frame or len(frames) - 1) + pad_frames + 1)

        # 提取裁剪后的音频数据
        cropped_chunks = []
        frame_index = 0
        for chunk in chunks:
            chunk_frames = len(chunk) // FRAME_BYTES
            if frame_index + chunk_frames <= start_frame:
                frame_index += chunk_frames
                continue
            if frame_index >= end_frame:
                break

            # 处理这个 chunk 中的帧
            for i in range(chunk_frames):
                if start_frame <= frame_index < end_frame:
                    start_byte = i * FRAME_BYTES
                    end_byte = start_byte + FRAME_BYTES
                    cropped_chunks.append(chunk[start_byte:end_byte])
                frame_index += 1

        if not cropped_chunks:
            _LOGGER.warning("No audio data after cropping")
            return SpeechResult("", SpeechResultState.SUCCESS)

        audio_data = b"".join(cropped_chunks)
        audio_seconds = len(audio_data) / (_SAMPLE_RATE * _SAMPLE_WIDTH)
        _LOGGER.debug(
            "Sending %.2fs of audio to MIMO ASR API",
            audio_seconds,
        )

        # 构建 WAV 文件
        wav_header = create_wav_header(
            sample_rate=_SAMPLE_RATE,
            channels=1,
            bits_per_sample=16,
            data_size=len(audio_data),
        )
        wav_data = wav_header + audio_data

        # 转换为 Base64
        audio_base64 = base64.b64encode(wav_data).decode("utf-8")
        data_url = f"data:audio/wav;base64,{audio_base64}"

        # 准备 API 请求
        request_data = {
            "model": self._model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": data_url
                            }
                        }
                    ]
                }
            ],
            "asr_options": {
                "language": self._language if self._language != "auto" else None
            }
        }

        # 调用 API
        try:
            client = await self._async_get_client()
            _LOGGER.debug("Sending request to MIMO ASR API")
            
            completion = await client.chat.completions.create(
                model=self._model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "input_audio",
                                "input_audio": {
                                    "data": data_url
                                }
                            }
                        ]
                    }
                ],
                extra_body={
                    "asr_options": {
                        "language": self._language if self._language != "auto" else None
                    }
                },
                timeout=request_timeout,
            )

            # 提取识别结果
            if completion.choices and completion.choices[0].message:
                text = completion.choices[0].message.content
                _LOGGER.debug("MIMO ASR result: %s", text)
                if text:
                    return SpeechResult(text, SpeechResultState.SUCCESS)
                else:
                    _LOGGER.warning("MIMO ASR returned empty text")
                    return SpeechResult("", SpeechResultState.SUCCESS)
            else:
                _LOGGER.error("No text in MIMO ASR response")
                return SpeechResult("", SpeechResultState.ERROR)

        except Exception as err:
            _LOGGER.error("MIMO ASR API error: %s", err)
            return SpeechResult("", SpeechResultState.ERROR)
