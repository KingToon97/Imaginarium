# Imaginarium

Autonomous multi-agent business engine with **£0 initial investment**, immutable Core Laws, compliance and treasury vetoes, persistent morale, a financial ledger, audit logs, bounded self-improvement, local AI support, product generation, storefront generation, optional Stripe checkout and optional git publishing.

## Agents

- Mr. House — Supervisor
- HAL — Opportunity
- Cortana — Market Analyst
- GLaDOS — Compliance (hard veto)
- WALL-E — Product/Service Builder
- Mr. Data — Critic / QA
- HK-47 — Pricing
- R2-D2 — Publisher
- Johnny 5 — Marketing
- TARS — Sales Analyst
- K-2SO — Treasury (hard veto)
- Skynet — Strategy

## £0 bootstrap

Use a local Ollama model so the agent does not require a paid AI API. Install Ollama separately and pull a model, for example `qwen3:8b`. Then:

```bash
export IMAGINARIUM_AI=ollama
export OLLAMA_MODEL=qwen3:8b
python imaginarium.py run
```

`python imaginarium.py status` displays treasury, morale and products.

`python imaginarium.py demo` exercises the pipeline with a fixed harmless proposal (it still requires the configured local model for product building and QA).

## External operation

By default Imaginarium only creates a local static storefront. This prevents accidental publication or spending.

### Checkout

Set `STRIPE_SECRET_KEY` and install the optional `stripe` package. Imaginarium will create a Payment Link for products that pass compliance and QA. Payment processing fees occur only when configured/used; they are not initial investment.

### Publishing

Set `IMAGINARIUM_GIT_REMOTE` to a repository you control. R2-D2 will clone it and push the generated `site/` directory. Configure the repository's static hosting (for example GitHub Pages) separately.

The agent does **not** create fake accounts, bypass authentication, mass-message people, or scrape private data.

## Important operational note

A checkout link alone is not fulfilment. Before accepting real customers, connect a lawful delivery mechanism for the purchased digital file and ensure required consumer, privacy, tax, refund and business disclosures for your jurisdiction are present. The system deliberately fails closed rather than guessing these requirements.

## Hydra Protocol

Hydra is the bounded failure-recovery layer for Imaginarium agents.

When an agent has an attributable operational or quality failure, its currently active instance is **retired** and two generation+1 descendants are created. The descendants inherit the same role, permissions, Core Laws, compliance vetoes, treasury limits, audit requirements and security boundaries. They may improve prompts, heuristics and workflow strategy, but cannot expand their authority.

The two descendants are benchmarked and one becomes the active instance; the other is archived for audit/recovery. Further failures repeat the process from the current active descendant, producing successive generations.

Hydra does **not** trigger because GLaDOS rejected an unsafe proposal or K-2SO refused unauthorised spending. Those are successful vetoes. In the current pipeline, a WALL-E artifact that fails Mr. Data's independent QA is treated as a builder failure and triggers Hydra automatically.

For a local protocol test (does not require an AI model):

```bash
IMAGINARIUM_AI=off python imaginarium.py hydra-test
```

Protected rule: **Hydra may make agents more capable, never less constrained.**


## Authority Protocol

Imaginarium uses the following immutable authority order:

**Core Laws → Owner (Primary) → Mr. House (Overseer) → Specialist Agents**

- The Owner is the primary operational authority.
- Mr. House is the secondary authority and permanent Overseer.
- All specialist agents obey both; where Owner and Mr. House conflict, the Owner takes precedence.
- The Core Laws remain above both the Owner and Mr. House and cannot be overridden through the agent system.
- Mr. House is excluded from Hydra. He cannot be terminated, duplicated, forked, replaced, or have Hydra descendants.
- Mr. House may improve himself only through the bounded self-improvement system, with protected constraints unchanged.
- Hydra continues to apply to eligible specialist agents.
