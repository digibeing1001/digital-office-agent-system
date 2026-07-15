# Digital Office 中文说明

本项目的主 README 已改为完整中文产品说明，请直接阅读 [README.md](README.md)。

2026-07-11 更新：科研分支已同步 durable dispatch lease、checkout 隔离健康检查、逐 gate harness 进度和 Solo-first 协调验证；科研经验只有通过来源、数据、实验或人工确认后才能进入长期记忆。

最快安装：

```bash
curl -fsSL https://raw.githubusercontent.com/digibeing1001/digital-office-agent-system/main/update | bash
```

以后升级：

```bash
~/.hermes/update
```

启动图形界面：

```bash
~/.hermes/digital-office-gui
```

系统会优先使用 `127.0.0.1:8787`。如果该端口已被其他程序占用，会自动避让并打开实际可用的地址。

打开管理后台：

```bash
~/.hermes/digital-office-gui --admin
```

安装器会区分程序文件和运行数据。已有个人规则或现有 Hermes/OpenClaw 数据时，它会要求明确选择保留还是覆盖，不会静默替用户做决定。
