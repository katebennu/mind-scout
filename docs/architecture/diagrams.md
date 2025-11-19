# MindScout Architecture Diagrams

Visual architecture diagrams using Mermaid (renders on GitHub, GitLab, and many markdown viewers).

## System Overview

```mermaid
graph TB
    subgraph "User Interfaces"
        WEB[Web UI<br/>React + Vite<br/>:3000]
        CLI[CLI Tools<br/>mindscout commands]
        CLAUDE[Claude Desktop<br/>+ MCP Integration]
    end

    subgraph "Application Layer"
        API[FastAPI Backend<br/>REST API<br/>:8000]
        MCP[MCP Server<br/>9 Tools<br/>stdio protocol]
    end

    subgraph "Core Services"
        DB[(SQLite Database<br/>Articles & Profile)]
        VS[ChromaDB<br/>Vector Store<br/>Embeddings]
        REC[Recommendation<br/>Engine]
        FETCH[Fetchers<br/>arXiv + S2]
    end

    subgraph "External Services"
        ARXIV[arXiv API<br/>RSS Feeds]
        S2[Semantic Scholar<br/>Citation Data]
        ANTHROPIC[Anthropic API<br/>Claude LLM]
    end

    WEB -->|HTTP| API
    CLI --> API
    CLI --> DB
    CLAUDE -->|stdio| MCP

    API --> DB
    API --> VS
    API --> REC
    MCP --> DB
    MCP --> VS
    MCP --> REC

    REC --> DB
    REC --> VS
    FETCH --> ARXIV
    FETCH --> S2
    FETCH --> DB

    API --> ANTHROPIC

    style WEB fill:#e1f5ff
    style CLI fill:#e1f5ff
    style CLAUDE fill:#e1f5ff
    style API fill:#fff4e1
    style MCP fill:#fff4e1
    style DB fill:#e8f5e9
    style VS fill:#e8f5e9
    style REC fill:#e8f5e9
    style FETCH fill:#e8f5e9
    style ARXIV fill:#fce4ec
    style S2 fill:#fce4ec
    style ANTHROPIC fill:#fce4ec
```

## Paper Fetching Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI/MCP as CLI/MCP Tool
    participant Fetcher
    participant API as External API
    participant DB as Database
    participant VS as VectorStore

    User->>CLI/MCP: fetch_articles("arxiv")
    CLI/MCP->>Fetcher: initialize ArxivFetcher

    Fetcher->>API: GET RSS feed
    API-->>Fetcher: XML response

    Fetcher->>Fetcher: Parse XML<br/>Extract metadata

    loop For each paper
        Fetcher->>DB: Check if exists (source_id)
        alt Paper is new
            Fetcher->>DB: INSERT article
            Fetcher->>VS: Generate & store embedding
        else Paper exists
            Fetcher->>Fetcher: Skip duplicate
        end
    end

    Fetcher-->>CLI/MCP: Return count (5 new)
    CLI/MCP-->>User: "Fetched 5 new papers"
```

## Semantic Search Flow

```mermaid
flowchart TD
    Start([User Query:<br/>'transformers for NLP']) --> Embed[Generate Query Embedding<br/>sentence-transformers]

    Embed --> Search[ChromaDB Vector Search<br/>Cosine Similarity]

    Search --> Top[Get Top K Results<br/>with similarity scores]

    Top --> Fetch[Fetch Full Articles<br/>from SQLite Database]

    Fetch --> Sort[Sort by Relevance<br/>relevance_score = similarity × 100]

    Sort --> Return([Return Results<br/>with scores])

    style Start fill:#e1f5ff
    style Embed fill:#fff4e1
    style Search fill:#e8f5e9
    style Top fill:#e8f5e9
    style Fetch fill:#fff4e1
    style Sort fill:#fff4e1
    style Return fill:#e1f5ff
