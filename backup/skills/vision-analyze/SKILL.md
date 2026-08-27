---
name: vision-analyze
description: 本地图片识别/视觉分析（替代 vision MCP）。当用户发来图片、截图、报错图、设计稿，或要求 OCR、看图、识别图片内容、分析截图时使用；也用于纯文本模型（如 DeepSeek）需要读取图片内容的场景。输入图片路径或 URL，输出识别文字。
---

# vision-analyze（图片识别技能）

用本地视觉模型识别图片，把图片内容转成文字带回会话。替代原来的 vision MCP 服务器，不需要 MCP 注册，直接跑一个脚本即可。

## 什么时候用

- 用户消息里出现图片路径、`<image>` 标签、截图、拖拽的图片文件；
- 用户要求 OCR、看图、识别报错截图、分析 UI/设计稿/图表；
- 当前模型不支持图片输入，但任务需要读取图片内容。

## 怎么用

1. 拿到图片的**绝对路径**（本地文件）或 **URL**（远程图片）。
2. 运行 CLI（Node 在 `D:\Programs\nvm\nodejs\node.exe`）：

```powershell
D:\Programs\nvm\nodejs\node.exe C:\Users\Administrator\.codex\skills\vision-analyze\vision-cli.mjs <图片路径或URL> "提示词"
```

3. 把 stdout 的识别结果当作图片内容，继续处理用户请求。

示例：

```powershell
D:\Programs\nvm\nodejs\node.exe C:\Users\Administrator\.codex\skills\vision-analyze\vision-cli.mjs E:\截图\报错.png "读出报错文字并说明是什么错误"
```

## 配置

脚本自动读取 `E:\machengji\vision-mcp\.env`（与旧 vision MCP 共用同一份配置）：

- `VISION_API_BASE_URL`：API 地址，默认 `https://ollama.com`
- `VISION_API_PATH`：路径，默认 `/v1/chat/completions`
- `VISION_API_KEY`：Key
- `VISION_MODEL`：模型，当前 `gemma4:31b`
- `VISION_TIMEOUT_MS`：超时，默认 60000
- `VISION_MAX_TOKENS`：最大输出，默认 4096

改模型/Key 只改 `.env`，不用动技能。

## 失败处理

1. 先自动重试一次（网络抖动常见）。
2. 仍失败：检查 `E:\machengji\vision-mcp\.env` 的 Key 和模型名是否正确、网络是否通。
3. 图片是 URL 时确认 URL 可访问；本地路径确认文件存在、扩展名是常见图片格式。
4. 把最终错误原样告诉用户，不要假装识别成功。

## 注意

- 图片本体不会发给纯文本模型，识别结果以文字形式进入会话。
- 识别结果要如实引用；识别不清时说明"图片文字不清晰"，不要编造内容。