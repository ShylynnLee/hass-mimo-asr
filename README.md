# 小米 MIMO ASR - Home Assistant 语音识别插件

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

这是一个 Home Assistant 自定义集成，用于接入小米 MIMO ASR 语音识别服务。

## 功能特性

- 支持中文、英文及自动语种检测
- 支持 WAV 和 MP3 音频格式
- 支持方言识别（粤语、四川话等）
- 基于 OpenAI 兼容 API，稳定可靠
- 支持 HACS 安装和更新

## 安装方法

### 通过 HACS 安装（推荐）

1. 在 HACS 中添加自定义存储库：
   - 存储库：`https://github.com/ShylynnLee/hass-mimo-asr`
   - 类别：集成
2. 搜索 "MIMO ASR" 并安装
3. 重启 Home Assistant

### 手动安装

1. 下载最新版本
2. 将 `custom_components/mimo_asr` 文件夹复制到您的 Home Assistant 配置目录
3. 重启 Home Assistant

## 配置说明

在 `configuration.yaml` 中添加：

```yaml
# 示例配置
mimo_asr:
  api_key: "your_api_key_here"
  language: "zh"  # 可选：auto/zh/en
```

或者通过 UI 配置：
1. 进入 设置 → 设备与服务 → 集成
2. 点击 + 添加集成
3. 搜索 "MIMO ASR"
4. 输入您的 API Key 和其他配置

## 使用方法

### 服务调用

```yaml
service: stt.mimo_asr
data:
  audio_file: "/config/audio/recording.wav"
  language: "zh"
response_variable: transcription
```

### 自动化示例

```yaml
automation:
  - alias: "语音转写新音频"
    trigger:
      platform: event
      event_type: folder_watcher
      event_data:
        event_type: created
        folder: "/config/audio/"
    action:
      - service: stt.mimo_asr
        data:
          audio_file: "{{ trigger.event.data.path }}"
          language: "zh"
        response_variable: stt_result
      - service: notify.mobile_app
        data:
          message: "语音转写结果: {{ stt_result.text }}"
```

## API 密钥获取

1. 访问 [小米 MIMO 开发者平台](https://api.xiaomimimo.com)
2. 注册并登录
3. 创建应用，获取 API Key
4. 确保账户有足够的调用额度

## 注意事项

- 音频文件大小限制：Base64 编码后 ≤ 10MB
- 建议音频格式：16kHz 采样率、单声道、16bit
- API 调用可能产生费用，请查看小米 MIMO 定价策略
- 音频数据会上传到小米服务器，请注意隐私合规

## 故障排除

### 常见问题

1. **API 认证失败**
   - 检查 API Key 是否正确
   - 确认 API Key 是否有效

2. **音频格式不支持**
   - 确保音频为 WAV 或 MP3 格式
   - 检查音频文件是否损坏

3. **识别准确率低**
   - 尝试指定正确的语言参数
   - 确保音频质量清晰

## 开发计划

- [ ] 支持实时流式识别
- [ ] 添加识别结果缓存
- [ ] 支持更多音频格式
- [ ] 添加 Web UI 配置面板

## 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 致谢

- 感谢小米 MIMO 团队提供优秀的语音识别服务
- 感谢 Home Assistant 社区的支持
