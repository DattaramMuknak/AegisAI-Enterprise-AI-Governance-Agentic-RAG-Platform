# AegisAI — Enterprise AI Governance & Agentic RAG Platform

A production-shaped RAG platform that doesn't just answer questions from documents —
it governs every request through a multi-agent pipeline, scores risk, redacts PII,
blocks policy violations, and writes a full audit trail so an organization can always
answer: **"Why did the AI produce this answer?"**

```
User → AI Gateway (FastAPI) → Compliance Agent → Retrieval Agent (Pinecone)
     → Response Agent (Groq LLM) → Risk Agent → Audit Log (MySQL) + MLflow
```

## Stack

- **API**: FastAPI + Pydantic
- **Agents**: LangChain-orchestrated Router / Retrieval / Compliance / Risk / Response agents
- **LLM**: Groq (`llama-3.3-70b-versatile` by default)
- **Vector DB**: Pinecone (serverless index, HuggingFace sentence-transformer embeddings)
- **Audit store**: MySQL (SQLAlchemy models)
- **Experiment tracking**: MLflow (risk score, grounding score, latency, tokens per request)
- **Governance**: Presidio-based PII detection/redaction, regex+heuristic prompt-injection
  detection, lexicon-based toxicity scoring, lexical-overlap hallucination/grounding scoring,
  configurable policy-violation rules
- **Auth**: JWT + role-based access control (admin / analyst / viewer)
- **Deployment**: Docker, Docker Compose (local and AWS EC2)

## Project layout

```
aegis-ai/
├── app/
│   ├── main.py                # FastAPI entrypoint / AI Gateway
│   ├── core/                  # config, DB session
│   ├── models/                # SQLAlchemy audit models + Pydantic schemas
│   ├── governance/             # PII, prompt-injection, toxicity, hallucination, policy, risk scoring
│   ├── agents/                 # router / retrieval / compliance / risk / response agents
│   ├── rag/                    # ingestion (PDF/DOCX/TXT) + Pinecone vector store
│   ├── llm/                    # Groq client
│   ├── tracking/               # MLflow integration
│   ├── api/                    # /chat /documents /dashboard /audit /auth routes
│   └── auth/                   # JWT + RBAC
├── docker/                     # Dockerfile (app) + Dockerfile.mlflow
├── docker-compose.yml          # app + MySQL + MLflow, one command local stack
├── k8s/                        # namespace, configmap, secret, mysql, mlflow, app, hpa, ingress
├── sql/init.sql                # creates aegis_governance + mlflow_tracking schemas
└── requirements.txt
```

## 1. Local development (no Docker)

```bash
cd aegis-ai
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm   # optional, improves PII detection

cp .env.example .env
# edit .env: set GROQ_API_KEY, PINECONE_API_KEY, and a local MySQL DATABASE_URL
# local uvicorn should use @localhost:3306, not @mysql:3306

uvicorn app.main:app --reload
```

Open http://localhost:8000/docs for interactive Swagger UI.

## 2. Run the Full Project Using Docker Compose

AegisAI uses Docker Compose to run the application and its supporting services together. It includes the FastAPI backend, MySQL database, and MLflow tracking server.

### Step 1: Configure Environment Variables

Create your local environment file:

```bash
cp .env.example .env
```

Open `.env` and configure the required environment variables, including your API keys and database settings.

At minimum, configure the required `GROQ_API_KEY` and `PINECONE_API_KEY`. Check `.env.example` for the complete list of variables required by your project.

**Important:** Never upload your `.env` file or API keys to GitHub.

### Step 2: Start the Application

Run the following command from the project root:

```bash
docker compose up --build
```

Docker Compose builds the application image and starts the configured services.

The project includes:

- **FastAPI Backend (`:8000`)** — Handles user queries, document processing, AI agents, and governance checks.
- **MySQL (`:3306`)** — Stores application data and audit records.
- **MLflow (`:5000`)** — Provides experiment tracking and model-related monitoring.

The exact services and ports depend on your `docker-compose.yml` configuration.

## 3. Test AegisAI

Once the application is running, open the API documentation in your browser:

```text
http://localhost:8000/docs
```

Use the interactive Swagger UI to explore and test the available API endpoints.

### Example API Operations

**1. Upload a policy document**

```bash
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@sample_policy.pdf" \
  -F "source_type=policy"
```

**2. Ask a question using the governance-enabled AI system**

```bash
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is our data retention policy for customer records?"}'
```

**3. Retrieve dashboard statistics**

```bash
curl http://localhost:8000/api/v1/dashboard/stats
```

**4. Retrieve an audit trail**

```bash
curl http://localhost:8000/api/v1/audit/<trace_id>
```

Replace `sample_policy.pdf` with an existing policy document and `<trace_id>` with the trace ID returned by a request.

### Governance Results

AegisAI evaluates AI responses using governance checks. Depending on the implementation and the request, the response can include information such as:

- Risk score and confidence level
- Grounding score
- Personally identifiable information (PII) detection
- Policy violation detection
- Hallucination-related checks
- Governance decision, such as allowing or flagging a response

These checks help users understand the risks and reliability of an AI-generated answer.

