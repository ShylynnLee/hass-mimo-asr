"""Support for MIMO ASR speech-to-text."""
import base64
import logging
from collections.abc import AsyncIterable
from typing import Any

import openai
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
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    CONF_API_KEY,
    CONF_BASE_URL,
    DEFAULT_BASE_URL,
    CONF_LANGUAGE,
    DEFAULT_LANGUAGE,
    CONF_MODEL,
    DEFAULT_MODEL,
)

_LOGGER = logging.getLogger(__name__)


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

    client = openai.AsyncOpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    async_add_entities([MimoAsrSpeechToTextEntity(config_entry, client, language, model)])


class MimoAsrSpeechToTextEntity(SpeechToTextEntity):
    """MIMO ASR speech-to-text entity."""

    def __init__(
        self,
        config_entry: ConfigEntry,
        client: openai.AsyncOpenAI,
        language: str,
        model: str,
    ) -> None:
        """Init MIMO ASR STT entity."""
        self._attr_unique_id = f"{config_entry.entry_id}"
        self._attr_name = config_entry.title
        self._config_entry = config_entry
        self._client = client
        self._language = language
        self._model = model

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        return ["auto", "zh", "en"]

    @property
    def supported_formats(self) -> list[AudioFormats]:
        """Return a list of supported formats."""
        return [AudioFormats.WAV, AudioFormats.MP3]

    @property
    def supported_codecs(self) -> list[AudioCodecs]:
        """Return a list of supported codecs."""
        return [AudioCodecs.PCM, AudioCodecs.MP3]

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
            return SpeechResult(None, SpeechResultState.ERROR)

        try:
            # 根据音频格式确定MIME类型
            if metadata.format == AudioFormats.WAV:
                mime_type = "audio/wav"
            else:
                mime_type = "audio/mpeg"

            # 转换为Base64
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            data_url = f"data:{mime_type};base64,{audio_base64}"

            # 调用MIMO ASR API
            completion = await self._client.chat.completions.create(
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
                        "language": self._language
                    }
                }
            )

            # 提取识别结果
            if completion.choices and completion.choices[0].message:
                text = completion.choices[0].message.content
                return SpeechResult(text, SpeechResultState.SUCCESS)
            else:
                return SpeechResult(None, SpeechResultState.ERROR)

        except Exception as err:
            _LOGGER.error("MIMO ASR error: %s", err)
            return SpeechResult(None, SpeechResultState.ERROR)
