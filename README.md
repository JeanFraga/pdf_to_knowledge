# pdf_to_knowledge

Agentic PDF-to-knowledge pipeline using Google ADK on GCP.

## Quick Start

### Prerequisites
- Python 3.12+ (ADK requires ≥3.10)
- Docker & Docker Compose
- Google Cloud SDK (`gcloud`)
- Terraform 1.5+

### 1. Bootstrap GCP Infrastructure

```bash
# Login to GCP
gcloud auth login
gcloud auth application-default login

# Run bootstrap script (idempotent)
./infrastructure/setup.sh
```

### 2. Initialize Terraform

```bash
cd infrastructure/terraform
terraform init
terraform plan  # Review changes
# terraform apply  # Deploy (creates GKE cluster - costs $$$)
```

### 3. Local Development

```bash
# Copy environment template
cp .env.example .env

# Add your Gemini API key to .env
# Get one at: https://aistudio.google.com/apikey

# Start agents locally
docker-compose up --build
```

## Project Structure

```
pdf_to_knowledge/
├── infrastructure/
│   ├── setup.sh              # Bootstrap script
│   └── terraform/            # IaC definitions
├── agents/
│   ├── ingestion-agent/      # PDF parsing & chunking
│   └── database-agent/       # Storage & retrieval
├── shared/
│   └── schemas/              # A2A message contracts
├── docs/                     # Documentation
└── docker-compose.yml        # Local orchestration
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for full system design.

## Sprint Status

See [docs/sprint-artifacts/sprint-1.md](docs/sprint-artifacts/sprint-1.md) for current progress.
