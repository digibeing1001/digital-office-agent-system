# 外部工具资源

本目录存放外部技能和参考资料的本地副本。

## 目录结构

```
tools/
└── downloaded/          # 已下载的外部技能（需手动安装）
    └── humanize-chinese-writing/  # 去 AI 味核心方法论
```

## 安装步骤

### humanize-chinese-writing（P0，去 AI 味核心方法论）

此技能是中文去 AI 味的核心参考，被撰稿人（04-writer）和审查员（05-reviewer）引用。

```bash
# 在 tools/downloaded/ 目录下执行：
cd tools/downloaded
git clone https://github.com/Lanqingsong/humanize-chinese-writing.git
```

安装后应包含以下关键文件：
- `README.md` — 回答者惯性理论 + 落笔前四步 + 五层检查
- `references/patterns.md` — 中文 AI 味 6 大类模式
- `scripts/audit_chinese_ai_style.py` — 机械审计脚本（可选）

**未安装时的降级行为**：撰稿人和审查员仍可基于 `style-library/kenny-writer.md` 中的禁用清单 + 四层自检执行去 AI 味检查，但缺少 humanize-chinese-writing 的作者站位四步和五层检查方法论。

### 其他外部技能

完整外部技能索引见 [workflow/external-skills.md](../workflow/external-skills.md)。大部分外部技能通过 API 或 MCP 接入，不需要下载到本地。