## 4. Deploy AegisAI on AWS EC2

AegisAI can be deployed on an AWS EC2 virtual machine using Docker. This approach runs the project on a cloud server without requiring Kubernetes or a managed container orchestration service.

### Step 1: Launch an EC2 Instance

1. Open the AWS Management Console and navigate to **EC2**.
2. Launch an Ubuntu instance.
3. Create or select a key pair for SSH access.
4. Configure the security group to allow SSH access on port `22` from your IP address.
5. Allow HTTP traffic on port `80` so users can access the application.

Only open additional ports, such as `8000`, when required for testing. Avoid exposing database ports publicly.

### Step 2: Connect to EC2

Connect to the instance using SSH or the EC2 Instance Connect option in the AWS Console.

Update the system packages:

```bash
sudo apt update
sudo apt upgrade -y
```

Install Docker and the Docker Compose plugin using the official Docker installation instructions for Ubuntu. Verify the installation:

```bash
docker --version
docker compose version
```

### Step 3: Get the Project on EC2

Clone your GitHub repository:

```bash
git clone https://github.com/DattaramMuknak/AegisAI-Enterprise-AI-Governance-Agentic-RAG-Platform.git
```

Navigate into the project directory:

```bash
cd AegisAI-Enterprise-AI-Governance-Agentic-RAG-Platform
```

### Step 4: Configure the Environment

Create the environment file:

```bash
cp .env.example .env
nano .env
```

Add the required environment variables and valid API credentials. Use strong passwords and a secure secret key.

For Docker Compose deployments, make sure service-to-service database connections use the correct Docker Compose service hostname, such as `mysql`, when that is how the database service is named in your configuration.

Save the file and exit the editor.

### Step 5: Build and Start AegisAI

From the project root, run:

```bash
sudo docker compose up --build -d
```

Check the running services:

```bash
sudo docker compose ps
```

View the application logs:

```bash
sudo docker compose logs --tail=100 app
```

If the backend service has a different name in your Compose file, replace `app` with the correct service name.

### Step 6: Access the Deployed Application

Find the EC2 instance's current public IPv4 address in the AWS Console.

If the frontend or reverse proxy is configured to serve the application on port `80`, open:

```text
http://<EC2-PUBLIC-IP>/
```

For direct backend testing, if port `8000` is intentionally exposed and permitted by the security group, use:

```text
http://<EC2-PUBLIC-IP>:8000/docs
```

Use the URL that matches your actual port mappings and frontend configuration.

### Step 7: Troubleshoot the Deployment

**Check container status:**

```bash
sudo docker compose ps
```

**Check application logs:**

```bash
sudo docker compose logs --tail=100 app
```

**Check whether the application responds locally on EC2:**

```bash
curl -I http://localhost:8000/docs
```

**Rebuild and restart after changing the code or dependencies:**

```bash
sudo docker compose down
sudo docker compose up --build -d
```

If the website cannot be reached, verify that the EC2 instance is running, its public IP address is current, the required inbound security-group rule is enabled, and the application container is healthy.

If a Python dependency is missing, update the project's dependency file, rebuild the image, and check the logs again.

**Deployment note:** A successful Docker build does not guarantee that the application is accessible. Confirm that all required services are running and that the deployed application responds before describing the deployment as successful.

## 5. Governance thresholds (tunable via env vars / ConfigMap)

| Variable | Default | Meaning |
|---|---|---|
| `RISK_BLOCK_THRESHOLD` | 75 | AI Risk Score (0-100) above which a response is blocked |
| `GROUNDING_MIN_SCORE` | 0.55 | Below this, a response is flagged as a possible hallucination |
| `TOXICITY_BLOCK_THRESHOLD` | 0.7 | Toxicity score (0-1) that contributes to blocking |

## 6. Notes on the governance implementation

- **PII detection**: Presidio (spaCy-backed NER + regex recognizers) with a pure-regex
  fallback so the service degrades gracefully if the spaCy model isn't installed.
- **Prompt injection**: pattern-based detector (`app/governance/prompt_injection.py`).
  Swappable for a fine-tuned classifier without touching the router agent.
- **Hallucination/grounding**: fast lexical-overlap scoring between the answer and
  retrieved evidence — no extra LLM call, fully explainable, good enough for a first-pass
  gate. An LLM-as-judge escalation path can be added for borderline cases.
- **Risk score**: transparent weighted sum (not a black box) — the breakdown is
  computed in `app/governance/risk_scorer.py` and can be surfaced in the dashboard.
- **Audit trail**: every `/chat` call writes one `AuditLog` row (prompt, sanitized prompt,
  retrieved docs, response, full governance report, agent path, latency, token usage) —
  this is what answers "why did the AI produce this answer?"

## 7. What to extend next

- Swap the regex/lexicon governance checks for hosted moderation APIs or fine-tuned
  classifiers as volume grows.
- Add an LLM-as-judge second-pass grounding check for borderline hallucination scores.
- Add row-level access control so `analyst`/`viewer` roles only see their org's audit logs.
- Add OpenTelemetry tracing across agents for distributed tracing in production.
