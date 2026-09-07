"""Constants for the MIMO ASR integration."""
DOMAIN = "mimo_asr"
NAME = "小米 MIMO ASR"

# API 配置
CONF_API_KEY = "api_key"
CONF_BASE_URL = "base_url"
DEFAULT_BASE_URL = "https://api.xiaomimimo.com/v1"
CONF_LANGUAGE = "language"
DEFAULT_LANGUAGE = "zh"
CONF_MODEL = "model"
DEFAULT_MODEL = "mimo-v2.5-asr"

# 可配置参数
CONF_SILENCE_SECONDS = "silence_seconds"
CONF_REQUEST_TIMEOUT = "request_timeout"

# 默认值
DEFAULT_SILENCE_SECONDS = 0.5
DEFAULT_REQUEST_TIMEOUT = 15

# 参数范围
SILENCE_SECONDS_MIN = 0.3
SILENCE_SECONDS_MAX = 1.5
REQUEST_TIMEOUT_MIN = 5
REQUEST_TIMEOUT_MAX = 60

# 支持的语言 (BCP47 格式)
SUPPORTED_LANGUAGES = ["zh", "zh-CN", "en"]
DEFAULT_LANGUAGE_CODE = "zh"

# VAD 参数（16kHz / 16bit / 单声道 PCM）
FRAME_BYTES = 320  # 10ms 一帧 (16000Hz * 2字节 * 0.01s)
SPEECH_RMS_THRESHOLD = 300  # 帧 RMS 达到该值视为语音
SPEECH_START_SECONDS = 0.3  # 累计语音达到该时长才进入"指令中"状态
MIN_COMMAND_SECONDS = 1.0  # 首个语音帧起总时长达到该值后才允许静音提前结束
MAX_AUDIO_SECONDS = 30.0  # 音频最长保留时长，超出强制截断
SILENCE_PAD_SECONDS = 0.2  # 裁剪后首尾保留的静音余量
