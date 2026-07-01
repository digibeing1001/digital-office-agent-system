# failure-mode-archiving — 失败模式即时归档(负面结果价值捕获)

## 用途

在实验或假设**不通过的当下**即时归档"什么条件下不工作",把科研中的负面结果转化为可复用的方法边界知识。科研里失败本身有价值:排除一个错误假设、划定一个方法的失效边界、记录一组不 work 的超参组合,都是科研产出。如果等项目结束才笼统抽一句"不要 Y",失败细节早就丢了。

本技能与 `experience-extraction`(项目级 anti-pattern 总结)互补:
- `experience-extraction`:项目结束时统一抽取行为教训("遇到 X,不要 Y"),粒度粗、时机晚。
- `failure-mode-archiving`(本技能):失败发生时即时归档方法边界("在条件 C 下,方法 M 不工作"),粒度细、时机即时。

一次失败既会在发生时由本技能归档为失败模式,也可能在项目结束时被 experience-extraction 抽取为 anti-pattern,两者不冲突。

## 触发条件

满足以下任一条件即激活本技能(由 PI/工程师/数据分析师主动调用,不等项目结束):

- **假设被证伪**:实验结果落在 PI 标注的"推翻该假设"区间
- **实验不通过**:baseline 复现失败、新方法跑不出预期指标、ablation 与假设方向相反
- **方法失效**:方法在某条件(长上下文/小样本/特定分布/特定硬件)下不 work 或性能崩塌
- **超参组合失败**:某组超参训练发散、OOM、收敛但指标显著低于预期
- **复现失败**:无法复现原论文数字,已排查环境/版本/数据后确认系统性偏差
- **PI 主动评估后判定假设不成立**(此时归档 + 触发方向性决策 H5)

不触发本技能的情况:笔误、环境配置错误、一次性 bug(这些记入实验日志即可,不属于方法级失败模式)。

## 工具依赖

无额外依赖,用 LLM 辅助抽取失败模式字段,失败模式库存储为 Markdown 文件:

```bash
pip install openai  # 调用 LLM 辅助抽取字段(也可用本地模型,或人工填写)
```

## 操作步骤

1. **确认这是方法级失败而非偶发事故** — 笔误/环境错/一次性 bug 不归档,记实验日志即可。只有"方法/假设/超参组合在某个条件下不 work"才归档。
2. **收集失败现场** — 假设/方法描述、预期结果、实际结果、实验配置、数据版本、环境、异常日志。从实验日志和工程师交接取回,不重新跑实验。
3. **抽取失败模式字段**(LLM 辅助或人工填写):
   - `hypothesis_or_method`:假设/方法是什么(原预期)
   - `expected_result`:预期结果(量化)
   - `actual_result`:实际结果(量化,附实验日志引用)
   - `failure_condition`:失效条件(什么条件下不工作,尽量具体可复现)
   - `possible_cause`:可能原因(标注"推测",不冒充定论;有证据的写证据)
   - `method_boundary`:方法边界(此方法在 X 范围内不适用)
   - `systemic_flag`:偶发失败 / 系统性失败(多次重复是否稳定复现)
   - `source_project_id`:来源项目 id
4. **去重**(与现有失败模式库比对):相同方法 + 相同失效条件视为重复,合并而非新增(补充新证据到已有记录)。
5. **写入** `skills/experience/<agent_id>/failure-modes/<topic>.md`,每条记录附来源项目 id 和归档时间。
6. **通知 PI 评估**:归档后通知 PI,PI 判断是否需要调整假设/路线。若 PI 决定调整方向,触发人类介入决策 H5(方向性决策)。
7. **(可选)建议更新评分卡**:若某方法连续多次失败模式归档,建议秘书复核 `scoring_config.yaml` 中对应维度的可行性权重。

## 调用示例

