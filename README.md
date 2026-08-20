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

## Test

```bash
python -m unittest discover -s tests -v
```

## Configuration

Copy `.env.example` to `.env` for optional external adapters. Do not commit secrets.

External publishing/payment adapters are disabled by default. The default publisher writes only to `runtime/site`.
