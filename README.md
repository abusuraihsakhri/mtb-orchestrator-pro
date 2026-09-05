# Mtb Orchestrator Pro

> **Domain:** Antimicrobial Stewardship & Microbiology  
> **Reference Guidelines & Standards:** `CLSI M100, EUCAST & CDC NHSN Clinical Standards`

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

**Mtb Orchestrator Pro** is an advanced multi-agent analytical platform for clinical decision support in antimicrobial stewardship and microbiology. It evaluates laboratory measurements against established clinical guidelines (CLSI M100, EUCAST, CDC NHSN) and generates prioritized alerts with actionable remediation steps.

The system processes tasks through specialized worker agents, each evaluating different aspects of the input data, and produces a consensus dossier with an HMAC-signed audit trail.

---

## 🚀 Installation

### Prerequisites
- Python 3.9 or higher
- pip (Python package manager)

### Setup
```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/mtb-orchestrator-pro.git
cd mtb-orchestrator-pro

# Create a virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Optional: Install FastAPI/uvicorn for REST API server
pip install fastapi uvicorn
```

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Specialized Worker Agents

- **`InvariantQCWorker`** — Primary mathematical & protocol boundary auditor. Triggers when primary metric exceeds 25.0.
- **`SafetyEscalationWorker`** — Safety boundary & emergency interlock worker. Triggers on critical flags or secondary metric > 12.0.
- **`ProtocolConformanceWorker`** — Spec conformance & discordance checker. Triggers on anomaly keywords in status descriptors.

### 🔐 Security & Audit

- **`PHIGuard`** — Zero-PHI outbound interceptor blocking SSNs, MRNs, phone numbers, emails, and patient names.
- **`AuditTrail`** — Tamper-evident HMAC-SHA256 chained audit logs with cryptographic signature verification.

### 🧠 Reasoning & Learning

- **`LLMFactory`** — Air-gapped LLM adapter supporting mock, Ollama, Claude, and OpenAI providers.
- **`ActiveLearningEngine`** — Bayesian calibration tracker updating worker reliability weights.

---

## 💻 CLI Quickstart & Usage

### 1. Run Single Task Evaluation
```bash
python cli.py audit --task-id TASK-001 --target SPECIMEN-01 --primary 28.5 --secondary 14.2 --critical --status DISCORDANT
```

### 2. Query Supervisory Chat
```bash
python cli.py chat "What is the system status?"
```

### 3. Batch Process CSV Records
```bash
python cli.py batch -i sample.csv -o results.csv
```

### 4. Verify Audit Trail Integrity
```bash
python cli.py verify-audit
```

### 5. Launch REST API Server
```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

### CLI Commands

| Command | Description | Key Arguments |
|:--------|:------------|:--------------|
| `audit` | Run single task evaluation | `--task-id`, `--target`, `--primary`, `--secondary`, `--critical`, `--status` |
| `chat` | Query supervisory assistant | `query` (positional) |
| `batch` | Batch process CSV file | `-i` (input), `-o` (output) |
| `verify-audit` | Verify HMAC audit integrity | — |
| `serve` | Launch FastAPI server | `--host`, `--port` |

### Input Data Schema (CSV Batch)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `task_id` | Unique task identifier | Required |
| `target_identifier` | Specimen or target key | Required |
| `primary_metric` | Primary measurement value | Required |
| `secondary_metric` | Secondary measurement value | Optional (default: 0.0) |
| `is_critical_flag` | Emergency escalation flag | Optional (default: false) |
| `status_descriptor` | Status code or phenotype | Optional (default: "NOMINAL") |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Regex-based inspection blocking SSNs, MRNs, phone numbers, emails, DOB, and patient identifiers from outbound data.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs with signature verification for every evaluation.
* **Input Validation:** Pydantic models with bounds checking, finite number validation, and length constraints.
* **Path Traversal Protection:** Batch output validated against allowed directories.
* **Secure Defaults:** Random audit key generation when `AUDIT_SECRET_KEY` is not set (with warning).

### Environment Variables

| Variable | Description | Default |
|:---------|:------------|:--------|
| `AUDIT_SECRET_KEY` | Secret key for HMAC audit trail signing | Random (session-only) |

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Run with coverage:

```bash
pytest -v --cov=agents --cov=mtb_orchestrator_pro
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py 1000
```

---

## 🐳 Container Deployment

```bash
docker build -t mtb-orchestrator-pro .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key mtb-orchestrator-pro
```

---

## 📁 Project Structure

```
mtb-orchestrator-pro/
├── agents/                  # Core agent package
│   ├── base.py             # PHI guard, audit trail, security
│   ├── models.py           # Pydantic data models
│   ├── workers.py          # Specialized worker agents
│   ├── supervisor.py       # Supervisor orchestrator
│   ├── api.py              # FastAPI REST endpoints
│   ├── llm_factory.py      # LLM provider factory
│   ├── metrics.py          # Prometheus metrics
│   ├── streamer.py         # WebSocket telemetry
│   └── learning.py         # Bayesian calibration engine
├── mtb_orchestrator_pro/    # Alternative package (Precision Oncology)
├── tests/                   # Test suite
├── cli.py                   # Command-line interface
├── simulator.py             # Load testing simulator
├── enrichment.py            # Domain enrichment engines
├── pyproject.toml           # Project configuration
├── Dockerfile               # Container definition
└── README.md                # This file
```
