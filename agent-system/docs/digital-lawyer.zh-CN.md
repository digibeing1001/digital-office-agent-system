# 数字律师设计说明

数字办公室中的 `legal` 是一个产品可见的数字员工：数字律师。它不是“法务部门”，也不再向用户暴露 `legal-contracts`、`legal-compliance` 这类子 Agent。合同审查、隐私数据、产品合规、用工/IP、争议分流都作为数字律师内部的 workflow lane 和 skill lane 运行。

## 设计原则

- 对外角色统一为数字员工，不混用“部门”和“员工”两套心智模型。
- 数字律师是一个企业内部法务数字员工，不是律师事务所或外部律师团队。
- 运行时以 workflow、skill、context envelope、artifact 和 human gate 为主，不模拟多层人类组织。
- 所有法律输出都是内部审查草稿，不是正式法律意见或法律结论。
- 对外发送、签署、上线、解雇、诉讼、监管提交等动作必须经过人工专业审查。

## 结构

```text
秘书 Agent
  -> 数字律师 legal
      -> legal_triage workflow
      -> legal_contract_review workflow
      -> legal_privacy_data_review workflow
      -> legal_product_compliance_review workflow
      -> legal_employment_ip_review workflow
      -> legal_dispute_triage workflow
      -> digital-lawyer-workflows skill pack
```

`legal` 是唯一的法务类数字员工。合同审查和合规审查不是独立数字员工，而是数字律师内部的可验证 skill lane。

## 常用工作流

- `legal_triage`：用户只说“找法务/找数字律师”或任务边界不清时使用。
- `legal_contract_review`：供应商合同、客户合同、SaaS、NDA、采购、服务协议、合同争议。
- `legal_privacy_data_review`：个人信息、数据处理、DPA、PIA、主体权利响应。
- `legal_product_compliance_review`：产品上线、营销宣传、AI 治理、监管变化、合规就绪。
- `legal_employment_ip_review`：劳动用工、解除、录用、知识产权、开源合规。
- `legal_dispute_triage`：律师函、争议、诉讼/仲裁前分流、外部律师协作。

## 外部技能库接入策略

`claude-for-legal-zh` 以 Apache 2.0 许可发布，已本地安装到 `skills/_imported/claude-for-legal-ZH`，并通过 `digital-lawyer-workflows` 受控使用。它按商事合同、公司法务、隐私数据、产品法务、劳动用工、AI 治理、知识产权、监管合规、争议解决等领域组织，适合作为数字律师 workflow 的来源。

`Legal-Skills-Chinese` 提供中国法推理原子技能，但其 README/CONTRIBUTING 标注为 CC BY-NC-ND 4.0。当前只能登记为参考源，不能直接内置、改作、再分发或商用，除非后续完成授权确认。

## 交付标准

数字律师最终交付必须包含：

1. 业务可读摘要
2. 来源与核验状态
3. 风险等级和影响
4. 建议动作和替代方案
5. 禁止动作或需暂停动作
6. 人工审查/审批门槛
