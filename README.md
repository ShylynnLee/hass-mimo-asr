# 小米 MIMO ASR - Home Assistant 语音识别插件

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

这是一个 Home Assistant 自定义集成，用于接入小米 MIMO ASR 语音识别服务。

## ✨ 功能特性

### v1.0.1 新功能
- **本地 VAD（语音活动检测）**：智能检测语音，减少无效 API 调用
- **流式音频处理**：内存效率高，响应速度快
- **可配置参数**：静音阈值、请求超时等可调
- **单实例限制**：防止重复配置
- **详细的日志系统**：便于调试和问题排查

### 核心功能
- 支持中文、英文及自动语种检测
- 支持 WAV 音频格式
- 基于 OpenAI 兼容 API，稳定可靠
- 支持 HACS 安装和更新
- 完美集成 Home Assistant 语音助手（Assist Pipeline）

## 📋 前提条件

- Home Assistant 2024.1 或更高版本
- 有效的 [Mimo API Key](https://mimo.mi.com/)（需注册并获取）

## 📦 安装

### 方法一：通过 HACS 安装（推荐）

1. 确保你已经安装了 [HACS](https://hacs.xyz/)。
2. 在 HACS 中点击右上角菜单 → **Custom repositories**。
3. 添加仓库地址：`https://github.com/ShylynnLee/hass-mimo-asr`，类别选择 **Integration**。
4. 点击 **Install** 安装。
5. 重启 Home Assistant。

### 方法二：手动安装

1. 下载本仓库所有文件，放入 `custom_components/mimo_asr/` 目录。
2. 重启 Home Assistant。

## ⚙️ 配置

### 基础配置
1. 进入 **设置** → **设备与服务** → **添加集成**。
2. 搜索 **小米 MIMO ASR**，点击进入。
3. 输入你的 **API Key**（从 Mimo 平台获取）。
4. 可选：配置 API 端点、语言、模型。
5. 点击确认，完成配置。

### 高级配置
配置完成后，可以调整以下参数：
- **静音检测秒数**：语音结束后等待多久才停止录音（0.3-1.5秒）
- **请求超时**：API 请求超时时间（5-60秒）

## 🗣️ 在语音助手中使用

配置完成后，你需要将本 STT 引擎设置为默认语音助手的识别器：

1. 进入 **设置** → **语音助手**。
2. 选择你的语音助手，点击 **配置**。
3. 在 **Speech-to-text** 部分，选择 **小米 MIMO ASR**。
4. 保存配置。

## 🔧 技术特性

### 本地 VAD（语音活动检测）
- **能量检测**：通过音频能量阈值判断是否为语音
- **静音检测**：语音结束后自动停止录音
- **智能截断**：只发送有效语音部分，节省带宽
- **最大时长限制**：防止过长的音频请求

### 音频处理
- **流式处理**：逐帧分析音频，内存效率高
- **WAV 编码**：标准 WAV 格式，兼容性好
- **16kHz/16bit/单声道**：标准语音识别参数

### 错误处理
- **详细的日志**：分级日志记录，便于调试
- **优雅降级**：网络错误时提供有用的错误信息
- **参数验证**：配置时验证 API Key 有效性

## 📊 性能优化

### 减少 API 调用
- 本地 VAD 检测语音活动
- 智能截断，只发送有效语音
- 静音检测，提前结束录音

### 内存优化
- 流式处理音频数据
- 及时释放无用内存
- 限制最大音频时长

## 🐛 故障排除

### 常见问题

#### 1. 语音识别不工作
- 检查 API Key 是否正确
- 确认网络连接正常
- 查看日志中的错误信息

#### 2. 识别准确率低
- 调整静音检测秒数
- 检查麦克风质量
- 确保环境噪音较低

#### 3. 响应速度慢
- 减少静音检测秒数
- 检查网络延迟
- 确认 API 服务状态

### 日志查看
```bash
# 查看 MIMO ASR 相关日志
grep -i "mimo_asr" /config/home-assistant.log

# 实时监控日志
tail -f /config/home-assistant.log | grep -i "mimo_asr"
```

## 📈 版本历史

### v1.0.1 (2026-09-07)
- ✨ 添加本地 VAD（语音活动检测）
- ✨ 使用 OpenAI 客户端库，提高稳定性
- ✨ 添加可配置参数（静音阈值、请求超时）
- ✨ 添加单实例限制
- ✨ 改进日志系统
- 🐛 修复音频格式兼容性问题

### v1.0.0 (2026-09-06)
- 🎉 初始版本
- ✨ 基础语音识别功能
- ✨ 支持中英文识别
- ✨ HACS 集成支持

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

### 开发环境
1. 克隆仓库
2. 安装依赖：`pip install openai>=1.0.0`
3. 在 Home Assistant 中测试

### 代码规范
- 遵循 PEP 8 规范
- 添加适当的注释和文档
- 确保类型注解完整

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- 感谢小米 MIMO 团队提供优秀的语音识别服务
- 感谢 Home Assistant 社区的支持
- 感谢 [ly2199/ha_mimo_asr](https://github.com/ly2199/ha_mimo_asr) 提供的参考实现

## 📞 支持

- **GitHub Issues**: [提交问题](https://github.com/ShylynnLee/hass-mimo-asr/issues)
- **文档**: [小米 MIMO ASR 文档](https://mimo.mi.com/docs/zh-CN/quick-start/usage-guide/audio/Speech-Recognition)
- **Home Assistant 社区**: [社区讨论](https://community.home-assistant.io/)
