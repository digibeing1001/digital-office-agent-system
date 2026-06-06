#!/usr/bin/env python3
"""GUI-facing control plane for the portable digital-office agent system."""

from __future__ import annotations

import argparse
import hashlib
import math
import datetime as dt
import importlib.util
import json
import mimetypes
import os
import re
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
import uuid
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree


TEXT_EXTS = {".md", ".txt", ".json", ".csv"}
DOCX_EXTS = {".docx"}
PDF_EXTS = {".pdf"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}


def maybe_reexec_venv() -> None:
    if os.environ.get("OFFICE_SYSTEM_NO_VENV"):
        return
    script_root = Path(__file__).resolve().parent.parent
    venv_python = script_root / ".venv" / "bin" / "python"
    if not venv_python.exists():
        return
    if Path(sys.executable).resolve() == venv_python.resolve():
        return
    os.execv(str(venv_python), [str(venv_python), __file__, *sys.argv[1:]])


maybe_reexec_venv()


def system_root() -> Path:
    configured = os.environ.get("DIGITAL_OFFICE_SYSTEM_HOME")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parent.parent


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9\u4e00-\u9fff._-]+", "-", value)
    value = value.strip("-._")
    return value or uuid.uuid4().hex[:8]


SAFE_COMPONENT_RE = re.compile(r"^[A-Za-z0-9_\u4e00-\u9fff][A-Za-z0-9._\-\u4e00-\u9fff]{0,127}$")
SAFE_CLAIM_RE = re.compile(r"^[^\x00-\x1f\x7f]{1,256}$")


def safe_component(value: str, label: str) -> str:
    value = str(value or "").strip()
    if not SAFE_COMPONENT_RE.fullmatch(value) or "/" in value or "\\" in value or value in {".", ".."}:
        print(f"office-system: invalid {label}: {value!r}", file=sys.stderr)
        raise SystemExit(2)
    return value


def safe_claim(value: str | None, label: str, required: bool = True) -> str:
    value = str(value or "").strip()
    if not value and not required:
        return ""
    if not SAFE_CLAIM_RE.fullmatch(value):
        print(f"office-system: invalid {label}: {value!r}", file=sys.stderr)
        raise SystemExit(2)
    return value


def registered_agent(root: Path, value: str) -> str:
    agent = safe_component(value, "agent id")
    registry = read_json(root / "agents.registry.json")
    if agent not in registry.get("agents", {}):
        print(f"office-system: unknown agent id: {agent}", file=sys.stderr)
        raise SystemExit(2)
    return agent


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def append_log(root: Path, event: dict[str, Any]) -> None:
    event = {"time": now_iso(), **event}
    log = root / "logs" / "office-system.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")


def project_path(root: Path, project: str) -> Path:
    return root / "projects" / safe_component(project, "project id")


def ensure_project(root: Path, project: str) -> Path:
    path = project_path(root, project)
    if not (path / "project.json").exists():
        print(f"office-system: project not found: {project}", file=sys.stderr)
        raise SystemExit(2)
    return path


def copy_template_project(root: Path, project_id: str, name: str, agents: list[str], schedule: str) -> Path:
    template = root / "projects" / "_template"
    project_id = safe_component(project_id, "project id")
    target = project_path(root, project_id)
    if target.exists():
        print(f"office-system: project already exists: {project_id}", file=sys.stderr)
        raise SystemExit(2)
    shutil.copytree(template, target)
    data = read_json(target / "project.json")
    data.update(
        {
            "project_id": project_id,
            "name": name,
            "status": "active",
            "created_at": now_iso(),
        }
    )
    if agents:
        data["agent_roster"] = agents
    data.setdefault("methodology_promotion", {})["schedule"] = schedule
    write_json(target / "project.json", data)
    return target


def entry_root(root: Path, scope: str, project: str | None) -> Path:
    if scope == "company":
        return root / "knowledge" / "company" / "entries"
    if not project:
        print("office-system: --project is required for project knowledge", file=sys.stderr)
        raise SystemExit(2)
    return ensure_project(root, project) / "knowledge" / "entries"


def classify_file(path: Path) -> str:
    ext = path.suffix.lower()
    if ext in TEXT_EXTS:
        return "text"
    if ext in DOCX_EXTS:
        return "word"
    if ext in PDF_EXTS:
        return "pdf"
    if ext in IMAGE_EXTS:
        return "image"
    return "binary"


def extract_text_file(source: Path, target: Path) -> tuple[str, str]:
    try:
        text = source.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = source.read_text(encoding="utf-8", errors="replace")
    write_text(target, text)
    return "local_extracted", "python_stdlib"


def extract_docx(source: Path, target: Path) -> tuple[str, str]:
    try:
        import docx  # type: ignore

        document = docx.Document(str(source))
        text_parts = [paragraph.text for paragraph in document.paragraphs if paragraph.text]
        for table in document.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if cells:
                    text_parts.append(" | ".join(cells))
        write_text(target, "\n\n".join(text_parts).strip() + "\n")
        return "local_extracted", "python_docx"
    except Exception:
        pass

    paragraphs: list[str] = []
    try:
        with zipfile.ZipFile(source) as archive:
            xml = archive.read("word/document.xml")
        tree = ElementTree.fromstring(xml)
        namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
        for para in tree.iter(f"{namespace}p"):
            chunks = [node.text for node in para.iter(f"{namespace}t") if node.text]
            if chunks:
                paragraphs.append("".join(chunks))
    except Exception as exc:
        write_text(target.with_name("extraction-error.txt"), f"docx extraction failed: {exc}\n")
        return "pending_extraction", "python_stdlib_zip_xml"
    write_text(target, "\n\n".join(paragraphs).strip() + "\n")
    return "local_extracted", "python_stdlib_zip_xml"


def extract_pdf(source: Path, target: Path) -> tuple[str, str]:
    tool = shutil.which("pdftotext")
    if tool:
        proc = subprocess.run([tool, str(source), "-"], text=True, capture_output=True)
        if proc.returncode == 0:
            write_text(target, proc.stdout)
            return "local_extracted", "poppler_pdftotext"

    try:
        from pypdf import PdfReader  # type: ignore

        reader = PdfReader(str(source))
        pages = []
        for index, page in enumerate(reader.pages, start=1):
            pages.append(f"\n\n--- page {index} ---\n\n{page.extract_text() or ''}")
        write_text(target, "\n".join(pages).strip() + "\n")
        return "local_extracted", "pypdf"
    except Exception as exc:
        write_text(target.with_name("README.md"), f"PDF text extraction pending or failed: {exc}\n")
        return "pending_local_model_install", "poppler_pdftotext_or_pypdf"


def extract_image_rapidocr(source: Path, target: Path) -> tuple[str, str] | None:
    try:
        from rapidocr_onnxruntime import RapidOCR  # type: ignore
    except Exception:
        return None
    try:
        engine = RapidOCR()
        result, _ = engine(str(source))
        lines = []
        for item in result or []:
            text = item[1] if len(item) > 1 else ""
            score = item[2] if len(item) > 2 else ""
            if text:
                lines.append(f"{text}\t{score}")
        write_text(target, "\n".join(lines).strip() + "\n")
        return "local_extracted", "rapidocr_onnxruntime"
    except Exception as exc:
        write_text(target.with_name("rapidocr-error.txt"), f"rapidocr failed: {exc}\n")
        return None


def extract_image_ocr(source: Path, target: Path) -> tuple[str, str]:
    rapid = extract_image_rapidocr(source, target)
    if rapid:
        return rapid

    tool = shutil.which("tesseract")
    if not tool:
        write_text(
            target.with_name("README.md"),
            "Image OCR pending. Install base-ocr-python for RapidOCR or base-ocr for Tesseract OCR.\n",
        )
        return "pending_local_model_install", "rapidocr_or_tesseract"
    proc = subprocess.run([tool, str(source), "stdout", "-l", "eng+chi_sim"], text=True, capture_output=True)
    if proc.returncode != 0:
        write_text(target.with_name("ocr-error.txt"), proc.stderr or "tesseract failed\n")
        return "pending_extraction", "tesseract_cli"
    write_text(target, proc.stdout)
    return "local_extracted", "tesseract_cli"


def run_extraction(source: Path, extracted_dir: Path, kind: str) -> tuple[str, str]:
    extracted_dir.mkdir(parents=True, exist_ok=True)
    target = extracted_dir / "text.md"
    if kind == "text":
        return extract_text_file(source, target)
    if kind == "word" and source.suffix.lower() == ".docx":
        return extract_docx(source, target)
    if kind == "pdf":
        return extract_pdf(source, target)
    if kind == "image":
        return extract_image_ocr(source, extracted_dir / "ocr.txt")
    write_text(extracted_dir / "README.md", f"No local extractor registered for {source.suffix}.\n")
    return "pending_extraction", "none"


