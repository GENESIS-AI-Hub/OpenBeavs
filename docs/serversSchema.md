```mermaid
graph TD
    subgraph External
        A[External SSO Provider (Microsoft SSO / Duo)]
    end

    subgraph Google Cloud Platform (GCP) Hosting
        direction LR
        subgraph Front-End / Web Service
            H[Web-Based Chat UI (React.js on Cloud Run/App Engine)]
        end

        subgraph Back-End Routing Service
            M[Core Back-End Routing Service (Node.js/Python on Cloud Run)]
        end

        subgraph Persistence & Registry
            K[Agent Services Registry (PostgreSQL/Firebase)]
            F[Chat History & User Data (ChatDB, MessagesDB)]
            O[File Storage Bucket (Cloud Storage)]
        end
    end

    subgraph Decentralized Agent Systems
        J(OSU-Developed Agent 1: FAIE/GOA)
        L(External Agent N: Other OSU Services)
    end

    %% Flow - Authentication (Required: FR2)
    A --> H : 1. SSO/Duo Auth
    H --> M : 2. Token Exchange / Session Init
    M --> F : 3. Store/Retrieve User ONID & Session

    %% Flow - Interaction (Required: Core Goal)
    H --> M : 4. User Chat Query + Attachments
    O --> M : 4b. Fetch File from Bucket (if attached)
    M --> K : 5. Lookup Agent Endpoint via Registry

    %% Flow - Agent Routing (Required: Back-End Routing)
    M -- 6. Route Context / Query --> J
    M -- 6b. Route Context / Query --> L
    J --> M : 7. Agent Response (JSON/Text)
    L --> M : 7b. Agent Response (JSON/Text)
    M --> H : 8. Response to User

    %% Flow - Persistence (Required: Persistent Conversations)
    M --> F : 9. Store New Message / Update ChatDB
    H --> F : 10. Load Chat History on session start

    %% File Uploads
    H --> O : 4a. File Upload (Client to Bucket)
    M --> O : 4b. Fetch File (Service to Bucket)

    style H fill:#39f,stroke:#333,stroke-width:2px,color:#fff
    style M fill:#9f9,stroke:#333,stroke-width:2px
    style J fill:#f9f,stroke:#333,stroke-width:2px
    style L fill:#f9f,stroke:#333,stroke-width:2px
    style F fill:#ccf,stroke:#333,stroke-width:2px
    style O fill:#ffc,stroke:#333,stroke-width:2px
```
