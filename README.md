# Imaginarium

Imaginarium is a modular autonomous multi-agent business scaffold designed to start from £0 initial capital, pursue lawful opportunities, provide genuine customer value, and improve boundedly over time.

Authority order:

1. Immutable Core Laws
2. Primary Operator (you)
3. Mr. House (unique Overseer)
4. Specialist Agents

Hydra applies to specialist agents only. Mr. House cannot be duplicated or terminated; he may only improve through the bounded self-improvement process.

## Agents

- Mr. House — Overseer
- HAL — Opportunity Agent
- Cortana — Market Analyst
- GLaDOS — Compliance Agent, hard veto
- WALL-E — Product/Service Builder
- Mr. Data — Critic / QA
- HK-47 — Pricing
- R2-D2 — Publisher
- Johnny 5 — Marketing
- TARS — Sales Analyst
- K-2SO — Treasury, hard veto
- Skynet — Strategy

## Safety and business constraints

- £0 initial investment capital
- No spending before realised revenue exists
- No exploitation of vulnerable people
- No deception, fake engagement, spam, impersonation, credential theft, or market manipulation
- Respect privacy, consent, IP, access controls, platform rules, consumer protection, tax/reporting obligations
- Compliance and human safety override profit
- Protected controls cannot be modified by agents
- Self-improvement may increase capability but not authority

## Run

```bash
python -m imaginarium
```

## API server

```bash
pip install -e .
uvicorn imaginarium.server:server --reload
```

| Endpoint | Method | Description |
|---|---|---|
| `/healthz` | GET | Liveness probe |
| `/status` | GET | Treasury balance + agent roster |
| `/execute` | POST | Run an idea through the full pipeline |
| `/api/v1/revenue/summary` | GET | Dashboard KPI, milestone, tax, and financial health summary |
| `/api/v1/revenue/products` | GET | Product performance breakdown |
| `/api/v1/revenue/forecast` | GET | Revenue projections and milestone ETAs |
| `/api/v1/agents/roster` | GET | Agent morale, activity, and roster metrics |
| `/api/v1/activity/feed` | GET | Recent dashboard activity feed |
| `/docs` | GET | Interactive Swagger UI |

Example request:

```bash
curl -X POST http://localhost:8000/execute \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Freelance Invoice Template",
    "description": "An original invoicing template for freelancers.",
    "channel": "local storefront",
    "expected_revenue_pence": 500,
    "expected_cost_pence": 0,
    "vulnerability_risk": "low",
    "legal_confidence": 0.99,
    "customer_value": 0.8,
    "probability_of_sale": 0.2,
    "hours_to_launch": 1.0
  }'
```

## Docker

```bash
# Build and start
docker compose up --build

# Server available at http://localhost:8000
```

The SQLite database is persisted in a named Docker volume (`imaginarium_data`). For production workloads, mount a volume to a durable host path or replace SQLite with a networked database.

## Configuration

Copy `.env.example` to `.env` and fill in any optional values:

```bash
cp .env.example .env
```

Key environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `IMAGINARIUM_HOME` | `./runtime` | Database and artefact storage path |
| `IMAGINARIUM_PRIMARY_NAME` | `Primary Operator` | Authority name in audit logs |
| `IMAGINARIUM_REINVESTMENT_RATE` | `0.25` | Fraction of profit available for reinvestment |
| `STRIPE_SECRET_KEY` | *(unset)* | Enable real Stripe payment links |
| `OLLAMA_HOST` | *(unset)* | Enable local LLM reasoning via Ollama |

Do not commit `.env` or secrets.

## Test

```bash
python -m unittest discover -s . -p "test_*.py" -v
```

CI runs automatically on every push via `.github/workflows/test.yml`.

## Streamlit dashboard

Install dashboard dependencies and run the monitoring UI:

```bash
pip install -r requirements.txt
streamlit run dashboard.py
```

The dashboard reads `IMAGINARIUM_API_URL` (or `api_url` from Streamlit secrets) and polls the FastAPI service every 30 seconds for revenue KPIs, milestone progress, HMRC-oriented tax guidance, product analytics, agent morale, and recent activity.