```python
import os, json, datetime

ARCHIVE_PROMPT = """从下面的失败现场中抽取失败模式记录。必须如实记录,可能原因标注"推测",不冒充定论。
字段:
- hypothesis_or_method: 假设/方法是什么(原预期)
- expected_result: 预期结果(量化)
- actual_result: 实际结果(量化)
- failure_condition: 失效条件(什么条件下不工作,具体可复现)
- possible_cause: 可能原因(标注"推测";有证据的写证据)
- method_boundary: 方法边界(此方法在 X 范围内不适用)
- systemic_flag: systemic(系统性) / sporadic(偶发)
- source_project_id: 来源项目 id

失败现场:
{evidence}

输出 JSON:
{{"hypothesis_or_method": "...", "expected_result": "...", "actual_result": "...",
  "failure_condition": "...", "possible_cause": "...", "method_boundary": "...",
  "systemic_flag": "systemic|sporadic", "source_project_id": "..."}}
"""

def archive_failure(agent_id, topic, evidence, project_id):
    # 1. LLM 抽取字段
    raw = llm_call(ARCHIVE_PROMPT.format(evidence=json.dumps(evidence, ensure_ascii=False)))
    record = json.loads(raw)
    record["source_project_id"] = project_id
    record["archived_at"] = datetime.date.today().isoformat()

    # 2. 去重(相同方法 + 相同失效条件合并)
    path = f"skills/experience/{agent_id}/failure-modes/{topic}.md"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    if is_duplicate_failure(record, path):
        merge_into_existing(record, path)  # 补充新证据到已有记录
    else:
        write_new_record(record, path)

    # 3. 通知 PI 评估是否调整方向
    notify_pi(agent_id, record, project_id)
    return {"archived": True, "topic": topic, "systemic": record["systemic_flag"]}

def is_duplicate_failure(record, path):
    if not os.path.isfile(path):
        return False
    with open(path, encoding="utf-8") as f:
        content = f.read()
    # 简化判断:相同 hypothesis_or_method 且相同 failure_condition 视为重复
    # 实际用语义相似度 > 0.85
    return record["hypothesis_or_method"][:30] in content and \
           record["failure_condition"][:30] in content

def write_new_record(record, path):
    entry = f"""## 失败模式 — {record['topic'] if 'topic' in record else '未命名'}

- **假设/方法**: {record['hypothesis_or_method']}
- **预期结果**: {record['expected_result']}
- **实际结果**: {record['actual_result']}
- **失效条件**: {record['failure_condition']}
- **可能原因**(推测): {record['possible_cause']}
- **方法边界**: {record['method_boundary']}
- **失败性质**: {record['systemic_flag']}
- **来源项目**: {record['source_project_id']}
- **归档时间**: {record['archived_at']}

"""
    with open(path, "a", encoding="utf-8") as f:
        f.write(entry)
```

## 输出格式

失败模式记录文件(`skills/experience/<agent_id>/failure-modes/<topic>.md`):

```markdown
## 失败模式 — 长上下文召回

- **假设/方法**: 方法 M 在长上下文场景下召回率优于 baseline B
- **预期结果**: 在 32k 上下文 benchmark 上召回率 ≥ 85%
- **实际结果**: 32k 时召回率掉到 62%,16k 时 84%(正常)
- **失效条件**: 上下文长度 > 16k 时方法 M 的召回率断崖式下降
- **可能原因**(推测): 注意力稀释,推测与位置编码外推有关;待验证
- **方法边界**: 方法 M 适用于上下文 ≤ 16k,长上下文场景需换方案
- **失败性质**: systemic(多次重复稳定复现)
- **来源项目**: proj_2026_07_memframework
- **归档时间**: 2026-07-01
```

归档确认回执:

```json
{
  "archived": true,
  "agent_id": "office-research-engineer",
  "topic": "long-context-recall",
  "systemic": "systemic",
  "pi_notified": true,
  "path": "skills/experience/office-research-engineer/failure-modes/long-context-recall.md"
}
```

## 检索(新实验设计前)

新实验设计前,方法学专家/工程师按方法名和条件检索相关失败模式,避免重蹈覆辙:

```python
def retrieve_failure_modes(agent_id, method_keyword, condition_keyword=None, top_k=5):
    """检索相关失败模式,注入实验设计的 prompt"""
    path = f"skills/experience/{agent_id}/failure-modes/"
    # 实际用向量检索;这里简化为关键词匹配
    hits = []
    for fn in os.listdir(path):
        with open(os.path.join(path, fn), encoding="utf-8") as f:
            content = f.read()
            if method_keyword in content:
                hits.append({"file": fn, "snippet": extract_relevant(content, method_keyword)})
    return hits[:top_k]
```

## 约束

- **如实记录**:失效条件和实际结果必须量化、可复现,不写成"效果不好""性能差"。
- **可能原因必须标注"推测"**:不冒充定论,有证据的写证据,没证据的标"待验证"。
- **不写成自我开脱**:不能写成"运气不好""数据不行",必须是方法/条件层面的归因。
- **去重**:相同方法 + 相同失效条件合并,不重复堆砌。
- **附来源项目 id**:每条记录可追溯,便于后续复核。
- **失败模式会过时**:方法迭代后旧失效条件可能不再成立,需定期复核(衰减机制同经验库,长期未复现的失败模式降权但不删除)。
- **不阻断流程(除非 PI 调整方向)**:归档本身不停项目;只有 PI 据此决定换方向时才触发 H5 暂停。
- **偶发 vs 系统性必须区分**:偶发失败标注 sporadic,系统性失败标注 systemic;只有 systemic 的才强烈建议后续追踪。

## 关键方法论引用

- 负结果价值:"Negative Results Are Positive"(Resch & Schamp 2024)— 负面结果是科学知识的一部分
- 失败学:科研失败经验建模(Failure Sense)— 把失败结构化沉淀
- ExpeL(Zhao et al. AAAI 2024, arXiv:2308.10144):去重和衰减机制参考
- 可复现性:ML Reproducibility Checklist(Pineau et al., 2021)— 失效条件记录的可复现标准