def add_file_entry(args: argparse.Namespace) -> int:
    root = system_root()
    source = Path(args.file).expanduser().resolve()
    if not source.exists():
        print(f"office-system: file not found: {source}", file=sys.stderr)
        return 2
    title = args.title or source.stem
    entry_id = f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{slugify(title)}"
    base = entry_root(root, args.scope, args.project) / entry_id
    source_dir = base / "source"
    extracted_dir = base / "extracted"
    source_dir.mkdir(parents=True, exist_ok=True)
    copied = source_dir / source.name
    shutil.copy2(source, copied)

    kind = args.kind or classify_file(source)
    status, extractor = run_extraction(copied, extracted_dir, kind)
    review_status = "pending_review" if status == "local_extracted" else status
    entry = {
        "version": "1.0.0",
        "entry_id": entry_id,
        "scope": args.scope,
        "project_id": args.project,
        "title": title,
        "kind": kind,
        "mime_type": mimetypes.guess_type(source.name)[0],
        "source_file": str(copied.relative_to(root)),
        "extracted_dir": str(extracted_dir.relative_to(root)),
        "status": review_status,
        "extractor": extractor,
        "created_at": now_iso(),
        "agent_readable": args.approve,
        "notes": args.notes or "",
    }
    if args.approve:
        entry["status"] = "approved_for_agent_use"
    write_json(base / "entry.json", entry)
    append_log(root, {"event": "knowledge_add_file", "entry_id": entry_id, "scope": args.scope, "project": args.project})
    print(json.dumps(entry, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def add_text_entry(args: argparse.Namespace) -> int:
    root = system_root()
    body = args.body if args.body is not None else sys.stdin.read()
    title = args.title
    entry_id = f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{slugify(title)}"
    base = entry_root(root, args.scope, args.project) / entry_id
    write_text(base / "source" / "entry.md", body.rstrip() + "\n")
    write_text(base / "extracted" / "text.md", body.rstrip() + "\n")
    entry = {
        "version": "1.0.0",
        "entry_id": entry_id,
        "scope": args.scope,
        "project_id": args.project,
        "title": title,
        "kind": "text",
        "source_file": str((base / "source" / "entry.md").relative_to(root)),
        "extracted_dir": str((base / "extracted").relative_to(root)),
        "status": "approved_for_agent_use" if args.approve else "pending_review",
        "extractor": "gui_text_entry",
        "created_at": now_iso(),
        "agent_readable": args.approve,
    }
    write_json(base / "entry.json", entry)
    append_log(root, {"event": "knowledge_add_text", "entry_id": entry_id, "scope": args.scope, "project": args.project})
    print(json.dumps(entry, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def add_rule(args: argparse.Namespace) -> int:
    root = system_root()
    body = args.body if args.body is not None else sys.stdin.read()
    filename = f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{slugify(args.title)}.md"
    if args.scope == "global":
        target = root / "rules" / "global" / filename
    elif args.scope == "agent":
        if not args.agent:
            print("office-system: --agent is required for agent rule", file=sys.stderr)
            return 2
        target = root / "rules" / "agents" / f"{args.agent}.md"
        body = f"\n\n## {args.title}\n\n{body.rstrip()}\n"
        if target.exists():
            target.write_text(target.read_text(encoding="utf-8") + body, encoding="utf-8")
            print(str(target))
            return 0
    else:
        if not args.project:
            print("office-system: --project is required for project rule", file=sys.stderr)
            return 2
        target = ensure_project(root, args.project) / "rules" / filename
    text = f"# {args.title}\n\n{body.rstrip()}\n"
    write_text(target, text)
    append_log(root, {"event": "rule_add", "scope": args.scope, "target": str(target.relative_to(root))})
    print(str(target))
    return 0


def iter_entry_manifests(path: Path) -> list[Path]:
    if not path.exists():
        return []
    return sorted(path.glob("*/entry.json"))


def load_entries(root: Path, base: Path) -> list[dict[str, Any]]:
    entries = []
    for manifest in iter_entry_manifests(base):
        try:
            entry = read_json(manifest)
            entry["_manifest"] = str(manifest.relative_to(root))
            entries.append(entry)
        except Exception:
            continue
    return entries


def tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z0-9_]+|[\u4e00-\u9fff]", text.lower())
    return [word for word in words if word.strip()]


def chunk_text(text: str, size: int = 1200, overlap: int = 180) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + size)
        chunks.append(text[start:end].strip())
        if end >= len(text):
            break
        start = max(0, end - overlap)
    return chunks


def extracted_text_for_entry(root: Path, entry: dict[str, Any]) -> str:
    extracted = root / str(entry.get("extracted_dir", ""))
    if not extracted.exists():
        return ""
    parts: list[str] = []
    for path in sorted(extracted.glob("*.md")) + sorted(extracted.glob("*.txt")):
        try:
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            continue
    return "\n\n".join(parts)


def rag_entry_base(root: Path, scope: str, project: str | None) -> Path:
    if scope == "company":
        return root / "knowledge" / "company" / "entries"
    if not project:
        print("office-system: --project is required for project RAG", file=sys.stderr)
        raise SystemExit(2)
    return ensure_project(root, project) / "knowledge" / "entries"


def rag_index_dir(root: Path, scope: str, project: str | None) -> Path:
    if scope == "company":
        return root / "knowledge" / "company" / "index"
    if not project:
        print("office-system: --project is required for project RAG", file=sys.stderr)
        raise SystemExit(2)
    return ensure_project(root, project) / "knowledge" / "index"


def try_embed(texts: list[str], model_name: str) -> tuple[list[list[float]] | None, str]:
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore
    except Exception:
        return None, "sentence_transformers_not_installed"
    try:
        model = SentenceTransformer(model_name)
        vectors = model.encode(texts, normalize_embeddings=True).tolist()
        return vectors, model_name
    except Exception as exc:
        return None, f"embedding_failed:{exc}"


def rag_index(args: argparse.Namespace) -> int:
    root = system_root()
    entries = load_entries(root, rag_entry_base(root, args.scope, args.project))
    records: list[dict[str, Any]] = []
    for entry in entries:
        if entry.get("status") == "archived":
            continue
        text = extracted_text_for_entry(root, entry)
        for index, chunk in enumerate(chunk_text(text, args.chunk_chars, args.chunk_overlap), start=1):
            records.append(
                {
                    "chunk_id": f"{entry.get('entry_id')}::{index}",
                    "entry_id": entry.get("entry_id"),
                    "title": entry.get("title"),
                    "scope": args.scope,
                    "project_id": args.project,
                    "source_file": entry.get("source_file"),
                    "status": entry.get("status"),
                    "text": chunk,
                    "tokens": tokenize(chunk),
                }
            )

    mode = args.mode
    embedding_status = "not_requested"
    if records and mode in {"auto", "embedding"}:
        vectors, embedding_status = try_embed([record["text"] for record in records], args.embedding_model)
        if vectors:
            for record, vector in zip(records, vectors):
                record["embedding"] = vector
            mode = "embedding"
        elif args.mode == "embedding":
            print(f"office-system: embedding index failed: {embedding_status}", file=sys.stderr)
            return 1
        else:
            mode = "lexical"
    elif mode == "auto":
        mode = "lexical"

    target_dir = rag_index_dir(root, args.scope, args.project)
    target_dir.mkdir(parents=True, exist_ok=True)
    index_file = target_dir / "index.jsonl"
    with index_file.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
    meta = {
        "version": "1.0.0",
        "scope": args.scope,
        "project_id": args.project,
        "mode": mode,
        "embedding_model": args.embedding_model if mode == "embedding" else None,
        "embedding_status": embedding_status,
        "chunks": len(records),
        "created_at": now_iso(),
    }
    write_json(target_dir / "index.meta.json", meta)
    append_log(root, {"event": "rag_index", "scope": args.scope, "project": args.project, "chunks": len(records), "mode": mode})
    print(json.dumps(meta, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def lexical_score(query_tokens: list[str], record_tokens: list[str]) -> float:
    if not query_tokens or not record_tokens:
        return 0.0
    counts: dict[str, int] = {}
    for token in record_tokens:
        counts[token] = counts.get(token, 0) + 1
    score = 0.0
    for token in query_tokens:
        score += math.log1p(counts.get(token, 0))
    return score / math.sqrt(len(record_tokens))


def dot(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right))


def rag_search(args: argparse.Namespace) -> int:
    root = system_root()
    index_dir = rag_index_dir(root, args.scope, args.project)
    index_file = index_dir / "index.jsonl"
    if not index_file.exists():
        print(f"office-system: RAG index not found: {index_file}", file=sys.stderr)
        return 2
    meta = read_json(index_dir / "index.meta.json") if (index_dir / "index.meta.json").exists() else {}
    records = []
    with index_file.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                records.append(json.loads(line))

    scored: list[tuple[float, dict[str, Any]]] = []
    if meta.get("mode") == "embedding":
        vectors, status = try_embed([args.query], meta.get("embedding_model") or args.embedding_model)
        if vectors:
            query_vector = vectors[0]
            for record in records:
                vector = record.get("embedding")
                if vector:
                    scored.append((dot(query_vector, vector), record))
        else:
            print(f"office-system: embedding search unavailable, falling back to lexical: {status}", file=sys.stderr)

    if not scored:
        query_tokens = tokenize(args.query)
        scored = [(lexical_score(query_tokens, record.get("tokens", [])), record) for record in records]

    results = [
        {
            "score": score,
            "chunk_id": record.get("chunk_id"),
            "entry_id": record.get("entry_id"),
            "title": record.get("title"),
            "source_file": record.get("source_file"),
            "status": record.get("status"),
            "text": record.get("text"),
        }
        for score, record in sorted(scored, key=lambda item: item[0], reverse=True)[: args.limit]
        if score > 0
    ]
    print(json.dumps({"query": args.query, "scope": args.scope, "project_id": args.project, "results": results}, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def context(args: argparse.Namespace) -> int:
    root = system_root()
    agent = args.agent
    project = args.project
    project_dir = ensure_project(root, project) if project else None
    project_data = read_json(project_dir / "project.json") if project_dir else None

    print("# Digital Office Agent Context")
    print()
    print("## Priority")
    print("1. Current user task and explicit project selection")
    print("2. System bootstrap and company global rules")
    print("3. Active project rules and project knowledge source files")
    print("4. Agent-specific rules")
    print("5. Company global knowledge and approved methodologies")
    print("6. Licensed industry references mounted by entitlement")
    print("7. KeyMemory project relay snapshots, preferences, approved summaries, and retrieval pointers")
    print()
    print("Fact authority: project knowledge > company global knowledge > licensed industry reference > KeyMemory.")
    print("Handoff authority: current task > KeyMemory project relay > project latest decisions > company methods.")
    print("If KeyMemory or licensed references conflict with source-backed project or company knowledge, source-backed knowledge wins.")
    print()

    print("## Rule Layers")
    for path in sorted((root / "rules" / "global").glob("*.md")):
        print(f"- company/global: {path.relative_to(root)}")
    if project_dir:
        for path in sorted((project_dir / "rules").glob("*.md")):
            print(f"- project/{project}: {path.relative_to(root)}")
    if agent:
        agent_rule = root / "rules" / "agents" / f"{agent}.md"
        if agent_rule.exists():
            print(f"- agent/{agent}: {agent_rule.relative_to(root)}")
    print()

    if project_data:
        print("## Project")
        print(f"- id: {project_data.get('project_id')}")
        print(f"- name: {project_data.get('name')}")
        print(f"- status: {project_data.get('status')}")
        print(f"- agent_roster: {', '.join(project_data.get('agent_roster', []))}")
        print(f"- methodology_schedule: {project_data.get('methodology_promotion', {}).get('schedule')}")
        print()

    print("## Project Knowledge")
    if project_dir:
        entries = load_entries(root, project_dir / "knowledge" / "entries")
        if entries:
            for entry in entries:
                print(f"- {entry.get('entry_id')}: {entry.get('title')} [{entry.get('kind')}, {entry.get('status')}]")
                print(f"  source: {entry.get('source_file')}")
                print(f"  extracted: {entry.get('extracted_dir')}")
        else:
            print("- none")
    else:
        print("- no active project")
    print()

    print("## Company Knowledge")
    company_entries = load_entries(root, root / "knowledge" / "company" / "entries")
    if company_entries:
        for entry in company_entries:
            print(f"- {entry.get('entry_id')}: {entry.get('title')} [{entry.get('kind')}, {entry.get('status')}]")
            print(f"  source: {entry.get('source_file')}")
    else:
        print("- no entry manifests yet")
    print()
    print("## KeyMemory")
    print("- Use after source-backed project and company knowledge.")
    print("- Allowed: preferences, durable operating memories, approved methodology summaries, semantic pointers.")
    print("- Forbidden: raw PDF/Word/image storage, unapproved project drafts, ordinary plaintext secrets.")
    return 0


def create_project(args: argparse.Namespace) -> int:
    root = system_root()
    project_id = args.project or slugify(args.name)
    agents = [item.strip() for item in args.agents.split(",") if item.strip()] if args.agents else []
    target = copy_template_project(root, project_id, args.name, agents, args.methodology_schedule)
    append_log(root, {"event": "project_create", "project": project_id})
    print(str(target))
    return 0


def methodology_draft(args: argparse.Namespace) -> int:
    root = system_root()
    project_dir = ensure_project(root, args.project)
    project = read_json(project_dir / "project.json")
    entries = load_entries(root, project_dir / "knowledge" / "entries")
    stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    target = project_dir / "reports" / "methodology-review" / "drafts" / f"{stamp}-methodology-summary.md"
    lines = [
        f"# Methodology Summary Draft: {project.get('name')}",
        "",
        f"- Project ID: {project.get('project_id')}",
        f"- Period: {args.period}",
        f"- Created at: {now_iso()}",
        "- State: draft_created",
        "",
        "## User Review Required",
        "",
        "This draft must be shown in the GUI. The user may edit it before approval. It must not be promoted to company knowledge until the user confirms.",
        "",
        "## Evidence Inventory",
    ]
    if entries:
        for entry in entries:
            lines.append(f"- {entry.get('entry_id')}: {entry.get('title')} [{entry.get('kind')}, {entry.get('status')}]")
    else:
        lines.append("- No project knowledge entries yet.")
    lines.extend(
        [
            "",
            "## Reusable Methodology",
            "",
            "TODO: Summarize what worked, what failed, reusable workflows, decision rules, templates, and risks.",
            "",
            "## Applicability",
            "",
            "TODO: Explain which future projects should reuse this methodology and which should not.",
            "",
            "## User Edits",
            "",
            "TODO: GUI user may edit this section before approval.",
        ]
    )
    write_text(target, "\n".join(lines) + "\n")
    append_log(root, {"event": "methodology_draft", "project": args.project, "draft": str(target.relative_to(root))})
    print(str(target))
    return 0


def methodology_approve(args: argparse.Namespace) -> int:
    root = system_root()
    project_dir = ensure_project(root, args.project)
    draft = Path(args.draft)
    draft_base = (project_dir / "reports" / "methodology-review" / "drafts").resolve()
    if not draft.is_absolute():
        draft = draft_base / safe_component(args.draft.removesuffix(".md"), "draft id")
        if draft.suffix != ".md":
            draft = draft.with_suffix(".md")
    else:
        draft = draft.resolve()
        if not draft.is_relative_to(draft_base):
            print(f"office-system: methodology draft must be under {draft_base}", file=sys.stderr)
            return 2
    if not draft.exists():
        print(f"office-system: draft not found: {draft}", file=sys.stderr)
        return 2
    if not args.confirmed:
        print("office-system: approval requires --confirmed after GUI user review/edit", file=sys.stderr)
        return 2
    target = root / "knowledge" / "company" / "methodologies" / "approved" / draft.name
    shutil.copy2(draft, target)
    append_log(root, {"event": "methodology_approve", "project": args.project, "target": str(target.relative_to(root))})
    print(str(target))
    return 0


def relay_add(args: argparse.Namespace) -> int:
    root = system_root()
    project_dir = ensure_project(root, args.project)
    refs = args.source_ref or []
    next_actions = args.next_action or []
    body = args.body if args.body is not None else sys.stdin.read()
    relay = {
        "version": "1.0.0",
        "relay_id": f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}",
        "project_id": args.project,
        "subproject_id": args.subproject,
        "agent": args.agent,
        "title": args.title,
        "summary": body.strip(),
        "status": args.status,
        "source_refs": refs,
        "next_actions": next_actions,
        "created_at": now_iso(),
        "authority": "relay_only",
        "sync_status": "pending_keymemory_sync",
    }
    outbox = project_dir / "relay" / "keymemory-outbox.jsonl"
    outbox.parent.mkdir(parents=True, exist_ok=True)
    with outbox.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(relay, ensure_ascii=False, sort_keys=True) + "\n")
    append_log(root, {"event": "relay_add", "project": args.project, "agent": args.agent, "relay_id": relay["relay_id"]})
    print(json.dumps(relay, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def agent_request_config_path(root: Path) -> Path:
    configured = os.environ.get("DIGITAL_OFFICE_AGENT_REQUEST_CONFIG")
    if configured:
        return Path(configured).expanduser()
    return root / "agent-requests" / "config.json"


def load_agent_request_config(root: Path) -> dict[str, Any]:
    path = agent_request_config_path(root)
    if path.exists():
        return read_json(path)
    example = root / "agent-requests" / "config.example.json"
    if example.exists():
        return read_json(example)
    return {
        "tenant_id": "",
        "server_url": "",
        "status_url": "",
        "auth_env": "DIGITAL_OFFICE_AGENT_REQUEST_TOKEN",
        "customer_visible_statuses": {
            "received": "接收需求",
            "in_progress": "正在推动需求",
            "completed": "已完成需求",
            "downloaded_deployed": "已下载部署",
            "pending_user_confirmation": "等待用户确认",
            "needs_tuning": "通过对话微调需求",
            "paused_by_user": "暂不处理",
        },
    }


def agent_request_labels(config: dict[str, Any]) -> dict[str, str]:
    labels = dict(config.get("customer_visible_statuses", {}))
    labels.update(config.get("internal_statuses", {}))
    return labels


def send_json(url: str, payload: dict[str, Any], auth_env: str, timeout: int) -> tuple[int, str]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(url, data=data, method="POST")
    request.add_header("Content-Type", "application/json")
    token = os.environ.get(auth_env, "")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, response.read().decode("utf-8", errors="replace")


def agent_request_submit(args: argparse.Namespace) -> int:
    root = system_root()
    config = load_agent_request_config(root)
    if config.get("require_user_submit_confirmation", True) and not args.confirmed:
        print("office-system: agent request submission requires --confirmed after user review", file=sys.stderr)
        return 2

    body = args.body if args.body is not None else sys.stdin.read()
    request_id = f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:8]}"
    labels = agent_request_labels(config)
    payload = {
        "version": "1.0.0",
        "kind": "agent-plugin-request",
        "request_id": request_id,
        "tenant_id": config.get("tenant_id", ""),
        "project_id": args.project,
        "requested_by": args.requested_by,
        "title": args.title,
        "priority": args.priority,
        "body": body.strip(),
        "status": "received",
        "status_label": labels.get("received", "接收需求"),
        "created_at": now_iso(),
        "source": "digital_office_secretary_agent",
        "skill_changes_requested": False,
        "notes": "This request asks the provider to design and publish an Agent plugin package. Customer-site skill add/remove/recompose operations are forbidden.",
    }
    payload = redact_obj(payload, config)

    outbox = root / "agent-requests" / "outbox" / f"{request_id}.json"
    write_json(outbox, {**payload, "sync_status": "pending_send"})

    server_url = config.get("server_url")
    sync_status = "pending_server_config"
    receipt: dict[str, Any] | None = None
    if server_url:
        try:
            status, response_body = send_json(server_url, payload, config.get("auth_env", "DIGITAL_OFFICE_AGENT_REQUEST_TOKEN"), args.timeout)
            sync_status = "sent"
            receipt = {
                "time": now_iso(),
                "request_id": request_id,
                "server_url": server_url,
                "status": status,
                "response": response_body[:2000],
            }
            write_json(root / "agent-requests" / "receipts" / f"{request_id}.json", receipt)
        except urllib.error.URLError as exc:
            sync_status = "send_failed"
            receipt = {
                "time": now_iso(),
                "request_id": request_id,
                "server_url": server_url,
                "error": str(exc),
            }
            write_json(root / "agent-requests" / "receipts" / f"{request_id}-failed.json", receipt)

    state = {
        **payload,
        "sync_status": sync_status,
        "outbox": str(outbox.relative_to(root)),
        "receipt": receipt,
    }
    write_json(root / "agent-requests" / "status" / f"{request_id}.json", state)
    append_log(root, {"event": "agent_request_submit", "request_id": request_id, "status": "received", "sync_status": sync_status})
    print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if sync_status != "send_failed" else 1


def agent_request_set_status(args: argparse.Namespace) -> int:
    root = system_root()
    config = load_agent_request_config(root)
    labels = agent_request_labels(config)
    request_id = safe_component(args.request_id, "request id")
    status_file = root / "agent-requests" / "status" / f"{request_id}.json"
    state = read_json(status_file) if status_file.exists() else {
        "version": "1.0.0",
        "kind": "agent-plugin-request-status",
        "request_id": request_id,
        "tenant_id": config.get("tenant_id", ""),
    }
    state["status"] = args.status
    state["status_label"] = labels.get(args.status, args.status)
    state["status_updated_at"] = now_iso()
    if args.message:
        state["status_message"] = args.message
    if args.package:
        state["agent_plugin_package"] = args.package
    write_json(status_file, state)
    append_log(root, {"event": "agent_request_set_status", "request_id": request_id, "status": args.status})
    print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def agent_request_status(args: argparse.Namespace) -> int:
    root = system_root()
    request_id = safe_component(args.request_id, "request id")
    status_file = root / "agent-requests" / "status" / f"{request_id}.json"
    if not status_file.exists():
        print(f"office-system: request status not found: {request_id}", file=sys.stderr)
        return 2
    print(json.dumps(read_json(status_file), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


SKILL_CHANGE_PATTERNS = [
    re.compile(r"(?i)\b(add|remove|delete|install|uninstall|replace|compose|recompose)\b.{0,40}\bskill\b"),
    re.compile(r"(?i)\bskill\b.{0,40}\b(add|remove|delete|install|uninstall|replace|compose|recompose)\b"),
    re.compile(r"(增加|新增|删除|移除|安装|卸载|替换|重新组合).{0,20}skill", re.IGNORECASE),
    re.compile(r"skill.{0,20}(增加|新增|删除|移除|安装|卸载|替换|重新组合)", re.IGNORECASE),
]


def contains_skill_change(text: str) -> bool:
    return any(pattern.search(text) for pattern in SKILL_CHANGE_PATTERNS)


def agent_improvement_draft(args: argparse.Namespace) -> int:
    root = system_root()
    agent = registered_agent(root, args.agent)
    body = args.body if args.body is not None else sys.stdin.read()
    if contains_skill_change(body):
        print("office-system: existing Agent improvements may change SOUL/workflow only; skill add/remove/install/recompose is forbidden", file=sys.stderr)
        return 2
    stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    draft_id = f"{stamp}-{args.kind}-{slugify(args.title)}"
    target = root / "agent-improvements" / agent / "drafts" / f"{draft_id}.md"
    lines = [
        f"# Agent Improvement Draft: {args.title}",
        "",
        f"- Agent: {agent}",
        f"- Kind: {args.kind}",
        f"- Project: {args.project or ''}",
        f"- Created at: {now_iso()}",
        "- State: draft_created",
        "- Skill changes: forbidden",
        "",
        "## User-Approved Change",
        "",
        body.strip(),
        "",
        "## Activation Rule",
        "",
        "This draft may improve the existing Agent SOUL document or workflow overlay only. It must not add, remove, install, or recompose skills.",
    ]
    write_text(target, "\n".join(lines) + "\n")
    append_log(root, {"event": "agent_improvement_draft", "agent": agent, "kind": args.kind, "draft": str(target.relative_to(root))})
    print(str(target))
    return 0


def agent_improvement_approve(args: argparse.Namespace) -> int:
    root = system_root()
    agent = registered_agent(root, args.agent)
    if not args.confirmed:
        print("office-system: approving an Agent improvement requires --confirmed after user review", file=sys.stderr)
        return 2
    draft = Path(args.draft).expanduser()
    draft_base = (root / "agent-improvements" / agent / "drafts").resolve()
    if not draft.is_absolute():
        draft_name = safe_component(args.draft.removesuffix(".md"), "draft id") + ".md"
        draft = draft_base / draft_name
    else:
        draft = draft.resolve()
        if not draft.is_relative_to(draft_base):
            print(f"office-system: draft must be under {draft_base}", file=sys.stderr)
            return 2
    if not draft.exists():
        print(f"office-system: draft not found: {draft}", file=sys.stderr)
        return 2
    text = draft.read_text(encoding="utf-8", errors="replace")
    if contains_skill_change(text):
        print("office-system: draft contains a forbidden skill change request", file=sys.stderr)
        return 2
    target = root / "agent-improvements" / agent / "approved" / draft.name
    shutil.copy2(draft, target)
    append_log(root, {"event": "agent_improvement_approve", "agent": agent, "target": str(target.relative_to(root))})
    print(str(target))
    return 0


def resolve_plugin_manifest(package: str) -> tuple[Path, Path, dict[str, Any]]:
    path = Path(package).expanduser()
    if path.is_file():
        return path.parent, path, read_json(path)
    candidates = [
        path / "agent-plugin.json",
        path / "plugin.manifest.json",
        path / "agent-plugin.manifest.json",
    ]
    for candidate in candidates:
        if candidate.exists():
            return path, candidate, read_json(candidate)
    print(f"office-system: no Agent plugin manifest found in {path}", file=sys.stderr)
    raise SystemExit(2)


def agent_plugin_report(args: argparse.Namespace) -> int:
    root = system_root()
    package_dir, manifest_path, manifest = resolve_plugin_manifest(args.package)
    agent_id = manifest.get("agent_id") or manifest.get("registry_entry", {}).get("id")
    if not agent_id:
        print("office-system: Agent plugin manifest must contain agent_id", file=sys.stderr)
        return 2
    agent_id = safe_component(agent_id, "agent id")
    registry = read_json(root / "agents.registry.json")
    current_agents = sorted(registry.get("agents", {}).keys())
    workflows = manifest.get("workflows", {})
    route_tests = manifest.get("route_tests", [])
    stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    report_id = f"{stamp}-{slugify(agent_id)}"
    target = root / "agent-plugins" / "reports" / f"{report_id}-integration-report.md"
    lines = [
        f"# New Agent Integration Report: {manifest.get('display_name', agent_id)}",
        "",
        "- State: pending_user_confirmation",
        f"- Agent ID: {agent_id}",
        f"- Package: {package_dir}",
        f"- Manifest: {manifest_path}",
        f"- Created at: {now_iso()}",
        f"- Report ID: {report_id}",
        "",
        "## Current System",
        "",
        f"- Existing agents: {', '.join(current_agents)}",
        f"- Target project: {args.project or 'global / not project-specific'}",
        "",
        "## How This Agent Will Be Added",
        "",
        "1. Copy the bundled profile template into the local profiles directory if needed.",
        "2. Add the packaged registry entry to `agent-system/agents.registry.json`.",
        "3. Add packaged workflow definitions and route tests.",
        "4. Optionally add the Agent to the selected project roster.",
        "5. Run router health checks before the Agent becomes active.",
        "",
        "## Workflow Impact",
        "",
    ]
    if workflows:
        for name, workflow in workflows.items():
            lines.append(f"- {name}: {workflow.get('label', '')}")
    else:
        lines.append("- No extra workflows declared by the package.")
    lines.extend(["", "## Route Tests", ""])
    if route_tests:
        for test in route_tests:
            lines.append(f"- `{test.get('prompt')}` -> `{test.get('expect')}`")
    else:
        lines.append("- No route tests declared by the package.")
    lines.extend(
        [
            "",
            "## User Confirmation Required",
            "",
            "The new Agent is not registered yet. Show this report in the GUI and wait for user confirmation.",
            "",
            "Available GUI actions:",
            "",
            "1. Confirm: register and deploy this Agent into the selected workflow.",
            "2. Tune Through Conversation: keep discussing and update the integration report before deployment.",
            "3. Pause: do not process now; keep the task suspended until the user returns.",
        ]
    )
    write_text(target, "\n".join(lines) + "\n")
    state = {
        "report_id": report_id,
        "request_id": safe_component(args.request_id, "request id") if args.request_id else None,
        "agent_id": agent_id,
        "status": "pending_user_confirmation",
        "status_label": "等待用户确认",
        "package": str(package_dir),
        "manifest": str(manifest_path),
        "report": str(target.relative_to(root)),
        "project_id": args.project,
        "created_at": now_iso(),
        "allowed_actions": ["confirm", "tune", "pause"],
    }
    write_json(root / "agent-plugins" / "status" / f"{report_id}.json", state)
    if args.request_id:
        request_id = safe_component(args.request_id, "request id")
        status_file = root / "agent-requests" / "status" / f"{request_id}.json"
        request_state = read_json(status_file) if status_file.exists() else {"request_id": args.request_id}
        request_state["status"] = "pending_user_confirmation"
        request_state["status_label"] = "等待用户确认"
        request_state["agent_plugin_report"] = str(target.relative_to(root))
        request_state["agent_plugin_report_id"] = report_id
        request_state["status_updated_at"] = now_iso()
        write_json(status_file, request_state)
    append_log(root, {"event": "agent_plugin_report", "agent": agent_id, "report": str(target.relative_to(root)), "report_id": report_id})
    print(str(target))
    return 0


def agent_plugin_decision(args: argparse.Namespace) -> int:
    root = system_root()
    report_id = safe_component(args.report_id, "report id")
    status_file = root / "agent-plugins" / "status" / f"{report_id}.json"
    if not status_file.exists():
        print(f"office-system: plugin report status not found: {report_id}", file=sys.stderr)
        return 2
    state = read_json(status_file)
    if args.decision == "confirm":
        state["status"] = "confirmed_for_activation"
        state["status_label"] = "已确认，等待注册部署"
        state["next_action"] = "run agent-plugin-activate --confirmed"
        state.pop("pause_reason", None)
    elif args.decision == "tune":
        state["status"] = "needs_tuning"
        state["status_label"] = "通过对话微调需求"
        state.pop("pause_reason", None)
        if args.message:
            state.setdefault("tuning_notes", []).append({"time": now_iso(), "message": args.message})
        state["next_action"] = "secretary continues requirement conversation and regenerates the integration report"
    elif args.decision == "pause":
        state["status"] = "paused_by_user"
        state["status_label"] = "暂不处理"
        if args.message:
            state["pause_reason"] = args.message
        state["next_action"] = "do nothing until the user resumes"
    state["decision_updated_at"] = now_iso()
    write_json(status_file, state)
    append_log(root, {"event": "agent_plugin_decision", "report_id": report_id, "decision": args.decision})
    print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def agent_plugin_activate(args: argparse.Namespace) -> int:
    root = system_root()
    request_id = safe_component(args.request_id, "request id") if args.request_id else None
    if not args.confirmed:
        print("office-system: Agent plugin activation requires --confirmed after user review of the integration report", file=sys.stderr)
        return 2
    if args.report and not Path(args.report).expanduser().exists():
        print(f"office-system: integration report not found: {args.report}", file=sys.stderr)
        return 2
    package_dir, manifest_path, manifest = resolve_plugin_manifest(args.package)
    registry_entry = manifest.get("registry_entry")
    if not isinstance(registry_entry, dict):
        print("office-system: Agent plugin manifest must include registry_entry", file=sys.stderr)
        return 2
    agent_id = manifest.get("agent_id") or registry_entry.get("id")
    if not agent_id:
        print("office-system: Agent plugin manifest must contain agent_id", file=sys.stderr)
        return 2
    agent_id = safe_component(agent_id, "agent id")

    registry_path_value = root / "agents.registry.json"
    registry = read_json(registry_path_value)
    if agent_id in registry.get("agents", {}) and not args.replace_agent:
        print(f"office-system: agent already registered: {agent_id}; pass --replace-agent to replace", file=sys.stderr)
        return 2

    stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    target_profile: Path | None = None
    profile_backup: Path | None = None
    profile_name = registry_entry.get("profile")
    if profile_name:
        profile_name = safe_component(profile_name, "profile name")
        source_profile = package_dir / "profiles" / profile_name
        target_profile = root.parent / "profiles" / profile_name
        if source_profile.exists():
            if target_profile.exists() and not args.replace_profile:
                print(f"office-system: profile already exists: {target_profile}; pass --replace-profile to replace", file=sys.stderr)
                return 2
            if target_profile.exists():
                profile_backup = target_profile.with_name(f"{target_profile.name}.bak.{stamp}")
                shutil.copytree(target_profile, profile_backup)
                shutil.rmtree(target_profile)
            shutil.copytree(source_profile, target_profile)

    backup = registry_path_value.with_suffix(f".json.bak.{stamp}")
    shutil.copy2(registry_path_value, backup)
    entry = dict(registry_entry)
    entry.pop("id", None)
    registry.setdefault("agents", {})[agent_id] = entry
    registry.setdefault("aliases", {}).update(manifest.get("aliases", {}))
    registry.setdefault("workflows", {}).update(manifest.get("workflows", {}))
    registry.setdefault("route_tests", []).extend(manifest.get("route_tests", []))
    write_json(registry_path_value, registry)

    project_file: Path | None = None
    project_backup: dict[str, Any] | None = None
    if args.project:
        project_dir = ensure_project(root, args.project)
        project_file = project_dir / "project.json"
        project = read_json(project_file)
        project_backup = json.loads(json.dumps(project))
        roster = project.setdefault("agent_roster", [])
        if agent_id not in roster:
            roster.append(agent_id)
        write_json(project_file, project)

    router = root.parent / "scripts" / "agent-router"
    health_proc = subprocess.run([str(router), "--health"], text=True, capture_output=True)
    if health_proc.returncode != 0:
        shutil.copy2(backup, registry_path_value)
        if project_file and project_backup is not None:
            write_json(project_file, project_backup)
        if target_profile and target_profile.exists():
            shutil.rmtree(target_profile)
        if profile_backup and profile_backup.exists():
            shutil.copytree(profile_backup, target_profile)
        print("office-system: router health failed after Agent registration; registry rolled back", file=sys.stderr)
        if health_proc.stdout:
            print(health_proc.stdout, file=sys.stderr)
        if health_proc.stderr:
            print(health_proc.stderr, file=sys.stderr)
        return 1

    state = {
        "agent_id": agent_id,
        "status": "activated",
        "status_label": "已下载部署",
        "request_id": request_id,
        "package": str(package_dir),
        "manifest": str(manifest_path),
        "registry_backup": str(backup),
        "project_id": args.project,
        "router_health": "passed",
    }
    if request_id:
        status_file = root / "agent-requests" / "status" / f"{request_id}.json"
        request_state = read_json(status_file) if status_file.exists() else {"request_id": request_id}
        request_state["status"] = "downloaded_deployed"
        request_state["status_label"] = "已下载部署"
        request_state["deployed_agent_id"] = agent_id
        request_state["status_updated_at"] = now_iso()
        write_json(status_file, request_state)
    append_log(root, {"event": "agent_plugin_activate", "agent": agent_id, "project": args.project})
    print(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def consent_path(root: Path) -> Path:
    configured = os.environ.get("DIGITAL_OFFICE_CONSENT_FILE")
    if configured:
        return Path(configured).expanduser()
    return root / "data-sharing" / "consent.json"


def load_consent(root: Path) -> dict[str, Any]:
    path = consent_path(root)
    if path.exists():
        return read_json(path)
    example = root / "data-sharing" / "consent.example.json"
    if example.exists():
        return read_json(example)
    return {"enabled": False, "allowed_scopes": {}}


REDACTION_PATTERNS = {
    "email": re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"),
    "phone_cn": re.compile(r"\b1[3-9]\d{9}\b"),
    "id_card_cn": re.compile(r"\b\d{17}[\dXx]\b"),
    "api_key": re.compile(r"\b(?:sk|gho|ghp|xoxb|hf)_[A-Za-z0-9_\-]{16,}\b"),
    "bearer_token": re.compile(r"Bearer\s+[A-Za-z0-9._\-]{16,}", re.IGNORECASE),
    "secret_like": re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*[:=]\s*[^\s,;]{6,}"),
}


def redact_text(text: str, consent: dict[str, Any]) -> str:
    redaction = consent.get("redaction", {})
    if not redaction.get("enabled", True):
        return text
    replacement = redaction.get("replace_with", "[REDACTED]")
    for name in redaction.get("patterns", []):
        pattern = REDACTION_PATTERNS.get(name)
        if pattern:
            text = pattern.sub(replacement, text)
    return text


def redact_obj(value: Any, consent: dict[str, Any]) -> Any:
    if isinstance(value, str):
        return redact_text(value, consent)
    if isinstance(value, list):
        return [redact_obj(item, consent) for item in value]
    if isinstance(value, dict):
        return {key: redact_obj(item, consent) for key, item in value.items()}
    return value


def read_jsonl(path: Path, limit: int | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
    return rows[-limit:] if limit else rows


def approved_methodology_summaries(root: Path, consent: dict[str, Any]) -> list[dict[str, Any]]:
    allowed = (
        consent.get("industry_experience_sharing", {}).get("enabled", False)
        and consent.get("allowed_scopes", {}).get("approved_methodologies", False)
    )
    if not allowed:
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted((root / "knowledge" / "company" / "methodologies" / "approved").glob("*.md")):
        text = path.read_text(encoding="utf-8", errors="replace")
        rows.append(
            {
                "path": str(path.relative_to(root)),
                "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "text": redact_text(text, consent),
            }
        )
    return rows


def relay_summaries(root: Path, consent: dict[str, Any]) -> list[dict[str, Any]]:
    allowed = (
        consent.get("industry_experience_sharing", {}).get("enabled", False)
        and consent.get("allowed_scopes", {}).get("project_relay_summaries", False)
    )
    if not allowed:
        return []
    rows: list[dict[str, Any]] = []
    for outbox in sorted((root / "projects").glob("*/relay/keymemory-outbox.jsonl")):
        for row in read_jsonl(outbox):
            sanitized = redact_obj(row, consent)
            project_id = str(sanitized.get("project_id", ""))
            subproject_id = str(sanitized.get("subproject_id", ""))
            source_refs = sanitized.get("source_refs", []) or []
            sanitized["project_hash"] = hashlib.sha256(project_id.encode("utf-8")).hexdigest() if project_id else ""
            sanitized["subproject_hash"] = hashlib.sha256(subproject_id.encode("utf-8")).hexdigest() if subproject_id else ""
            sanitized["source_ref_hashes"] = [
                hashlib.sha256(str(ref).encode("utf-8")).hexdigest() for ref in source_refs
            ]
            sanitized.pop("project_id", None)
            sanitized.pop("subproject_id", None)
            sanitized.pop("source_refs", None)
            rows.append(sanitized)
    return rows


def telemetry_payload(root: Path, consent: dict[str, Any]) -> dict[str, Any]:
    allowed = consent.get("allowed_scopes", {})
    health_data = {
        "agents_registry": (root / "agents.registry.json").exists(),
        "knowledge_registry": (root / "knowledge.registry.json").exists(),
        "rules_registry": (root / "rules" / "rules.registry.json").exists(),
        "multimodal_pipeline": (root / "multimodal.pipeline.json").exists(),
        "rag_pipeline": (root / "rag.pipeline.json").exists(),
        "tesseract": bool(shutil.which("tesseract")),
        "pdftotext": bool(shutil.which("pdftotext")),
        "sentence_transformers": bool(importlib.util.find_spec("sentence_transformers")),
    }
    payload: dict[str, Any] = {
        "version": "1.0.0",
        "tenant_id": consent.get("tenant_id"),
        "exported_at": now_iso(),
        "mode": consent.get("mode"),
        "experience_telemetry": consent.get("experience_telemetry", {}),
        "industry_experience_sharing": consent.get("industry_experience_sharing", {}),
        "contains_raw_documents": false_value(),
        "contains_raw_images": false_value(),
        "contains_raw_keymemory_records": false_value(),
        "health": health_data if allowed.get("system_health", True) else {},
        "model_capability_status": health_data if allowed.get("model_capability_status", True) else {},
        "route_events": read_jsonl(root / "logs" / "router-events.jsonl", limit=500) if allowed.get("agent_routes", True) else [],
        "office_events": read_jsonl(root / "logs" / "office-system.jsonl", limit=500) if allowed.get("workflow_metrics", True) else [],
        "approved_methodologies": approved_methodology_summaries(root, consent),
        "project_relay_summaries": relay_summaries(root, consent),
    }
    return redact_obj(payload, consent)


def false_value() -> bool:
    return False


def telemetry_status(args: argparse.Namespace) -> int:
    root = system_root()
    consent = load_consent(root)
    status = {
        "consent_file": str(consent_path(root)),
        "enabled": consent.get("enabled", False),
        "server_configured": bool(consent.get("server_url")),
        "experience_telemetry_enabled": consent.get("experience_telemetry", {}).get("enabled", False),
        "industry_experience_sharing_enabled": consent.get("industry_experience_sharing", {}).get("enabled", False),
        "allowed_scopes": consent.get("allowed_scopes", {}),
    }
    print(json.dumps(status, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def telemetry_export(args: argparse.Namespace) -> int:
    root = system_root()
    consent = load_consent(root)
    if not consent.get("enabled", False):
        print("office-system: telemetry disabled by consent file", file=sys.stderr)
        return 2
    payload = telemetry_payload(root, consent)
    stamp = dt.datetime.now().strftime("%Y%m%d%H%M%S")
    target = root / "data-sharing" / "exports" / f"{stamp}-telemetry-bundle.json"
    write_json(target, payload)
    append_log(root, {"event": "telemetry_export", "target": str(target.relative_to(root))})
    print(str(target))
    return 0


def telemetry_send(args: argparse.Namespace) -> int:
    root = system_root()
    consent = load_consent(root)
    if not consent.get("enabled", False):
        print("office-system: telemetry disabled by consent file", file=sys.stderr)
        return 2
    if consent.get("review", {}).get("require_admin_review_before_send", True) and not args.confirmed:
        print("office-system: telemetry-send requires --confirmed after admin review", file=sys.stderr)
        return 2
    server_url = consent.get("server_url")
    if not server_url:
        print("office-system: telemetry server_url is not configured", file=sys.stderr)
        return 2
    token = os.environ.get(consent.get("auth_env", "DIGITAL_OFFICE_TELEMETRY_TOKEN"), "")
    bundle = Path(args.bundle).expanduser()
    if not bundle.is_absolute():
        bundle = root / "data-sharing" / "exports" / args.bundle
    if not bundle.exists():
        print(f"office-system: bundle not found: {bundle}", file=sys.stderr)
        return 2
    data = bundle.read_bytes()
    request = urllib.request.Request(server_url, data=data, method="POST")
    request.add_header("Content-Type", "application/json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
            receipt = {
                "time": now_iso(),
                "bundle": str(bundle.relative_to(root)) if bundle.is_relative_to(root) else str(bundle),
                "server_url": server_url,
                "status": response.status,
                "response": body[:2000],
            }
    except urllib.error.URLError as exc:
        print(f"office-system: telemetry send failed: {exc}", file=sys.stderr)
        return 1
    target = root / "data-sharing" / "receipts" / f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-receipt.json"
    write_json(target, receipt)
    append_log(root, {"event": "telemetry_send", "receipt": str(target.relative_to(root))})
    print(json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def identity_context(args: argparse.Namespace) -> int:
    root = system_root()
    project = safe_component(args.project, "project id") if args.project else ""
    agent = registered_agent(root, args.agent) if args.agent else ""
    if project:
        ensure_project(root, project)
    claims = {
        "version": "1.0.0",
        "kind": "digital-office-identity-context",
        "tenant_id": safe_claim(args.tenant, "tenant id"),
        "deployment_id": safe_claim(args.deployment, "deployment id"),
        "user_id": safe_claim(args.user, "user id"),
        "user_role": safe_claim(args.role, "user role"),
        "project_id": project,
        "agent_id": agent,
        "workflow_run_id": safe_claim(args.workflow_run, "workflow run id", required=False),
        "session_id": safe_claim(args.session, "session id", required=False),
        "created_at": now_iso(),
    }
    append_log(root, {"event": "identity_context", "tenant_id": claims["tenant_id"], "deployment_id": claims["deployment_id"], "user_id": claims["user_id"], "project": project, "agent": agent})
    print(json.dumps(claims, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


CUSTOMER_OWNED_MOUNT_TARGETS = {"company_knowledge", "project_knowledge", "agent_specialist_context"}
PROVIDER_SOLD_MOUNT_TARGETS = {"licensed_company_reference", "licensed_project_reference", "licensed_agent_reference"}


def knowledge_source_mount(args: argparse.Namespace) -> int:
    root = system_root()
    source_class = args.source_class
    mount_target = args.mount_target
    project = safe_component(args.project, "project id") if args.project else ""
    agent = registered_agent(root, args.agent) if args.agent else ""
    if project:
        ensure_project(root, project)
    if mount_target in {"project_knowledge", "licensed_project_reference"} and not project:
        print("office-system: project-scoped knowledge mounts require --project", file=sys.stderr)
        return 2
    if mount_target in {"agent_specialist_context", "licensed_agent_reference"} and not agent:
        print("office-system: agent-scoped knowledge mounts require --agent", file=sys.stderr)
        return 2
    if source_class == "customer_owned_external_kb" and mount_target not in CUSTOMER_OWNED_MOUNT_TARGETS:
        print("office-system: customer-owned external KB cannot be mounted as licensed industry reference", file=sys.stderr)
        return 2
    if source_class == "provider_sold_industry_kb" and mount_target not in PROVIDER_SOLD_MOUNT_TARGETS:
        print("office-system: provider-sold industry KB must be mounted as licensed reference, not company/project source storage", file=sys.stderr)
        return 2
    mount_id = args.mount_id or f"{dt.datetime.now().strftime('%Y%m%d%H%M%S')}-{slugify(args.source_id)}"
    mount_id = safe_component(mount_id, "mount id")
    provider_sold = source_class == "provider_sold_industry_kb"
    record = {
        "version": "1.0.0",
        "kind": "digital-office-knowledge-source-mount",
        "mount_id": mount_id,
        "source_class": source_class,
        "source_id": safe_claim(args.source_id, "source id"),
        "display_name": safe_claim(args.display_name or args.source_id, "display name"),
        "provider": safe_claim(args.provider, "provider", required=False),
        "tenant_id": safe_claim(args.tenant, "tenant id"),
        "deployment_id": safe_claim(args.deployment, "deployment id"),
        "created_by": safe_claim(args.created_by, "created by"),
        "mount_target": mount_target,
        "project_id": project,
        "agent_id": agent,
        "entitlement_id": safe_claim(args.entitlement, "entitlement id", required=provider_sold),
        "license_sku": safe_claim(args.license_sku, "license sku", required=False),
        "allowed_users": [safe_claim(item, "allowed user") for item in (args.allowed_user or [])],
        "allowed_roles": [safe_claim(item, "allowed role") for item in (args.allowed_role or [])],
        "inside_digital_office_only": provider_sold,
        "download_allowed": not provider_sold,
        "export_allowed": not provider_sold,
        "plain_source_files_on_customer_host": not provider_sold,
        "retrieval_mode": "controlled_remote_retrieval" if provider_sold else args.sync_mode,
        "created_at": now_iso(),
        "status": "active",
    }
    target = root / "knowledge" / "mounts" / f"{mount_id}.json"
    if target.exists() and not args.replace:
        print(f"office-system: knowledge mount already exists: {mount_id}; pass --replace to replace", file=sys.stderr)
        return 2
    write_json(target, record)
    append_log(root, {"event": "knowledge_source_mounted", "mount_id": mount_id, "source_class": source_class, "mount_target": mount_target, "tenant_id": record["tenant_id"], "deployment_id": record["deployment_id"], "created_by": record["created_by"]})
    print(json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def knowledge_access_log(args: argparse.Namespace) -> int:
    root = system_root()
    project = safe_component(args.project, "project id") if args.project else ""
    agent = registered_agent(root, args.agent) if args.agent else ""
    if project:
        ensure_project(root, project)
    query_hash = hashlib.sha256((args.query or "").encode("utf-8")).hexdigest() if args.query else ""
    event = {
        "time": now_iso(),
        "event": "knowledge_access",
        "tenant_id": safe_claim(args.tenant, "tenant id"),
        "deployment_id": safe_claim(args.deployment, "deployment id"),
        "user_id": safe_claim(args.user, "user id"),
        "user_role": safe_claim(args.role, "user role"),
        "project_id": project,
        "agent_id": agent,
        "workflow_run_id": safe_claim(args.workflow_run, "workflow run id", required=False),
        "source_class": args.source_class,
        "source_id": safe_claim(args.source_id, "source id"),
        "mount_id": safe_component(args.mount_id, "mount id"),
        "knowledge_pack_id": safe_claim(args.knowledge_pack, "knowledge pack id", required=False),
        "entitlement_id": safe_claim(args.entitlement, "entitlement id", required=False),
        "query_hash": query_hash,
        "result_source_ids": [safe_claim(item, "result source id") for item in (args.result_source_id or [])],
        "snippet_count": args.snippet_count,
        "decision": args.decision,
        "deny_reason": safe_claim(args.deny_reason, "deny reason", required=False),
    }
    log = root / "logs" / "knowledge-access.jsonl"
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n")
    append_log(root, {"event": "knowledge_access_log", "mount_id": event["mount_id"], "source_class": args.source_class, "decision": args.decision, "tenant_id": event["tenant_id"], "deployment_id": event["deployment_id"], "user_id": event["user_id"]})
    print(json.dumps(event, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def health(args: argparse.Namespace) -> int:
    root = system_root()
    checks = {
        "root": str(root),
        "agents_registry": (root / "agents.registry.json").exists(),
        "knowledge_registry": (root / "knowledge.registry.json").exists(),
        "identity_access_registry": (root / "identity.access.registry.json").exists(),
        "industry_solutions_registry": (root / "industry-solutions.registry.json").exists(),
        "external_knowledge_sources_registry": (root / "external-knowledge-sources.registry.json").exists(),
        "rules_registry": (root / "rules" / "rules.registry.json").exists(),
        "multimodal_pipeline": (root / "multimodal.pipeline.json").exists(),
        "rag_pipeline": (root / "rag.pipeline.json").exists(),
        "tesseract": bool(shutil.which("tesseract")),
        "pdftotext": bool(shutil.which("pdftotext")),
        "rapidocr_onnxruntime": bool(importlib.util.find_spec("rapidocr_onnxruntime")),
        "pypdf": bool(importlib.util.find_spec("pypdf")),
        "python_docx": bool(importlib.util.find_spec("docx")),
        "sentence_transformers": bool(importlib.util.find_spec("sentence_transformers")),
        "python_docx_builtin": True,
    }
    print(json.dumps(checks, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if all(checks[k] for k in ("agents_registry", "knowledge_registry", "identity_access_registry", "industry_solutions_registry", "external_knowledge_sources_registry", "rules_registry", "multimodal_pipeline")) else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="office-system")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("project-create")
    p.add_argument("--project")
    p.add_argument("--name", required=True)
    p.add_argument("--agents", default="")
    p.add_argument("--methodology-schedule", choices=["manual", "weekly", "monthly", "on_project_close"], default="manual")
    p.set_defaults(func=create_project)

    p = sub.add_parser("knowledge-add")
    p.add_argument("--scope", choices=["company", "project"], required=True)
    p.add_argument("--project")
    p.add_argument("--file", required=True)
    p.add_argument("--title")
    p.add_argument("--kind", choices=["text", "word", "pdf", "image", "binary"])
    p.add_argument("--notes")
    p.add_argument("--approve", action="store_true")
    p.set_defaults(func=add_file_entry)

    p = sub.add_parser("knowledge-add-text")
    p.add_argument("--scope", choices=["company", "project"], required=True)
    p.add_argument("--project")
    p.add_argument("--title", required=True)
    p.add_argument("--body")
    p.add_argument("--approve", action="store_true")
    p.set_defaults(func=add_text_entry)

    p = sub.add_parser("rule-add")
    p.add_argument("--scope", choices=["global", "agent", "project"], required=True)
    p.add_argument("--project")
    p.add_argument("--agent")
    p.add_argument("--title", required=True)
    p.add_argument("--body")
    p.set_defaults(func=add_rule)

    p = sub.add_parser("context")
    p.add_argument("--project")
    p.add_argument("--agent")
    p.set_defaults(func=context)

    p = sub.add_parser("identity-context")
    p.add_argument("--tenant", required=True)
    p.add_argument("--deployment", required=True)
    p.add_argument("--user", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--project")
    p.add_argument("--agent")
    p.add_argument("--workflow-run")
    p.add_argument("--session")
    p.set_defaults(func=identity_context)

    p = sub.add_parser("methodology-draft")
    p.add_argument("--project", required=True)
    p.add_argument("--period", default="manual")
    p.set_defaults(func=methodology_draft)

    p = sub.add_parser("methodology-approve")
    p.add_argument("--project", required=True)
    p.add_argument("--draft", required=True)
    p.add_argument("--confirmed", action="store_true")
    p.set_defaults(func=methodology_approve)

    p = sub.add_parser("relay-add")
    p.add_argument("--project", required=True)
    p.add_argument("--subproject")
    p.add_argument("--agent", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--body")
    p.add_argument("--status", choices=["active", "blocked", "done", "superseded"], default="active")
    p.add_argument("--source-ref", action="append")
    p.add_argument("--next-action", action="append")
    p.set_defaults(func=relay_add)

    p = sub.add_parser("agent-request-submit")
    p.add_argument("--title", required=True)
    p.add_argument("--body")
    p.add_argument("--project")
    p.add_argument("--requested-by")
    p.add_argument("--priority", choices=["low", "normal", "high", "urgent"], default="normal")
    p.add_argument("--confirmed", action="store_true")
    p.add_argument("--timeout", type=int, default=30)
    p.set_defaults(func=agent_request_submit)

    p = sub.add_parser("agent-request-status")
    p.add_argument("--request-id", required=True)
    p.set_defaults(func=agent_request_status)

    p = sub.add_parser("agent-request-set-status")
    p.add_argument("--request-id", required=True)
    p.add_argument(
        "--status",
        choices=["received", "in_progress", "completed", "downloaded_deployed", "pending_user_confirmation", "needs_tuning", "paused_by_user", "needs_more_info", "rejected"],
        required=True,
    )
    p.add_argument("--message")
    p.add_argument("--package")
    p.set_defaults(func=agent_request_set_status)

    p = sub.add_parser("agent-improvement-draft")
    p.add_argument("--agent", required=True)
    p.add_argument("--kind", choices=["soul", "workflow"], required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--body")
    p.add_argument("--project")
    p.set_defaults(func=agent_improvement_draft)

    p = sub.add_parser("agent-improvement-approve")
    p.add_argument("--agent", required=True)
    p.add_argument("--draft", required=True)
    p.add_argument("--confirmed", action="store_true")
    p.set_defaults(func=agent_improvement_approve)

    p = sub.add_parser("agent-plugin-report")
    p.add_argument("--package", required=True)
    p.add_argument("--project")
    p.add_argument("--request-id")
    p.set_defaults(func=agent_plugin_report)

    p = sub.add_parser("agent-plugin-decision")
    p.add_argument("--report-id", required=True)
    p.add_argument("--decision", choices=["confirm", "tune", "pause"], required=True)
    p.add_argument("--message")
    p.set_defaults(func=agent_plugin_decision)

    p = sub.add_parser("agent-plugin-activate")
    p.add_argument("--package", required=True)
    p.add_argument("--project")
    p.add_argument("--report")
    p.add_argument("--request-id")
    p.add_argument("--confirmed", action="store_true")
    p.add_argument("--replace-agent", action="store_true")
    p.add_argument("--replace-profile", action="store_true")
    p.set_defaults(func=agent_plugin_activate)

    p = sub.add_parser("rag-index")
    p.add_argument("--scope", choices=["company", "project"], required=True)
    p.add_argument("--project")
    p.add_argument("--mode", choices=["auto", "lexical", "embedding"], default="auto")
    p.add_argument("--embedding-model", default="BAAI/bge-small-zh-v1.5")
    p.add_argument("--chunk-chars", type=int, default=1200)
    p.add_argument("--chunk-overlap", type=int, default=180)
    p.set_defaults(func=rag_index)

    p = sub.add_parser("rag-search")
    p.add_argument("--scope", choices=["company", "project"], required=True)
    p.add_argument("--project")
    p.add_argument("--query", required=True)
    p.add_argument("--limit", type=int, default=5)
    p.add_argument("--embedding-model", default="BAAI/bge-small-zh-v1.5")
    p.set_defaults(func=rag_search)

    p = sub.add_parser("knowledge-source-mount")
    p.add_argument("--source-class", choices=["customer_owned_external_kb", "provider_sold_industry_kb"], required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--display-name")
    p.add_argument("--provider", default="")
    p.add_argument("--tenant", required=True)
    p.add_argument("--deployment", required=True)
    p.add_argument("--created-by", required=True)
    p.add_argument("--mount-target", choices=["company_knowledge", "project_knowledge", "agent_specialist_context", "licensed_company_reference", "licensed_project_reference", "licensed_agent_reference"], required=True)
    p.add_argument("--project")
    p.add_argument("--agent")
    p.add_argument("--entitlement")
    p.add_argument("--license-sku")
    p.add_argument("--sync-mode", choices=["metadata_only", "selected_items", "excerpt_index", "embedding_index", "full_customer_owned_sync", "controlled_remote_retrieval"], default="excerpt_index")
    p.add_argument("--allowed-user", action="append")
    p.add_argument("--allowed-role", action="append")
    p.add_argument("--mount-id")
    p.add_argument("--replace", action="store_true")
    p.set_defaults(func=knowledge_source_mount)

    p = sub.add_parser("knowledge-access-log")
    p.add_argument("--tenant", required=True)
    p.add_argument("--deployment", required=True)
    p.add_argument("--user", required=True)
    p.add_argument("--role", required=True)
    p.add_argument("--project")
    p.add_argument("--agent")
    p.add_argument("--workflow-run")
    p.add_argument("--source-class", choices=["customer_owned_external_kb", "provider_sold_industry_kb"], required=True)
    p.add_argument("--source-id", required=True)
    p.add_argument("--mount-id", required=True)
    p.add_argument("--knowledge-pack")
    p.add_argument("--entitlement")
    p.add_argument("--query")
    p.add_argument("--result-source-id", action="append")
    p.add_argument("--snippet-count", type=int, default=0)
    p.add_argument("--decision", choices=["allow", "deny"], required=True)
    p.add_argument("--deny-reason")
    p.set_defaults(func=knowledge_access_log)

    p = sub.add_parser("telemetry-status")
    p.set_defaults(func=telemetry_status)

    p = sub.add_parser("telemetry-export")
    p.set_defaults(func=telemetry_export)

    p = sub.add_parser("telemetry-send")
    p.add_argument("--bundle", required=True)
    p.add_argument("--confirmed", action="store_true")
    p.add_argument("--timeout", type=int, default=30)
    p.set_defaults(func=telemetry_send)

    p = sub.add_parser("health")
    p.set_defaults(func=health)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