```

## Recommendation Engine Flow

```mermaid
graph TD
    A[Get Recommendations Request] --> B[Load User Profile]
    B --> C[Get User Interests]
    B --> D[Get Unread Articles]

    C --> E[Scoring Algorithm]
    D --> E

    E --> F{For Each Article}
    F --> G[Topic Match<br/>+20 per match]
    F --> H[Citation Count<br/>+10 if >100]
    F --> I[Recency<br/>+5 if <30 days]
    F --> J[Source Preference<br/>+5 if preferred]
    F --> K[Semantic Similarity<br/>+15 if >0.7]

    G --> L[Calculate Total Score]
    H --> L
    I --> L
    J --> L
    K --> L

    L --> M{Score >= Threshold?}
    M -->|Yes| N[Add to Results]
    M -->|No| O[Discard]

    N --> P[Sort by Score DESC]
    P --> Q[Take Top N]
    Q --> R[Attach Reasons]
    R --> S([Return Recommendations])

    style A fill:#e1f5ff
    style S fill:#e1f5ff
    style E fill:#fff4e1
    style L fill:#fff4e1
    style P fill:#e8f5e9
```

## MCP Server Integration

```mermaid
sequenceDiagram
    participant User
    participant Claude as Claude Desktop
    participant MCP as MCP Server
    participant DB as Database
    participant VS as VectorStore

    User->>Claude: "Show me recent AI papers"

    Claude->>Claude: Decide to use<br/>search_papers tool

    Claude->>MCP: search_papers(<br/>query="recent AI papers",<br/>limit=10)

    MCP->>VS: semantic_search(query)
    VS-->>MCP: [article_ids + scores]

    MCP->>DB: SELECT articles WHERE id IN (...)
    DB-->>MCP: [article records]

    MCP->>MCP: Format as JSON

    MCP-->>Claude: Return structured data

    Claude->>Claude: Generate natural<br/>language response

    Claude-->>User: "I found 10 recent AI papers:<br/>1. Attention Is All You Need...<br/>2. BERT: Pre-training..."
