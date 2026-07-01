# socratic-elicitation — Socratic 引导立项

## 用途
基于 academic-research-skills 的 Socratic 引导模式，通过结构化提问引导用户澄清研究意图、明确约束条件、识别隐含假设。在课题立项前通过对话式引导，确保研究方向明确、可行、有价值。避免"用户说一句就开干"的仓促立项。

适用于:课题立项前的需求澄清、研究方向的意图探测、模糊需求的精确化、隐含假设的识别与挑战。

## 触发条件
- 科研秘书启动立项流程
- 课题规划师需要明确研究方向
- 用户提出的研究需求模糊或宽泛
- intent_confirmed 为 false（Loop context 节点未确认意图）
- 用户要求"帮我理清研究方向""立项前的讨论"

## 操作步骤

### 步骤 1:意图探测
```python
def detect_intent(user_input: str) -> dict:
    """探测用户研究意图的清晰度"""
    analysis = llm_call(f"""
    分析以下用户输入的研究意图清晰度:
    "{user_input}"
    
    评估维度:
    1. 问题清晰度 (1-5): 研究问题是否明确
    2. 范围明确性 (1-5): 研究范围是否边界清晰
    3. 约束识别 (1-5): 是否提到约束（时间/资源/方法）
    4. 价值主张 (1-5): 研究价值是否阐述
    5. 隐含假设 (list): 用户可能未明说的假设
    
    输出 JSON。
    """)
    return json.loads(analysis)
```

### 步骤 2:生成 Socratic 问题
```python
def generate_socratic_questions(intent_analysis: dict, user_input: str) -> list:
    """基于意图分析生成针对性 Socratic 问题"""
    questions = []
    
    # 问题清晰度低
    if intent_analysis["问题清晰度"] <= 3:
        questions.append({
            "dimension": "clarity",
            "question": "你希望解决的核心问题是什么？能用一句话描述吗？",
            "purpose": "明确核心问题",
        })
    
    # 范围不明确
    if intent_analysis["范围明确性"] <= 3:
        questions.append({
            "dimension": "scope",
            "question": "这个研究涵盖哪些范围？哪些明确不包含？",
            "purpose": "界定研究边界",
        })
    
    # 约束未识别
    if intent_analysis["约束识别"] <= 3:
        questions.append({
            "dimension": "constraints",
            "question": "有哪些约束条件？（时间、数据、计算资源、方法限制）",
            "purpose": "识别约束",
        })
    
    # 价值未阐述
    if intent_analysis["价值主张"] <= 3:
        questions.append({
            "dimension": "value",
            "question": "这个研究为什么重要？谁会受益？解决了什么痛点？",
            "purpose": "明确价值",
        })
    
    # 挑战隐含假设
    for assumption in intent_analysis.get("隐含假设", []):
        questions.append({
            "dimension": "assumption",
            "question": f"你假设了'{assumption}'，这个假设成立吗？有没有反例？",
            "purpose": "挑战假设",
        })
    
    return questions
```

### 步骤 3:对话式引导
```python
def socratic_dialogue(user_input: str, max_rounds: int = 5) -> dict:
    """多轮 Socratic 对话引导"""
    dialogue_history = []
    current_input = user_input
    
    for round_num in range(max_rounds):
        # 分析当前意图
        analysis = detect_intent(current_input)
        
        # 所有维度都清晰 → 结束
        if all(analysis[d] >= 4 for d in ["问题清晰度", "范围明确性", "约束识别", "价值主张"]):
            dialogue_history.append({"round": round_num, "type": "converged", "analysis": analysis})
            break
        
        # 生成问题
        questions = generate_socratic_questions(analysis, current_input)
        dialogue_history.append({"round": round_num, "type": "questions", "questions": questions, "analysis": analysis})
        
        # 模拟用户回答（实际由用户提供）
        # 在实际使用中，这里等待用户输入
        current_input = wait_for_user_response(questions)
    
    return {
        "rounds": len(dialogue_history),
        "history": dialogue_history,
        "converged": dialogue_history[-1]["type"] == "converged",
    }
```

### 步骤 4:生成立项摘要
```python
def generate_project_brief(dialogue: dict) -> dict:
    """基于 Socratic 对话生成立项摘要"""
    final_analysis = dialogue["history"][-1]["analysis"]
    
    brief = {
        "research_question": final_analysis.get("明确的研究问题", ""),
        "scope": {
            "includes": final_analysis.get("包含范围", []),
            "excludes": final_analysis.get("排除范围", []),
        },
        "constraints": {
            "time": final_analysis.get("时间约束", ""),
            "data": final_analysis.get("数据约束", ""),
            "resources": final_analysis.get("资源约束", ""),
            "methods": final_analysis.get("方法约束", []),
        },
        "value_proposition": final_analysis.get("价值主张", ""),
        "assumptions": final_analysis.get("已验证假设", []),
        "risk_assumptions": final_analysis.get("未验证假设", []),
        "dialogue_rounds": dialogue["rounds"],
        "intent_confirmed": dialogue["converged"],
    }
    return brief
```

### 步骤 5:可行性预评估
```python
def feasibility_pre_check(brief: dict) -> dict:
    """立项摘要的可行性预评估"""
    return {
        "feasibility_score": _score_feasibility(brief),  # 1-7
        "novelty_indicator": _assess_novelty(brief),
        "resource_match": _check_resources(brief),
        "risks": _identify_risks(brief),
        "recommendation": "proceed" if _score_feasibility(brief) >= 4 else "refine",
    }
```

## 输出格式
立项摘要（写入 `outputs/proposals/<project>-brief.md`）:
- **研究问题**:一句话明确描述
- **范围**:包含 / 排除
- **约束**:时间 / 数据 / 资源 / 方法
- **价值主张**:为什么重要
- **假设**:已验证 / 未验证（风险假设）
- **可行性预评估**:可行性评分 + 新颖性 + 资源匹配 + 风险
- **对话记录**:Socratic 对话全过程

## 约束
- Socratic 问题必须开放式，不得引导性提问
- 每轮最多 5 个问题（防止用户疲劳）
- 最多 5 轮对话（防止无限循环）
- 未验证假设必须标记为风险，不得默认成立
- 立项摘要必须用户确认后才算 intent_confirmed = true
- 可行性预评估只是参考，不替代正式评审

## 与现有 skill 的关系
- **与 ai-native-loop.manifest.json 协同**:socratic-elicitation 是 context 节点意图确认的实现
- **与 hypothesis-building 协同**:socratic-elicitation 明确方向后，hypothesis-building 生成具体假设
- **与 goap-planner 协同**:socratic-elicitation 产出立项摘要后，goap-planner 规划执行路径
- **与 experiment-design 协同**:socratic-elicitation 确认约束后，experiment-design 设计实验

## 依赖工具/API
- LLM API（意图分析、问题生成、摘要生成）
- 无外部依赖

## 关键方法论引用
- academic-research-skills Socratic 引导模式: https://github.com/Imbad0202/academic-research-skills
- Socratic 方法: 通过提问引导思考而非直接给出答案
- PRISMA 系统综述的立题阶段
