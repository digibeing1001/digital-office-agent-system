import type { AgentSummary } from '../types'

export const agentNames: Record<string, string> = {
  secretary: '秘书',
  pm: '产品经理',
  researcher: '研究员',
  planner: '规划师',
  'vibe-designer': '设计师',
  coder: '程序员',
  writer: '写作助手',
  legal: '企业法务',
}

export const agentRoles: Record<string, string> = {
  secretary: '接收任务、安排工作、跟进进度',
  pm: '梳理需求、确定优先级和验收标准',
  researcher: '查找资料、核对事实和来源',
  planner: '制定方案、拆解步骤和管理依赖',
  'vibe-designer': '界面、体验、原型和设计审查',
  coder: '开发、调试、测试和发布',
  writer: '写作、编辑和内容交付',
  legal: '合同、合规、隐私和企业法律事务',
}

export const stageLabels: Record<string, string> = {
  context: '了解情况',
  decide: '制定方案',
  act: '开始办理',
  evaluate: '检查交付',
}

export const statusLabels: Record<string, string> = {
  active: '可工作',
  inactive: '已停用',
  archived: '已归档',
  created: '已创建',
  queued: '等待中',
  context_loading: '了解情况',
  deciding: '制定方案',
  acting: '办理中',
  evaluating: '检查中',
  waiting_human: '等待确认',
  waiting_human_judgment: '等待判断',
  waiting_approval: '等待审批',
  blocked: '需要补充',
  completed: '已完成',
  failed: '未完成',
  cancelled: '已取消',
  stopped: '已停止',
  pending: '待审批',
  approved: '已批准',
  rejected: '已拒绝',
}

export function displayAgentName(agent: AgentSummary | undefined): string {
  if (!agent) return '数字员工'
  return agentNames[agent.agent_id] || agent.display_name_zh || agent.display_name || agent.agent_id
}

export function displayAgentRole(agent: AgentSummary): string {
  return agentRoles[agent.agent_id] || agent.user_visible_role || agent.portable_role || '专业数字员工'
}

export function formatTime(value?: string): string {
  if (!value) return '刚刚'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return value
  return new Intl.DateTimeFormat('zh-CN', { month: 'numeric', day: 'numeric', hour: '2-digit', minute: '2-digit' }).format(date)
}

export function initials(name: string): string {
  const clean = name.replace(/Digital Office/gi, '').trim()
  return clean.slice(0, 2).toUpperCase() || 'DO'
}
