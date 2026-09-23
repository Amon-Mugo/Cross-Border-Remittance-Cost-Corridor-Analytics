# Cross-Border Remittance Cost & Corridor Analytics

An end-to-end AWS-native data engineering platform that ingests, transforms, and analyzes the World Bank's Remittance Prices Worldwide (RPW) dataset — surfacing how much it actually costs to send money across 350+ international corridors, and why.

**Live dashboard:** https://amon-mugo-cross-border-remittance-cost-corr-dashboardapp-hmpwt3.streamlit.app/

---

## Why this project exists

Remittances are a lifeline for millions of households, but pricing across providers, corridors, and payment methods is opaque and inconsistent. This project builds a production-style pipeline — from raw World Bank data to a queryable Snowflake warehouse to an interactive dashboard — to make that cost structure transparent and explorable, with a dedicated lens on Kenya as a major receiving market.

**Key finding:** in Kenya's inbound corridors, bank-published transfer rates run 3-5x higher than mobile money and money-transfer-operator (MTO) rates for the same corridor — a gap that's invisible unless you can compare providers side by side.

---

## Architecture

World Bank RPW (.xlsx, cumulative quarterly release)
        |
        v
  Airflow DAG (manual xlsx drop --> S3 raw/)
        |
        v
  EMR Serverless (PySpark transform: validate grain, flag quality issues)
        |
        v
  S3 curated/ (partitioned Parquet, per quarter_label)
        |
        v
  Snowflake RAW layer (stored procedure, idempotent per-quarter load)
        |
        v
  dbt: staging --> intermediate --> marts
        |
        v
  Streamlit dashboard (DuckDB snapshot of marts, deployed to Streamlit Cloud)

Terraform provisions all AWS infra (S3, ECR, IAM/OIDC, EMR Serverless app).
GitHub Actions runs CI on every PR and gated CD on merge to main
(Terraform apply -> ECR push + EMR image update -> dbt run to prod),
with manual approval required before any production change.

---

## Tech stack

| Layer | Tools |
|---|---|
| Infrastructure as Code | Terraform (OIDC-based GitHub Actions auth, no long-lived AWS keys) |
| Compute | AWS EMR Serverless (Spark 3.5 / EMR 7.1.0), Docker |
| Storage | AWS S3 (raw + curated buckets) |
| Transform | PySpark |
| Warehouse | Snowflake (RSA key-pair auth, role-based least privilege) |
| Modeling | dbt (staging -> intermediate -> marts, full test coverage) |
| Orchestration | Apache Airflow 3.3.1 (Dockerized, local) |
| Dashboard | Streamlit + Plotly, DuckDB (offline snapshot of marts) |
| CI/CD | GitHub Actions (separate CI and gated CD pipelines) |

---

## Data pipeline

**Source:** World Bank Remittance Prices Worldwide dataset, approximately 198,000 raw rows spanning 2016 Q2 through 2025 Q1, cumulative and republished quarterly.

**Ingestion and transform (EMR Serverless / PySpark)**

- Structural dedup on true grain (`raw_id` + `cc_number`, where `cc_number` distinguishes the $200 vs $500 send-amount tier)
- Data quality flags computed and reported without dropping rows (FX margin consistency, transparency disclosure, duplicate detection)
- Output partitioned per-quarter to match Snowflake's load procedure
- Final grain-deduplicated row count: 314,846

**Warehouse load (Snowflake)**

- Idempotent per-quarter DELETE-then-COPY via stored procedure
- Storage integration for direct S3 to Snowflake reads, no credential passing

**Modeling (dbt)**

- Staging: 1:1 typed model over raw, snake_cased, no filtering
- Intermediate: enriched with currency and region/income reference seeds, cost components decomposed (fee + FX margin vs. reported total), transparency and mismatch flags derived
- Marts: four models
  - `mart_corridor_cost_trends` — cost trends by corridor and period
  - `mart_provider_comparison` — full provider-level comparison, preserving all real cost-driver dimensions (firm type, payment instrument, pickup method)
  - `mart_transparency_flags` — firm-level scorecard for pricing transparency and reporting consistency
  - `mart_kenya_corridors` — Kenya-specific slice, sending vs. receiving role
- Full test suite: grain uniqueness, referential invariants, not-null coverage, accepted-values checks — all green in CI

**Orchestration (Airflow)**

- Single DAG: ingest (convert new quarterly release) -> transform (EMR Serverless job) -> load (Snowflake stored procedure call)
- Failure alerting via a custom email callback (SMTP), since Airflow's built-in `email_on_failure` doesn't fire reliably in this setup

**CI/CD (GitHub Actions)**

- CI (every PR): Terraform fmt/validate/plan, Docker build/lint, PySpark unit tests, dbt build against an isolated CI schema
- CD (merge to main): Terraform apply -> Docker image push to ECR + EMR Serverless application image update -> dbt run promoted to production schemas. Terraform apply and the image swap are gated behind a GitHub Environment requiring manual approval before touching real infrastructure

---

## Dashboard

Built with Streamlit and Plotly, backed by a self-contained DuckDB snapshot of the four dbt marts (not live Snowflake queries, to keep the deployed app dependency-light and fast).

### Global view

Multi-corridor cost trend comparison and a provider transparency scorecard across the full dataset.

![Global cost trends](global_screanshots/global-cost-trends.png)
![Global corridor detail](global_screanshots/global-corridor-detail.png)

### Kenya spotlight

Sending vs. receiving role toggle, cost trends, and firm-level comparison for Kenya's corridors.

![Kenya sending and receiving corridors](screenshots_kenya/kenya-sending-receiving.png)
![Kenya cost breakdown](screenshots_kenya/kenya-cost-breakdown.png)
![Average cost by firm in Kenya](screenshots_kenya/kenya-avg-cost-by-firm.png)

---

## Key findings

- **Bank vs. MTO/mobile pricing gap:** in Kenya's inbound corridors, bank-published rates (major commercial banks) run 3-5x higher than mobile money and MTO rates for equivalent transfers.
- **Kenya's remittance profile:** a strong receiving market with heavy inbound competition — 6 corridors and 64 firms on the receiving side, versus 4 corridors and 21 firms sending, consistent with Kenya's real-world position.
- **Pricing transparency:** the large majority of observations (roughly 98 percent) are fully disclosed and internally consistent; a small but real minority (under 2 percent) show missing cost components or a mismatch between reported and decomposed total cost.

---

## Local setup

Prerequisites: Python 3.12, Docker, an AWS account with a configured SSO profile, a Snowflake account, and Terraform.

Clone and set up the main project venv (dbt and orchestration dependencies):

    git clone https://github.com/Amon-Mugo/Cross-Border-Remittance-Cost-Corridor-Analytics.git
    cd Cross-Border-Remittance-Cost-Corridor-Analytics
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt

Provision AWS infrastructure:

    cd terraform
    terraform init
    terraform plan

Run dbt against Snowflake (requires profiles.yml with RSA key-pair auth configured):

    cd ../dbt
    dbt build

Bring up Airflow locally:

    cd ..
    docker compose up -d

Run the dashboard locally:

    cd dashboard
    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    streamlit run app.py

---

## Project status

All 10 milestones complete: infrastructure, containerized transform layer, PySpark pipeline, Snowflake warehouse, dbt modeling, Airflow orchestration, interactive dashboard, gated CI/CD, and this documentation.

---

## Author

**Amon Mugo** — Data Engineer, Kenya
GitHub: [Amon-Mugo](https://github.com/Amon-Mugo)
