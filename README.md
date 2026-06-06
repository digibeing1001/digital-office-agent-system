# Digital Office Agent System

Portable Digital Office layer for Hermes.

中文开发者文档: [README.zh-CN.md](README.zh-CN.md)

This package contains:

- `agent-system/`: registries, GUI-facing control plane, knowledge/rules/memory policies, local model installers, release policies
- `scripts/agent-router`: registry-driven router for existing Hermes Agents
- `profiles/`: sanitized Agent profile templates without credentials
- `skills/agent-team-staffing`: secretary staffing workflow guidance
- `SOUL.md`: default Digital Office secretary bootstrap

## Product Boundary

Enterprise users should see the Digital Office GUI, not raw Hermes CLI. Hermes is the backend runtime.

New production Agents are delivered as provider-designed Agent plugin packages. The customer-site secretary Agent clarifies requirements and submits them to the provider backend; it does not autonomously create production Agents or add/remove skills.

Existing Agents may be improved through SOUL/workflow overlays only. Customer production must not add, remove, install, replace, or recompose skills through the GUI.

## Install

From this repository root:

```bash
./install.sh ~/.hermes
```

The installer backs up an existing `SOUL.md` before installing the Digital Office bootstrap.

## Health Checks

```bash
~/.hermes/scripts/agent-router --health
~/.hermes/agent-system/bin/office-system health
~/.hermes/agent-system/bin/product-update status
```

Local OCR/RAG model weights are not stored in this repository. They are downloaded on deployment with:

```bash
~/.hermes/agent-system/bin/install-local-models --pack base-ocr-python
~/.hermes/agent-system/bin/install-local-models --pack base-rag-zh
```

## GUI Contract

See `agent-system/docs/gui-contract.md`.
