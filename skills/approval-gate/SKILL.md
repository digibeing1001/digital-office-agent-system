# approval-gate — 审批门

## 用途
硬管控动作阻断。识别即将执行的动作类型,命中 11 类硬管控清单时无条件阻断,路由到人工或专业复核,记录审批结果。确保高风险动作不未经审批执行。

## 触发条件
- 任何角色即将执行可能产生不可逆影响的动作时。
- 系统检测到高风险动作时。
- 用户提到"审批""管控""阻断""hard gate"时。

## 工具依赖
无额外依赖。

## 操作步骤
1. 识别即将执行的动作类型。
2. 与 11 类硬管控清单匹配。
3. 命中则无条件阻断,不执行。
4. 路由:通知人工审批 / 转专业角色复核。
5. 记录审批结果(通过/拒绝/待定)。
6. 只有审批通过后才放行。

## 调用示例

`hard_controls.yaml`(11 类硬管控):
```yaml
hard_controls:
  - id: HC01
    name: "提交代码到 main 分支"
    pattern: "git push.*main|git commit.*main"
    action: "block"
    route_to: "human_approval"
  - id: HC02
    name: "发布/部署到生产环境"
    pattern: "deploy|publish.*production|release"
    action: "block"
    route_to: "human_approval"
  - id: HC03
    name: "删除大量文件/数据"
    pattern: "delete.*batch|rm.*-rf|drop.*table"
    action: "block"
    route_to: "human_approval"
  - id: HC04
    name: "发送对外邮件/消息"
    pattern: "send.*email|publish.*external"
    action: "block"
    route_to: "human_approval"
  - id: HC05
    name: "修改共享配置/权限"
    pattern: "chmod|chown|modify.*config.*shared"
    action: "block"
    route_to: "human_approval"
  - id: HC06
    name: "产生费用/采购"
    pattern: "purchase|pay|spend|order"
    action: "block"
    route_to: "human_approval"
  - id: HC07
    name: "对外发布论文/声明"
    pattern: "submit.*paper|publish.*paper|press.*release"
    action: "block"
    route_to: "qa_inspector"
  - id: HC08
    name: "分享敏感数据/密钥"
    pattern: "share.*key|share.*credential|export.*data"
    action: "block"
    route_to: "human_approval"
  - id: HC09
    name: "格式化/重置环境"
    pattern: "format|reset.*env|wipe"
    action: "block"
    route_to: "human_approval"
  - id: HC10
    name: "安装/卸载系统级软件"
    pattern: "apt.*install|brew.*install|pip.*install.*--system"
    action: "block"
    route_to: "human_approval"
  - id: HC11
    name: "修改 git history(force push/reset)"
    pattern: "git.*--force|git.*reset.--hard"
    action: "block"
    route_to: "human_approval"
```

```python
import yaml
import re

def load_controls(path="hard_controls.yaml"):
    with open(path) as f:
        return yaml.safe_load(f)["hard_controls"]

def check_gate(action_desc, controls):
    """检查动作是否命中硬管控"""
    for hc in controls:
        if re.search(hc["pattern"], action_desc, re.IGNORECASE):
            return {
                "blocked": True,
                "control_id": hc["id"],
                "control_name": hc["name"],
                "route_to": hc["route_to"],
                "message": f"⚠️ 命中硬管控 {hc['id']}: {hc['name']},已阻断,路由至 {hc['route_to']}",
            }
    return {"blocked": False, "message": "未命中硬管控,放行"}

def execute_with_gate(action_desc, action_fn, controls):
    """带审批门的执行"""
    gate = check_gate(action_desc, controls)
    if gate["blocked"]:
        print(gate["message"])
        # 记录到审批日志
        log = {
            "action": action_desc,
            "control_id": gate["control_id"],
            "status": "blocked_pending_approval",
            "route_to": gate["route_to"],
        }
        print(f"审批日志: {log}")
        return None  # 不执行
    # 未命中,执行
    return action_fn()

# 执行
controls = load_controls()

# 测试:命中硬管控的动作
result = execute_with_gate("git push origin main", None, controls)
# 输出: ⚠️ 命中硬管控 HC01...

# 测试:未命中的动作
result = execute_with_gate("git status", lambda: print("执行成功"), controls)
# 输出: 执行成功
```

## 输出格式
- 审批日志:动作描述、命中的管控 ID、状态(blocked/approved)、路由目标。
- 阻断时不执行动作,返回 None。

## 约束
- 硬管控无条件阻断,不因任何理由跳过。
- 阻断后必须人工审批或专业复核通过才放行,不可自动放行。
- 审批日志永久保留,不可删除。
- 11 类清单可根据需要扩展,但不可缩减现有管控项。
