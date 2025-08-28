# Architecture

This demo implements a minimal Agentic RAG pipeline.

![Architecture](images/architecture.png)

- **Planner**: regex-based, detects invoice IDs, selects steps.
- **Retriever**: loads CSVs in `data/`, captures row offsets for provenance.
- **Web search**: DuckDuckGo for reference context.
- **Verifier**: applies simple rules for price, total, and receipt coverage.
- **Synthesizer**: OpenAI (configurable via env vars) generates final explanation; fallback template if key missing.
- **Audit**: JSONL log for every step.
- **Follow-up**: supports an "Approve it" mock requiring human confirmation.