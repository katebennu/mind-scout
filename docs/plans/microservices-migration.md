# Plan: Mind Scout Microservices Migration

## Overview
Migrate Mind Scout from a monolithic architecture to 5-6 microservices, deployable to GKE.

**Scope:** MVP deployment (working K8s manifests, basic GKE deployment)
**Database:** Shared PostgreSQL (Cloud SQL)
**Users:** Single user (no auth required)

---

## Current Architecture

```
├── mindscout/           # Core Python library
│   ├── database.py      # SQLite + SQLAlchemy models
│   ├── fetchers/        # arXiv, Semantic Scholar, RSS
│   ├── processors/      # LLM content processing
│   ├── vectorstore.py   # ChromaDB embeddings
│   ├── recommender.py   # Recommendation engine
│   └── profile.py       # User profile
├── backend/             # FastAPI monolith (all endpoints)
├── frontend/            # React + Material UI
└── mcp-server/          # Claude Desktop integration
```

---

## Target Architecture: 5 Microservices

```
┌─────────────────────────────────────────────────────────────────┐
│                         FRONTEND                                 │
│                    (React + Nginx container)                     │
└─────────────────────────────────┬───────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                       API GATEWAY                                │
│              (FastAPI - routing, aggregation)                    │
└──────┬──────────┬──────────┬──────────┬──────────┬──────────────┘
       │          │          │          │          │
┌──────▼───┐ ┌────▼────┐ ┌───▼────┐ ┌───▼────┐ ┌───▼────┐
│ ARTICLES │ │ FETCHER │ │PROCESS │ │ SEARCH │ │ USER   │
│ SERVICE  │ │ SERVICE │ │SERVICE │ │SERVICE │ │SERVICE │
└────┬─────┘ └────┬────┘ └───┬────┘ └───┬────┘ └───┬────┘
     │            │          │          │          │
     └────────────┴──────────┴────┬─────┴──────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │   SHARED POSTGRESQL       │
                    │      (Cloud SQL)          │
                    └───────────────────────────┘
```

---

## Service Breakdown

### 1. Frontend Service
**What:** React app served via Nginx
**Port:** 80
**Source:** `frontend/` → containerized with Nginx
**Changes:**
- Add `frontend/Dockerfile` (multi-stage build)
- Add `frontend/nginx.conf` for SPA routing
- Update API base URL to use K8s service name

### 2. API Gateway
**What:** FastAPI routing layer, request aggregation
**Port:** 8000
**Source:** New `services/gateway/`
**Responsibilities:**
- Route requests to appropriate services
- Aggregate responses when needed (e.g., article + recommendations)
- Health checks for all services
**Endpoints:**
- All `/api/*` routes (proxied to services)
- `/health` - gateway + downstream health

### 3. Articles Service
**What:** Article CRUD, reading history, ratings, notifications
**Port:** 8001
**Source:** New `services/articles/`
**Tables owned:** `articles`, `notifications`
**Endpoints:**
- `GET/POST /articles` - list, create
- `GET/PUT /articles/{id}` - get, update (read/rate)
- `GET /articles/sources` - distinct sources
- `GET/POST/DELETE /notifications` - notification management

### 4. Fetcher Service
**What:** Content discovery from external sources
**Port:** 8002
**Source:** New `services/fetcher/`
**From:** `mindscout/fetchers/`, `backend/api/fetchers.py`, `subscriptions.py`
**Tables owned:** `rss_feeds`
**External APIs:** arXiv, Semantic Scholar, RSS feeds
**Endpoints:**
- `POST /fetch/arxiv` - fetch arXiv papers
- `POST /fetch/semanticscholar` - fetch SS papers
- `GET/POST/DELETE /subscriptions` - RSS management
- `POST /subscriptions/{id}/refresh` - refresh feed
- `POST /subscriptions/refresh-all` - refresh all active feeds

### 5. Processor Service
**What:** LLM-powered content processing
**Port:** 8003
**Source:** New `services/processor/`
**From:** `mindscout/processors/`
**External APIs:** Anthropic Claude
**Endpoints:**
- `POST /process` - process unprocessed articles
- `POST /process/{id}` - process single article

