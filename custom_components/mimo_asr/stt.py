"""Support for MIMO ASR speech-to-text."""
import base64
import io
import logging
import wave
from collections.abc import AsyncIterable
from typing import Any

import aiohttp
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
from homeassistant.const import CONF_API_KEY
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_BASE_URL,
    DEFAULT_BASE_URL,
    CONF_LANGUAGE,
    DEFAULT_LANGUAGE,
    CONF_MODEL,
    DEFAULT_MODEL,
)

_LOGGER = logging.getLogger(__name__)

TRANSCRIPTION_TIMEOUT = 30  # seconds


def encode_wav(data: bytes, channels: int, sample_rate: int) -> bytes:
    """Wrap raw PCM samples into a WAV container."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(channels)
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(data)
    return buffer.getvalue()


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up MIMO ASR speech-to-text entity."""
    api_key = config_entry.data[CONF_API_KEY]
    base_url = config_entry.data.get(CONF_BASE_URL, DEFAULT_BASE_URL)
    language = config_entry.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
    model = config_entry.data.get(CONF_MODEL, DEFAULT_MODEL)

    async_add_entities([MimoAsrSpeechToTextEntity(hass, api_key, base_url, language, model)])


class MimoAsrSpeechToTextEntity(SpeechToTextEntity):
    """MIMO ASR speech-to-text entity."""

    def __init__(
        self,
        hass: HomeAssistant,
        api_key: str,
        base_url: str,
        language: str,
        model: str,
    ) -> None:
        """Init MIMO ASR STT entity."""
        self._hass = hass
        self._api_key = api_key
        self._base_url = base_url.rstrip('/')
        self._language = language
        self._model = model
        self._attr_unique_id = f"mimo_asr_{model}"
        self._attr_name = f"MIMO ASR ({model})"

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        return ["auto", "zh", "en"]

    @property
    def supported_formats(self) -> list[AudioFormats]:
        """Return a list of supported formats."""
        return [AudioFormats.WAV]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        """Return a list of supported codecs."""
        return [AudioCodecs.PCM]

    @property
    def supported_bit_rates(self) -> list[AudioBitRates]:
        """Return a list of supported bitrates."""
        return [AudioBitRates.BITRATE_16]

    @property
    def supported_sample_rates(self) -> list[AudioSampleRates]:
        """Return a list of supported samplerates."""
        return [AudioSampleRates.SAMPLERATE_16000]

    @property
    def supported_channels(self) -> list[AudioChannels]:
        """Return a list of supported channels."""
        return [AudioChannels.CHANNEL_MONO]

    async def async_process_audio_stream(
        self, metadata: SpeechMetadata, stream: AsyncIterable[bytes]
    ) -> SpeechResult:
        """Process an audio stream to STT service."""
        audio_data = b""
        async for chunk in stream:
            audio_data += chunk

        if not audio_data:
            _LOGGER.error("No audio data received")
            return SpeechResult(None, SpeechResultState.ERROR)

        try:
            # 将原始PCM音频编码为WAV容器
            wav_data = await self._hass.async_add_executor_job(
                encode_wav,
                audio_data,
                int(metadata.channel),
                int(metadata.sample_rate),
            )
            
            # 转换为Base64
            audio_base64 = base64.b64encode(wav_data).decode("utf-8")
            data_url = f"data:audio/wav;base64,{audio_base64}"

            _LOGGER.debug(
                "Encoded %.2f MB of audio to WAV, base64 length: %d",
                len(wav_data) / (1024 * 1024),
                len(audio_base64),
            )

            # 准备请求数据
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
                    "language": self._language
                }
            }
            
            # 构建请求URL
            url = f"{self._base_url}/chat/completions"
            
            # 设置请求头
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}"
            }
            
            _LOGGER.debug("Sending request to MIMO ASR API: %s", url)
            
            # 发送请求
            session = async_get_clientsession(self._hass)
            async with session.post(
                url,
                json=request_data,
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=TRANSCRIPTION_TIMEOUT),
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    _LOGGER.error("MIMO ASR API error %d: %s", response.status, error_text)
                    return SpeechResult(None, SpeechResultState.ERROR)
                
                result = await response.json()
                
                # 提取识别结果
                if "choices" in result and len(result["choices"]) > 0:
                    message = result["choices"][0].get("message", {})
                    text = message.get("content", "")
                    _LOGGER.debug("MIMO ASR result: %s", text)
                    if text:
                        return SpeechResult(text, SpeechResultState.SUCCESS)
                    else:
                        _LOGGER.warning("MIMO ASR returned empty text")
                        return SpeechResult(None, SpeechResultState.ERROR)
                else:
                    _LOGGER.error("No text in MIMO ASR response: %s", result)
                    return SpeechResult(None, SpeechResultState.ERROR)

        except aiohttp.ClientError as err:
            _LOGGER.error("MIMO ASR network error: %s", err)
            return SpeechResult(None, SpeechResultState.ERROR)
        except asyncio.TimeoutError:
            _LOGGER.error("MIMO ASR request timed out")
            return SpeechResult(None, SpeechResultState.ERROR)
        except Exception as err:
            _LOGGER.error("MIMO ASR unexpected error: %s", err)
            return SpeechResult(None, SpeechResultState.ERROR)
