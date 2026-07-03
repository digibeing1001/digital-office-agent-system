# Digital Office Design System

## Product Direction

Digital Office should feel like entering a company that is already working. The user interface uses familiar SaaS labels and controls, while the main office view uses restrained spatial and material cues to make Agents feel approachable.

## Two Surfaces

- User app: `我的办公室`, `任务`, `数字员工`, `资料库`, `审批`, `交付物`, `工作记录`, `设置`.
- Admin app: `系统概览`, `Agent 管理`, `Skills`, `运行监控`, `权限与预算`, `审计`, `系统维护`.

The applications have separate entry points and permissions but share tokens and components.

## Visual System

- Direction: modern editorial enterprise office with functional skeuomorphism.
- Background: cool paper white `#f3f6f4`.
- Ink: green-black `#18231f`.
- Primary: office green `#1e6b55`.
- Action: cobalt `#2f5bd3`.
- Attention: approval red `#c44949`.
- Surfaces: true white, matte painted panels, paper and restrained glass.
- Radius: 4px controls, 6px panels, 8px dialogs. Do not use large bubbly cards.
- Typography: Source Han Sans SC compatible stack for UI; Source Han Serif SC compatible stack for editorial headings; IBM Plex Mono compatible stack for operational data.
- Motion: 120-280ms state transitions, file handoff movement, status lamps and drawers. Respect reduced motion.

## Interaction Rules

- The secretary remains the default task entry point.
- Skills are capabilities and tools, never subordinate people.
- User pages use plain language. Runtime identifiers and hashes belong in the admin app.
- Custom Agent deletion is archive-first. Permanent deletion preserves history and requires admin confirmation.
- Demo mode is explicitly labeled and never mixes sample content with real records silently.
