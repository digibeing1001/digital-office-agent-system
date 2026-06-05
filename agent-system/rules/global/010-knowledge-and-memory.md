# Knowledge And Memory Policy

## Two Knowledge Bases

- Company global knowledge base: `agent-system/knowledge/company/`
- Project knowledge base: `agent-system/projects/<project_id>/knowledge/`

Company knowledge is reusable across projects. Project knowledge is scoped to a
single project unless the user approves promotion.

## KeyMemory Role

KeyMemory stays useful, but it is not the raw knowledge base. Use it for:

- user preferences and durable operating memories
- semantic pointers to approved knowledge entries
- approved methodology summaries after user confirmation
- secrets through KeyMemory secret storage only

Do not use KeyMemory for raw PDF, Word, image, or unapproved project draft
storage.

## Agent Reading

When an Agent works inside a project, it should first request project context
through:

```bash
agent-system/bin/office-system context --project <project_id> --agent <agent>
```

The context output lists active company knowledge, project knowledge, rule
layers, and known conflicts.
