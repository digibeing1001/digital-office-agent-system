# Local Models And Deployment

This repository does not store model weights or Python dependency folders.

At deployment time, install local capabilities on the enterprise host:

```bash
agent-system/bin/install-local-models base-ocr-python
agent-system/bin/install-local-models base-rag-zh
```

Optional packs:

```bash
agent-system/bin/install-local-models base-rag-en
agent-system/bin/install-local-models enhanced-rag-multilingual
agent-system/bin/install-local-models enhanced-ocr
```

Default local capabilities:

- OCR: RapidOCR ONNX Runtime, with optional Tesseract fallback.
- PDF text: `pypdf`, with optional `pdftotext` fallback.
- Word text: `python-docx`, with builtin ZIP/XML fallback.
- RAG embeddings: `BAAI/bge-small-zh-v1.5` by default.
- Multilingual RAG upgrade: `BAAI/bge-m3`.

The GUI should show `office-system health` so admins can see which local
capabilities are installed.
