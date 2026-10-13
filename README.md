# MTB Orchestrator Pro

A rule-based, multi-worker demonstration of task evaluation, batch processing and in-memory audit logging. The active command-line application and REST API are implemented in Python. A separate static browser preview executes equivalent demonstration rules locally without a backend.

**Clinical limitation:** The primary (>25), secondary (>12), critical-flag and status-keyword triggers are illustrative software rules. They are **not** derived from or validated against CLSI, EUCAST, CDC, AMP/ASCO/CAP or other clinical practice guidelines. Do not use this repository for patient care, microbiology interpretation, molecular tumor boards or trial eligibility decisions.

## Features

- Three deterministic workers for threshold, critical-flag and descriptor checks, with summary dossiers.
- Single-task evaluation and CSV batch processing through the CLI.
- Optional FastAPI endpoints for task evaluation and mock supervisory queries.
- Session-only HMAC-SHA256 audit chain, with integrity checks while the same process remains running.
- Browser-only preview for synthetic single-task inputs, CSV processing, JSON export and CSV export.
- Separate legacy **mtb_orchestrator_pro/** precision-oncology example, kept for compatibility. It does **not** perform real variant annotation, clinical trial matching or drug-interaction checking.

## Use the browser preview

The site files are under **web/**. Serve them locally to load the JavaScript module:

~~~bash
python -m http.server 8080 --directory web
~~~

Open http://localhost:8080/, submit synthetic values, or upload a CSV containing the required columns **task_id,target_identifier,primary_metric** and optionally **secondary_metric,status_descriptor,is_critical_flag**. Processing and downloads take place in your browser. The preview does not call the FastAPI backend, store inputs persistently, contact an LLM or generate HMAC signatures. Batch input is limited to 2 MB and 5,000 data rows. Use a current browser with ES module and File API support.

The GitHub Pages publication workflow is in **.github/workflows/pages.yml**; availability of the published site depends on GitHub Pages being enabled and deployment succeeding.

## Install and run Python

Requires Python 3.10 or later.

~~~bash
git clone https://github.com/abusuraihsakhri/mtb-orchestrator-pro.git
cd mtb-orchestrator-pro
python -m pip install -e ".[server,test]"

mtb-orchestrator-pro audit --task-id TASK-001 --target SPEC-001 --primary 28 --secondary 13 --critical --status DISCORDANT
mtb-orchestrator-pro batch -i sample.csv -o results.csv
mtb-orchestrator-pro chat "status"
mtb-orchestrator-pro serve --host 127.0.0.1 --port 8000
~~~

The REST API provides **GET /health**, **GET /metrics**, **POST /api/audit**, **POST /api/chat** and **GET /api/audit/logs**. Interactive API documentation is served at **/docs** when FastAPI is running. **MTB_API_TOKEN**, when configured, requires an Authorization bearer token header for non-health routes; the audit-log route is **disabled** if that variable is unset.

To run the container, put unique high-entropy values for **AUDIT_SECRET_KEY** and **MTB_API_TOKEN** into your own **.env** file (see **.env.example**), then use **docker compose up --build**. Compose binds port 8000 only to localhost by default. Do not use the sample values or reuse any credential from repository history.

The installed **mtb-orchestrator-oncology** CLI selects the separate legacy oncology example, which is not the same workflow as **mtb-orchestrator-pro**. Its CSV example is **sample_oncology.csv**.

## Audit and privacy limitations

The CLI and API HMAC chain is **memory-only**: it does not survive a process restart, and hashes from the browser preview are deliberately absent. **mtb-orchestrator-pro verify-audit** checks the current process's blocks; it reports no blocks when invoked separately after a previous CLI command. For durable audit trails, key lifecycle, retention and external verification, additional engineering is required.

The application checks for certain direct identifiers with regular expressions. This is **not complete de-identification** or a HIPAA Safe Harbor guarantee. Enter synthetic data only. The HTTP service is intended for local demonstrations; do not expose it publicly without appropriate infrastructure controls. The supervisory query uses a deterministic mock response, not a hosted or local language model.

## Tests

~~~bash
python -m pytest -q
python -m compileall -q agents mtb_orchestrator_pro cli.py enrichment.py simulator.py
node --test tests/test_web.mjs
~~~

The Python suite includes worker, validation, API authentication, audit-integrity and batch tests. The JavaScript suite covers browser rule thresholds, validation, CSV parsing and export escaping. GitHub Actions runs the Python suite on Python 3.10, 3.11 and 3.12 and JavaScript tests using Node 22.

## Technology and license

Python, Pydantic 2, optional FastAPI/Uvicorn; dependency-free browser JavaScript (ES modules), HTML and CSS. Licensed under [MIT](LICENSE).
