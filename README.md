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
- **Deployment**: Docker, Docker Compose (local)

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

## 2. Run the full stack with Docker Compose

```bash
cp .env.example .env
# fill in GROQ_API_KEY and PINECONE_API_KEY at minimum

docker compose up --build
```

When running the API on your host with `uvicorn`, do not use the Docker-only hostname
`mysql` in `DATABASE_URL`. Use `localhost` for a MySQL server exposed on your machine,
for example `mysql+pymysql://aegis:aegis_password@localhost:3306/aegis_governance`.

This starts:
- **MySQL** on `:3306` (auto-creates `aegis_governance` + `mlflow_tracking` schemas via `sql/init.sql`)
- **MLflow** tracking server on `:5000` (backed by MySQL)
- **AegisAI app** on `:8000`

## 2.1 Run on AWS EC2

On EC2, build and run the app container directly:

```bash
docker build -t aegis-app .
docker run -d --name aegis-app -p 80:8000 --env-file .env aegis-app
```

If you want to change the container port, pass `-e PORT=...` and map the host port to match:

```bash
docker run -d --name aegis-app -e PORT=8000 -p 80:8000 --env-file .env aegis-app
```

## 3. Try it

```bash
# Upload a policy document
curl -X POST http://localhost:8000/api/v1/documents/upload \
  -F "file=@sample_policy.pdf" -F "source_type=policy"

# Ask a governed question
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "What is our data retention policy for customer records?"}'

# Governance dashboard stats
curl http://localhost:8000/api/v1/dashboard/stats

# Full audit trail for one request
curl http://localhost:8000/api/v1/audit/<trace_id>
```

A typical `/chat` response includes a governance block like:

```json
{
  "governance": {
    "risk_score": 18,
    "grounding_score": 0.94,
    "pii_detected": false,
    "policy_violation": false,
    "hallucination_flag": false,
    "governance_decision": "allowed",
    "confidence": "High"
  }
}
```

## 4. Deploy to AWS (EKS)

### 4.1 Push images to ECR

```bash
aws ecr create-repository --repository-name aegis-app
aws ecr create-repository --repository-name aegis-mlflow

aws ecr get-login-password --region <region> | docker login --username AWS \
  --password-stdin <account_id>.dkr.ecr.<region>.amazonaws.com

docker build -t <account_id>.dkr.ecr.<region>.amazonaws.com/aegis-app:latest .
docker push <account_id>.dkr.ecr.<region>.amazonaws.com/aegis-app:latest

docker build -t <account_id>.dkr.ecr.<region>.amazonaws.com/aegis-mlflow:latest -f docker/Dockerfile.mlflow .
docker push <account_id>.dkr.ecr.<region>.amazonaws.com/aegis-mlflow:latest
```

### 4.2 Create the EKS cluster

```bash
eksctl create cluster \
  --name aegis-cluster \
  --region <region> \
  --nodegroup-name aegis-nodes \
  --node-type t3.large \
  --nodes 3 --nodes-min 3 --nodes-max 6 \
  --managed
```

### 4.3 Recommended: use managed AWS services instead of in-cluster stateful pods

- **MySQL** → Amazon RDS for MySQL (Multi-AZ) instead of `k8s/03-mysql.yaml`
- **MLflow artifacts** → S3 bucket instead of a PVC (`--default-artifact-root s3://<bucket>/mlflow-artifacts`)
- **Secrets** → AWS Secrets Manager + [External Secrets Operator](https://external-secrets.io/), instead of hand-editing `k8s/02-secret.yaml`
- **Ingress/TLS** → AWS Load Balancer Controller + ACM certificate (see annotation in `06-service-ingress.yaml`)

### 4.4 Install the AWS Load Balancer Controller (for the Ingress)

```bash
eksctl utils associate-iam-oidc-provider --cluster aegis-cluster --approve
helm repo add eks https://aws.github.io/eks-charts
helm install aws-load-balancer-controller eks/aws-load-balancer-controller \
  -n kube-system --set clusterName=aegis-cluster
```

### 4.5 Apply manifests

```bash
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/01-configmap.yaml

# Replace placeholders in 02-secret.yaml or create the secret imperatively instead:
kubectl create secret generic aegis-secrets -n aegis-ai \
  --from-literal=SECRET_KEY=$(openssl rand -hex 32) \
  --from-literal=DATABASE_URL="mysql+pymysql://aegis:<pwd>@<rds-endpoint>:3306/aegis_governance" \
  --from-literal=GROQ_API_KEY=<your_key> \
  --from-literal=PINECONE_API_KEY=<your_key> \
  --from-literal=MYSQL_ROOT_PASSWORD=<pwd> \
  --from-literal=MYSQL_PASSWORD=<pwd>

# Skip 03-mysql.yaml if using RDS
kubectl apply -f k8s/04-mlflow.yaml
kubectl apply -f k8s/05-app-deployment.yaml
kubectl apply -f k8s/06-service-ingress.yaml
kubectl apply -f k8s/07-hpa.yaml

kubectl get pods -n aegis-ai -w
kubectl get ingress -n aegis-ai   # grab the ALB hostname, point your DNS at it
```

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
