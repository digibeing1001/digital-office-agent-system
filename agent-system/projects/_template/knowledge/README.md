# Project Knowledge Base

This folder stores project-specific source files, text entries, extracted text,
image captions, OCR output, and review state.

Agents may read this folder only through the project context contract:

```bash
agent-system/bin/office-system context --project <project_id> --agent <agent>
```

GUI uploads should create one entry folder per source item.
