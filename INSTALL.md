# 安装指南

## 方法一：通过 HACS 安装（推荐）

1. 确保您已安装 [HACS](https://hacs.xyz/)
2. 在 HACS 中，点击右上角菜单 → "自定义存储库"
3. 输入存储库 URL：`https://github.com/yourusername/hass-mimo-asr`
4. 类别选择 "集成"
5. 点击 "添加"
6. 搜索 "MIMO ASR" 并安装
7. 重启 Home Assistant

## 方法二：手动安装

1. 下载最新版本
2. 将 `custom_components/mimo_asr` 文件夹复制到您的 Home Assistant 配置目录
3. 重启 Home Assistant

## 配置

### 通过 UI 配置（推荐）

1. 进入 设置 → 设备与服务 → 集成
2. 点击 "+ 添加集成"
3. 搜索 "MIMO ASR"
4. 输入您的 API Key 和其他配置
5. 点击 "提交"

### 通过配置文件

在 `configuration.yaml` 中添加：

```yaml
mimo_asr:
  api_key: "your_api_key_here"
  language: "zh"  # 可选：auto/zh/en
```

## 获取 API Key

1. 访问 [小米 MIMO 开发者平台](https://api.xiaomimimo.com)
2. 注册并登录
3. 创建应用，获取 API Key
4. 确保账户有足够的调用额度

## 测试安装

1. 准备一个测试音频文件（WAV 或 MP3 格式）
2. 在 Home Assistant 中调用服务：

```yaml
service: stt.mimo_asr
data:
  audio_file: "/config/audio/test.wav"
  language: "zh"
```

3. 检查日志中是否有错误信息

## 故障排除

1. **集成未显示**：确保文件路径正确，重启 Home Assistant
2. **API 认证失败**：检查 API Key 是否正确
3. **音频格式错误**：确保音频为 WAV 或 MP3 格式

## 更多帮助

查看 [README.md](README.md) 获取详细使用说明。
