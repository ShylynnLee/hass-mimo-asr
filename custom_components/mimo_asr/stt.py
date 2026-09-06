"""Support for MIMO ASR speech-to-text."""
import base64
import logging
from typing import Any

import openai
from homeassistant.components.stt import (
    SpeechResult,
    SpeechResultState,
    SttProvider,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import CONF_API_KEY, CONF_BASE_URL, DEFAULT_BASE_URL, CONF_LANGUAGE, DEFAULT_LANGUAGE, CONF_MODEL, DEFAULT_MODEL

_LOGGER = logging.getLogger(__name__)

async def async_get_engine(hass: HomeAssistant, config: ConfigEntry) -> "MimoAsrProvider":
    """Set up MIMO ASR speech-to-text."""
    return MimoAsrProvider(hass, config)

class MimoAsrProvider(SttProvider):
    """MIMO ASR speech-to-text provider."""

    def __init__(self, hass: HomeAssistant, config: ConfigEntry) -> None:
        """Initialize MIMO ASR provider."""
        self.hass = hass
        self.config = config
        self.client = openai.AsyncOpenAI(
            api_key=config.data[CONF_API_KEY],
            base_url=config.data.get(CONF_BASE_URL, DEFAULT_BASE_URL)
        )
        self.language = config.data.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
        self.model = config.data.get(CONF_MODEL, DEFAULT_MODEL)

    @property
    def supported_languages(self) -> list[str]:
        """Return a list of supported languages."""
        return ["auto", "zh", "en"]

    @property
    def supported_formats(self) -> list[str]:
        """Return a list of supported formats."""
        return ["wav", "mp3"]

    @property
    def supported_codecs(self) -> list[str]:
        """Return a list of supported codecs."""
        return ["pcm", "mp3"]

    @property
    def supported_bit_rates(self) -> list[int]:
        """Return a list of supported bitrates."""
        return [16]

    @property
    def supported_sample_rates(self) -> list[int]:
        """Return a list of supported samplerates."""
        return [16000]

    @property
    def supported_channels(self) -> list[int]:
        """Return a list of supported channels."""
        return [1]

    async def async_process_audio_stream(
        self, metadata: Any, stream: Any
    ) -> SpeechResult:
        """Process an audio stream to STT service."""
        audio_data = b""
        async for chunk in stream:
            audio_data += chunk

        if not audio_data:
            return SpeechResult("", SpeechResultState.ERROR)

        try:
            # 根据音频格式确定MIME类型
            if metadata.format == "wav":
                mime_type = "audio/wav"
            else:
                mime_type = "audio/mpeg"

            # 转换为Base64
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            data_url = f"data:{mime_type};base64,{audio_base64}"

            # 调用MIMO ASR API
            completion = await self.client.chat.completions.create(
                model=self.model,
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
                        "language": self.language
                    }
                }
            )

            # 提取识别结果
            if completion.choices and completion.choices[0].message:
                text = completion.choices[0].message.content
                return SpeechResult(text, SpeechResultState.SUCCESS)
            else:
                return SpeechResult("", SpeechResultState.ERROR)

        except Exception as err:
            _LOGGER.error("MIMO ASR error: %s", err)
            return SpeechResult("", SpeechResultState.ERROR)
