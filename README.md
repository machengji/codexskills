# Codex GitHub Daily Sync

每天把本机 Codex 的自定义 skills 和安全处理后的配置提交并推送到你的 GitHub 仓库。

## 备份内容

- `skills/`：只备份自定义 skills，自动跳过 Codex 随版本安装的 `.system`。
- `config.toml`：会删除 `token`、`secret`、`api_key`、`password` 等配置值。
- `AGENTS.md`、`hooks/`、`rules/`、`prompts/`。

不会备份登录信息、会话、日志、缓存、记忆、插件缓存、`.env` 文件或私钥文件。技能/钩子中的常见 GitHub、OpenAI、AWS 令牌格式也会被替换为 `__REDACTED_SECRET__`。仍建议将 GitHub 仓库设为 Private，并在首次推送前检查 `backup/` 目录。

## 首次设置

1. 在 GitHub 新建一个空的 **Private** 仓库，不要初始化 README、`.gitignore` 或 License。
2. 打开 PowerShell，进入此目录后运行（把 URL 换成你的仓库地址）：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\Setup-CodexGitHubSync.ps1 -RepositoryUrl "https://github.com/你的用户名/codex-backup.git" -Time "20:00"
```

首次运行会复制安全范围内的文件、初始化 Git、推送到 GitHub，并创建名为 `Codex Daily GitHub Sync` 的 Windows 计划任务。时间采用 24 小时制。

Git 通过你现有的 Git Credential Manager 登录或 SSH 密钥认证；脚本不会保存 GitHub Token。计划任务以当前 Windows 用户的交互式身份运行，因此电脑需要开机且该用户已登录。

## 手动同步与验证

```powershell
.\Sync-CodexBackup.ps1
Get-ScheduledTask -TaskName "Codex Daily GitHub Sync"
```

首次推送遇到 GitHub 身份验证时，按 Git 弹出的浏览器登录即可。之后计划任务可复用凭据。

## 停用定时同步

```powershell
.\Remove-CodexGitHubSyncTask.ps1
```

这只删除计划任务，不会删除本地备份或 GitHub 仓库。

## 自检

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\tests\Test-Sync.ps1
```
