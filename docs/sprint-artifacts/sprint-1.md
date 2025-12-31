# Sprint 1: Foundation & Schema Contract

**Sprint Duration:** 2 weeks  
**Start Date:** 2025-01-02  
**End Date:** 2025-01-15  
**Developer:** Jean (Solo)

---

## Sprint Goal

> Establish GCP infrastructure foundation, enable local development workflow, and freeze the inter-agent communication contract to de-risk all future development.

---

## Sprint Backlog

| ID | Story | Status | Est. Days | Actual |
|:---|:------|:-------|:----------|:-------|
| 1.1 | Project Init & Terraform Setup | ✅ Done | 3-4 | 1 |
| 1.2 | Local Dev Environment with Gemini | 🔲 Not Started | 2-3 | — |
| 4.1 | A2A Protocol Definition | 🔲 Not Started | 2-3 | — |

**Status Legend:** 🔲 Not Started | 🔄 In Progress | ✅ Done | ⛔ Blocked

---

## Story Details

### Story 1.1: Project Initialization & Terraform Setup

**As a** Developer,  
**I want to** initialize the project repository with Terraform and ADK structures,  
**So that** I have a consistent foundation for infrastructure and agent development.

#### Acceptance Criteria
- [ ] GCP Project created and billing enabled
- [ ] `infrastructure/terraform` directory with `main.tf` exists
- [ ] GCS backend configured for Terraform state
- [ ] GKE Autopilot cluster resource defined (not deployed yet)
- [ ] `agents/ingestion-agent` directory created via `adk init`
- [ ] `agents/database-agent` directory created via `adk init`
- [ ] `docker-compose.yml` for local orchestration exists

#### Tasks
- [ ] **1.1.1** Create GCP Project in Console
- [ ] **1.1.2** Enable billing and required APIs (Vertex AI, GKE, Firestore, Cloud Storage)
- [ ] **1.1.3** Create GCS bucket for Terraform state
- [ ] **1.1.4** Initialize Terraform with GCS backend
- [ ] **1.1.5** Define GKE Autopilot cluster resource in `main.tf`
- [ ] **1.1.6** Run `adk init` for ingestion-agent
- [ ] **1.1.7** Run `adk init` for database-agent
- [ ] **1.1.8** Create base `docker-compose.yml`

#### Technical Notes
- Terraform version: 1.5+
- Use GCS backend with state locking
- GKE Autopilot reduces ops overhead for solo dev

---

### Story 1.2: Local Development Environment with Gemini

**As a** Developer,  
**I want to** run the agents locally using Docker Compose and connect them to Gemini API,  
**So that** I can test agent logic without deploying to GCP.

#### Acceptance Criteria
- [ ] Gemini API key configured as environment variable
- [ ] `docker-compose up` starts both agents successfully
- [ ] Ingestion Agent can make a "Hello World" call to Gemini Flash
- [ ] Logs appear in console output

#### Tasks
- [ ] **1.2.1** Generate Gemini API key in GCP Console
- [ ] **1.2.2** Create `.env.example` with required variables
- [ ] **1.2.3** Configure Dockerfiles for both agents
- [ ] **1.2.4** Update `docker-compose.yml` with API key mounts
- [ ] **1.2.5** Configure ADK for local A2A discovery mode
- [ ] **1.2.6** Implement "Hello Gemini" test endpoint in ingestion-agent
- [ ] **1.2.7** Verify end-to-end local startup

#### Technical Notes
- Mount API keys via environment variables (never commit `.env`)
- ADK local network discovery may need explicit port mapping

---

### Story 4.1: A2A Protocol Definition

**As a** Developer,  
**I want to** define the Protobuf/JSON schema for `StoreKnowledge` messages,  
**So that** the Ingestion and Database agents communicate with a strict contract.

#### Acceptance Criteria
- [ ] `shared/schemas/` directory exists
- [ ] `StoreKnowledgeRequest` schema defined (Pydantic or Protobuf)
- [ ] Schema includes: `chunk_text`, `global_context`, `visuals[]`, `metadata`
- [ ] Both agents can import and validate against this schema
- [ ] Schema version documented

#### Tasks
- [ ] **4.1.1** Create `shared/schemas/` directory structure
- [ ] **4.1.2** Review PRD JSON Schema draft for field requirements
- [ ] **4.1.3** Define `StoreKnowledgeRequest` Pydantic model
- [ ] **4.1.4** Define `StoreKnowledgeResponse` Pydantic model
- [ ] **4.1.5** Add schema validation utilities
- [ ] **4.1.6** Import schema in ingestion-agent (verify)
- [ ] **4.1.7** Import schema in database-agent (verify)
- [ ] **4.1.8** Document schema in `shared/schemas/README.md`

#### Technical Notes
- Pydantic preferred over Protobuf for Python-native validation
- Consider using `pydantic-settings` for config validation too
- Version the schema (v1) to allow future evolution

---

## Definition of Done (Sprint Level)

- [ ] All acceptance criteria for stories 1.1, 1.2, 4.1 met
- [ ] `docker-compose up` runs without errors
- [ ] Both agents start and can reach Gemini API
- [ ] Schema is importable by both agents
- [ ] Code committed and pushed to main branch
- [ ] README updated with local dev setup instructions

---

## Dependencies & Blockers

| Item | Type | Status | Notes |
|:-----|:-----|:-------|:------|
| GCP Account | Dependency | 🔲 Needed | Required for Story 1.1 |
| Billing enabled | Dependency | 🔲 Needed | Required for API access |
| Gemini API enabled | Dependency | 🔲 Needed | Required for Story 1.2 |

---

## Daily Log

### Day 1 (2025-01-02)
- [ ] Tasks completed:
- [ ] Blockers:
- [ ] Notes:

### Day 2 (2025-01-03)
- [ ] Tasks completed:
- [ ] Blockers:
- [ ] Notes:

### Day 3 (2025-01-06)
- [ ] Tasks completed:
- [ ] Blockers:
- [ ] Notes:

### Day 4 (2025-01-07)
- [ ] Tasks completed:
- [ ] Blockers:
- [ ] Notes:

### Day 5 (2025-01-08)
- [ ] Tasks completed:
- [ ] Blockers:
- [ ] Notes:

### Day 6 (2025-01-09)
- [ ] Tasks completed:
- [ ] Blockers:
- [ ] Notes:

### Day 7 (2025-01-10)
- [ ] Tasks completed:
- [ ] Blockers:
- [ ] Notes:

### Day 8 (2025-01-13)
- [ ] Tasks completed:
- [ ] Blockers:
- [ ] Notes:

### Day 9 (2025-01-14)
- [ ] Tasks completed:
- [ ] Blockers:
- [ ] Notes:

### Day 10 (2025-01-15)
- [ ] Tasks completed:
- [ ] Blockers:
- [ ] Notes:

---

## Sprint Retrospective (Complete at Sprint End)

### What went well?
-

### What could be improved?
-

### Action items for next sprint?
-

---

## Sprint Outcome

**Status:** 🔲 In Progress  
**Velocity:** — (first sprint, establishing baseline)  
**Carryover:** —
