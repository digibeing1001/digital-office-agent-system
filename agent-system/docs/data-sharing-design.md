# Enterprise Data Contribution Design

The digital-office system may collect data for future agent training, model
training, and industry knowledge-base construction only through an explicit
data contribution layer.

## Non-Negotiable Rule

Do not silently collect enterprise data. The tenant administrator must enable
data contribution, configure the server endpoint, review or allow the export
class, and be able to disable it.

The GUI label should be friendly, not alarming:

- `Help us improve the experience`: no-content product telemetry.
- `Industry experience co-building`: anonymized workflow patterns and approved
  methodology summaries.

Do not use misleading labels that hide data contribution. Friendly wording is
fine; deceptive wording is not.

## What To Collect

Collect data that improves the product without exposing raw client material:

- route events: intent label, selected Agent, selected workflow, status
- workflow metrics: duration, retries, failure category, handoff count
- approved methodology summaries
- anonymized project relay patterns
- sanitized examples of prompts and outputs only if explicitly enabled
- source references and quality labels, not raw documents by default

## What Not To Collect By Default

- raw PDF, Word, image, or project source files
- raw KeyMemory records
- credentials or tokens
- client names, personal identifiers, bank accounts, ID numbers
- unapproved project drafts

## Where Data Comes From

- Project knowledge base: source-backed project facts. Export only approved
  summaries or sanitized snippets.
- Company global knowledge base: approved methodology and reusable knowledge.
  Export only entries marked approved.
- KeyMemory: relay and continuity summaries. Export only relay summaries with
  source refs, not raw memories.

## Transmission Flow

1. GUI admin enables `data-sharing/consent.json`.
2. `office-system telemetry-export` creates a local bundle.
3. GUI shows the bundle to the admin for review.
4. `office-system telemetry-send --bundle <path>` sends it to the configured
   server.
5. A receipt is written under `data-sharing/receipts/`.

This keeps enterprise deployment compatible with law, accounting, and other
sensitive industries.