### 6. Search & Recommendations Service
**What:** Vector search, embeddings, recommendations
**Port:** 8004
**Source:** New `services/search/`
**From:** `mindscout/vectorstore.py`, `recommender.py`, `profile.py`
**Tables owned:** `user_profile`
**Storage:** ChromaDB (persistent volume)
**Endpoints:**
- `GET /search?q=` - semantic search
- `GET /recommendations` - personalized recommendations
- `GET/PUT /profile` - user profile management
- `GET /profile/stats` - reading statistics

---

## New Directory Structure

```
mind-scout/
├── services/
│   ├── gateway/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── routes/
│   ├── articles/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── models.py
│   │   ├── requirements.txt
│   │   └── api/
│   ├── fetcher/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── fetchers/        # moved from mindscout/
│   ├── processor/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   ├── requirements.txt
│   │   └── llm.py           # moved from mindscout/
│   └── search/
│       ├── Dockerfile
│       ├── main.py
│       ├── requirements.txt
│       ├── vectorstore.py   # moved from mindscout/
│       └── recommender.py   # moved from mindscout/
├── shared/
│   ├── database.py          # SQLAlchemy models (shared)
│   └── config.py            # shared configuration
├── k8s/
│   ├── namespace.yaml
│   ├── configmap.yaml
│   ├── secrets.yaml
│   ├── frontend/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── gateway/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── articles/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── fetcher/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── cronjob.yaml      # Scheduled fetch job
│   ├── processor/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   ├── search/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── pvc.yaml         # ChromaDB storage
│   └── ingress.yaml
├── docker-compose.yaml      # local development
├── skaffold.yaml           # optional: dev workflow
├── frontend/               # existing, add Dockerfile
└── (legacy mindscout/, backend/ - keep for reference)
```

---

## Database Migration: SQLite → PostgreSQL

### Changes Required:
1. Update `DATABASE_URL` environment variable
2. SQLAlchemy connection string: `postgresql://user:pass@host:5432/mindscout`
3. Update models for PostgreSQL compatibility (minimal changes)
4. Create migration script for existing data (if any)

### Shared Models (`shared/database.py`):
```python
# All services import from here
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class Article(Base): ...
class UserProfile(Base): ...
class RSSFeed(Base): ...
class Notification(Base): ...
```

---

## Kubernetes Resources

### Per Service:
- **Deployment**: 1-2 replicas (MVP)
- **Service**: ClusterIP (internal), LoadBalancer for gateway
- **ConfigMap**: Non-sensitive config
- **Secret**: API keys (ANTHROPIC_API_KEY)

### Shared:
- **Namespace**: `mindscout`
- **Ingress**: Route external traffic to gateway
- **PersistentVolumeClaim**: ChromaDB data (search service)
- **CronJob**: Scheduled fetching (RSS refresh + processing)

### Scheduled Fetching (CronJob)
A Kubernetes CronJob handles automated content discovery:

```yaml
# k8s/fetcher/cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: scheduled-fetch
  namespace: mindscout
spec:
  schedule: "0 */6 * * *"  # Every 6 hours
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: fetcher
            image: curlimages/curl
            command:
            - /bin/sh
            - -c
            - |
              # Refresh all RSS subscriptions
              curl -X POST http://fetcher-service:8002/subscriptions/refresh-all
              # Fetch from arXiv default categories
              curl -X POST http://fetcher-service:8002/fetch/arxiv
              # Trigger processing for new articles
              curl -X POST http://processor-service:8003/process
          restartPolicy: OnFailure
```

**Schedule options:**
- `"0 */6 * * *"` - Every 6 hours (default)
- `"0 8,20 * * *"` - Twice daily at 8am and 8pm
- `"0 * * * *"` - Every hour

### GKE Specific:
- **Cloud SQL**: Managed PostgreSQL
- **Cloud SQL Auth Proxy**: Secure DB connection
- **Workload Identity**: Service account binding

---

## Implementation Phases

### Phase 1: Dockerize Monolith
- [ ] Add `Dockerfile` to existing `backend/`
- [ ] Add `Dockerfile` to `frontend/` (multi-stage with Nginx)
- [ ] Create `docker-compose.yaml` with PostgreSQL
- [ ] Migrate database code from SQLite to PostgreSQL
- [ ] Test locally with Docker Compose