```

## Database Schema

```mermaid
erDiagram
    ARTICLES {
        int id PK
        string source_id UK
        string source
        string title
        text authors
        text abstract
        string url
        datetime published_date
        datetime fetched_date
        string categories
        int citation_count
        int influential_citations
        boolean is_read
        int rating
        text embedding
        boolean processed
    }

    USER_PROFILE {
        int id PK
        text interests
        string skill_level
        text preferred_sources
        int daily_reading_goal
        datetime created_date
        datetime updated_date
    }

    ARTICLES ||--o{ USER_PROFILE : "personalized for"
```

## API Endpoints Architecture

```mermaid
graph LR
    subgraph "Client Requests"
        C1[GET /api/articles]
        C2[GET /api/articles/:id]
        C3[POST /api/search]
        C4[GET /api/recommendations]
        C5[GET /api/profile]
    end

    subgraph "FastAPI Routes"
        R1[articles.list_articles]
        R2[articles.get_article]
        R3[search.search_articles]
        R4[recommendations.get_recommendations]
        R5[profile.get_profile]
    end

    subgraph "Services"
        DB[(Database)]
        VS[VectorStore]
        REC[RecommendationEngine]
    end

    C1 --> R1 --> DB
    C2 --> R2 --> DB
    C3 --> R3 --> VS --> DB
    C4 --> R4 --> REC --> DB
    C4 --> R4 --> REC --> VS
    C5 --> R5 --> DB

    style C1 fill:#e1f5ff
    style C2 fill:#e1f5ff
    style C3 fill:#e1f5ff
    style C4 fill:#e1f5ff
    style C5 fill:#e1f5ff
    style DB fill:#e8f5e9
    style VS fill:#e8f5e9
    style REC fill:#e8f5e9
```

## MCP Tools Overview

```mermaid
mindmap
    root((MCP Server<br/>9 Tools))
        Search & Discovery
            search_papers
                Semantic search
                Vector similarity
                Top K results
            get_recommendations
                Interest matching
                Citation scoring
                Relevance ranking
        Library Management
            list_articles
                Pagination
                Filtering
                Sorting
            get_article
                By ID
                Full details
        Reading & Tracking
            rate_article
                1-5 stars
                User feedback
            mark_article_read
                Read/unread status
                Progress tracking
        Profile & Settings
            get_profile
                View interests
                Reading stats
                Library metrics
            update_interests
                Topic preferences
                Skill level
        Data Fetching
            fetch_articles
                arXiv integration
                Semantic Scholar
                Auto-save to DB
```

## GCP Deployment Architecture

```mermaid
graph TB
    subgraph "Users"
        U1[Web Browser]
        U2[Claude Desktop]
    end

    subgraph "Google Cloud Platform"
        subgraph "Frontend"
            CDN[Cloud CDN<br/>Global Edge Cache]
            STORAGE[Cloud Storage<br/>Static Files]
        end

        subgraph "Backend"
            LB[Load Balancer<br/>HTTPS]
            CR[Cloud Run<br/>Backend API<br/>Auto-scaling 0-10]
        end

        subgraph "Data Layer"
            SQL[(Cloud SQL<br/>PostgreSQL 15<br/>10GB SSD)]
            SECRETS[Secret Manager<br/>API Keys, Passwords]
        end

        subgraph "Automation"
            BUILD[Cloud Build<br/>CI/CD Pipeline]
            SCHEDULER[Cloud Scheduler<br/>Cron Jobs]
        end

        subgraph "Monitoring"
            LOGS[Cloud Logging<br/>Centralized Logs]
            METRICS[Cloud Monitoring<br/>Metrics & Alerts]
        end
    end

    subgraph "External APIs"
        ARXIV[arXiv API]
        S2[Semantic Scholar]
        CLAUDE_API[Anthropic API]
    end

    U1 -->|HTTPS| CDN
    CDN --> STORAGE
    U1 -->|API Calls| LB
    LB --> CR
    U2 -->|Local MCP| CR

    CR --> SQL
    CR --> SECRETS
    CR --> ARXIV
    CR --> S2
    CR --> CLAUDE_API

    BUILD -->|Deploy| CR
    SCHEDULER -->|Trigger| CR

    CR --> LOGS
    CR --> METRICS

    style U1 fill:#e1f5ff
    style U2 fill:#e1f5ff
    style CDN fill:#fff4e1
    style STORAGE fill:#fff4e1
    style CR fill:#fff4e1
    style SQL fill:#e8f5e9
    style SECRETS fill:#e8f5e9
    style BUILD fill:#fce4ec
    style SCHEDULER fill:#fce4ec
    style LOGS fill:#f3e5f5
    style METRICS fill:#f3e5f5
```

## Deployment Flow (CI/CD)

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant GH as GitHub
    participant CB as Cloud Build
    participant GCR as Container Registry
    participant CR as Cloud Run
    participant SQL as Cloud SQL

    Dev->>GH: git push origin main
    GH->>CB: Trigger webhook

    CB->>CB: Clone repository
    CB->>CB: docker build -t image

    CB->>GCR: docker push image

    CB->>CR: gcloud run deploy<br/>--image=image<br/>--set-secrets=...

    CR->>SQL: Verify connection
    SQL-->>CR: Connection OK

    CR->>CR: Run migrations<br/>Start new revision

    CR->>CR: Health check /health

    CR->>CR: Route traffic to new revision

    CR-->>CB: Deployment successful
    CB-->>GH: Update commit status ✅
    GH-->>Dev: Deployment complete!
```

## Data Flow: Complete User Journey

```mermaid
graph TD
    Start([User opens Claude Desktop]) --> A1[Ask: 'Fetch latest AI papers']

    A1 --> B1[Claude decides: use fetch_articles]
    B1 --> C1[MCP: fetch_articles source=arxiv]
    C1 --> D1[ArxivFetcher: GET RSS feed]
    D1 --> E1[Parse & save to DB: 5 new papers]
    E1 --> F1[Generate embeddings: Store in ChromaDB]

    F1 --> A2[User: 'Show me papers about transformers']

    A2 --> B2[Claude decides: use search_papers]
    B2 --> C2[MCP: search_papers query='transformers']
    C2 --> D2[VectorStore: semantic_search]
    D2 --> E2[Return top 10 matches with scores]

    E2 --> A3[User: 'I like paper #2']

    A3 --> B3[Claude decides: use rate_article]
    B3 --> C3[MCP: rate_article id=2 rating=5]
    C3 --> D3[Database: UPDATE rating=5]

    D3 --> A4[User: 'Give me recommendations']

    A4 --> B4[Claude decides: use get_recommendations]
    B4 --> C4[RecommendationEngine: calculate scores]
    C4 --> D4[Consider: ratings, interests, citations]
    D4 --> E4[Return top 10 personalized papers]

    E4 --> End([User discovers new research!])

    style Start fill:#e1f5ff
    style End fill:#4caf50,color:#fff
    style A1 fill:#fff4e1
    style A2 fill:#fff4e1
    style A3 fill:#fff4e1
    style A4 fill:#fff4e1
```

## Component Interaction Matrix

```mermaid
graph LR
    subgraph "Components"
        A[Web UI]
        B[CLI]
        C[MCP Server]
        D[FastAPI]
        E[Database]
        F[VectorStore]
        G[Recommender]
        H[Fetchers]
    end

    A -->|HTTP REST| D
    B -->|Direct| E
    B -->|Direct| F
    C -->|Direct| E
    C -->|Direct| F
    C -->|Direct| G
    D -->|SQLAlchemy| E
    D -->|Queries| F
    D -->|Calls| G
    G -->|Reads| E
    G -->|Searches| F
    H -->|Writes| E
    H -->|Stores| F

    style A fill:#e1f5ff
    style B fill:#e1f5ff
    style C fill:#e1f5ff
    style D fill:#fff4e1
    style E fill:#e8f5e9
    style F fill:#e8f5e9
    style G fill:#fff4e1
    style H fill:#fff4e1
```

## Testing Coverage Overview

```mermaid
pie title Test Coverage by Module
    "MCP Server (86.3%)" : 86.3
    "Database (97.9%)" : 97.9
    "arXiv Fetcher (80.9%)" : 80.9
    "Content Processor (63.6%)" : 63.6
    "LLM Processor (58.3%)" : 58.3
    "Backend API (0%)" : 0
    "CLI (0%)" : 0
```

## Technology Stack

```mermaid
graph TD
    subgraph "Frontend Stack"
        F1[React 18]
        F2[Vite]
        F3[Tailwind CSS]
        F4[TypeScript]
    end

    subgraph "Backend Stack"
        B1[FastAPI]
        B2[Uvicorn]
        B3[SQLAlchemy]
        B4[Pydantic]
    end

    subgraph "AI/ML Stack"
        M1[Anthropic Claude API]
        M2[ChromaDB]
        M3[sentence-transformers]
        M4[all-MiniLM-L6-v2]
    end

    subgraph "Infrastructure"
        I1[Docker]
        I2[Google Cloud Run]
        I3[Cloud SQL PostgreSQL]
        I4[Cloud Build]
    end

    subgraph "Development"
        D1[pytest + pytest-cov]
        D2[black + ruff]
        D3[Git + GitHub]
    end

    style F1 fill:#61dafb
    style B1 fill:#009688
    style M1 fill:#ff6f00
    style I1 fill:#2496ed
    style D1 fill:#0a9396
```

---

## How to View These Diagrams

1. **On GitHub**: Just open this file - Mermaid renders automatically!
2. **VS Code**: Install "Markdown Preview Mermaid Support" extension
3. **Online**: Copy to https://mermaid.live for interactive editing
4. **Export**: Use mermaid-cli to export as PNG/SVG/PDF

```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Export diagram
mmdc -i ARCHITECTURE_DIAGRAM.md -o architecture.png
```

## Legend

- 🔵 Blue boxes: User interfaces / Entry points
- 🟡 Yellow boxes: Application layer / Services
- 🟢 Green boxes: Data storage / State
- 🔴 Red boxes: External services / APIs
- 🟣 Purple boxes: Monitoring / Observability