### Phase 2: Extract Services
- [ ] Create `services/` directory structure
- [ ] Extract Articles Service (simplest, good first service)
- [ ] Extract Fetcher Service
- [ ] Extract Processor Service
- [ ] Extract Search/Recommendations Service
- [ ] Create API Gateway with routing
- [ ] Update frontend to use gateway

### Phase 3: Kubernetes Manifests
- [ ] Create K8s namespace and base configs
- [ ] Create deployments and services for each microservice
- [ ] Create ConfigMaps and Secrets
- [ ] Create PVC for ChromaDB
- [ ] Create CronJob for scheduled fetching
- [ ] Create Ingress for external access
- [ ] Test with Minikube/Kind locally

### Phase 4: GKE Deployment
- [ ] Set up GKE cluster
- [ ] Set up Cloud SQL PostgreSQL instance
- [ ] Configure Cloud SQL Auth Proxy
- [ ] Deploy all services to GKE
- [ ] Configure Ingress/Load Balancer
- [ ] Verify end-to-end functionality

---

## Cost Estimate (GKE)

### Monthly Infrastructure Costs (MVP)

| Resource | Spec | Monthly Cost |
|----------|------|--------------|
| **GKE Cluster** | Autopilot (pay per pod) | ~$0 |
| **Compute (Pods)** | | |
| - Frontend | 0.25 vCPU, 256MB | ~$3 |
| - Gateway | 0.25 vCPU, 256MB | ~$3 |
| - Articles | 0.25 vCPU, 256MB | ~$3 |
| - Fetcher | 0.25 vCPU, 256MB | ~$3 |
| - Processor | 0.5 vCPU, 512MB | ~$6 |
| - Search | 0.5 vCPU, 1GB | ~$8 |
| **Cloud SQL (PostgreSQL)** | db-f1-micro (shared) | ~$9 |
| **Persistent Disk** | 10GB SSD (ChromaDB) | ~$2 |
| **Load Balancer** | 1 forwarding rule | ~$18 |
| **Egress** | Minimal (<1GB) | ~$0 |
| **Total Infrastructure** | | **~$55/month** |

### External API Costs

| Service | Usage | Monthly Cost |
|---------|-------|--------------|
| **Anthropic (Claude Haiku)** | ~1000 articles processed | ~$0.12 |
| **arXiv API** | Free | $0 |
| **Semantic Scholar API** | Free | $0 |
| **Total APIs** | | **~$1/month** |

### Grand Total: ~$55-60/month

### Cost Optimization Options

**Reduce to ~$30-35/month:**
- Use Preemptible/Spot VMs for non-critical services (-60% compute)
- Use Cloud Run instead of GKE (pay only when requests come in)
- Use smaller Cloud SQL instance

**Reduce to ~$15-20/month:**
- Single VM approach: Run everything on one e2-small ($6/mo) with Docker Compose
- Use SQLite instead of Cloud SQL
- Skip the load balancer (use VM's IP directly or Cloudflare tunnel)

**Recommendation:** For a single-user MVP, consider starting with Cloud Run (~$5-15/month) or a single e2-small VM (~$15/month). Migrate to full GKE when scaling to multiple users.

---

## Key Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Service communication failures | Health checks, retries, circuit breakers (future) |
| Database connection limits | Connection pooling, Cloud SQL proxy |
| ChromaDB data persistence | PVC with appropriate storage class |
| API key exposure | K8s Secrets, Workload Identity |
| Cold start latency | Keep replicas warm, optimize imports |

---

## Files to Create (Summary)

**New files:** ~40 files
- 5 service directories with Dockerfile, main.py, requirements.txt
- 1 gateway service
- 1 shared library
- ~15 K8s manifest files
- docker-compose.yaml
- Frontend Dockerfile + nginx.conf

**Files to modify:**
- `frontend/src/` - API base URL configuration
- Database connection strings

**Files to deprecate (keep for reference):**
- `mindscout/` - logic moved to services
- `backend/` - replaced by gateway + services
