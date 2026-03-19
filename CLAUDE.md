# CLAUDE.md — Contexto do Projeto

## Objetivo
Pipeline de dados completo para análise estatística do Campeonato Brasileiro Série A 2023.
Coletar estatísticas do FBref, armazenar no PostgreSQL via Docker, orquestrar com Airflow
e analisar correlações entre métricas e vitórias/derrotas dos times.

## Stack
- Scraping: Python + BeautifulSoup + Requests (fonte: FBref.com)
- Orquestração: Apache Airflow 2.8.1
- Banco de dados: PostgreSQL 15 (porta 5434)
- Infra: Docker Compose
- Análise: Pandas, Scikit-learn, Jupyter

## Estrutura do projeto
```
brasileirao-2023-pipeline/
├── scraping/
│   ├── scrapers/
│   │   ├── match_scraper.py       # Resultados e gols por partida (VAZIO)
│   │   ├── player_scraper.py      # Stats por jogador (VAZIO)
│   │   └── advanced_scraper.py    # xG, posse, pressão (VAZIO)
│   └── requirements.txt           # (VAZIO)
├── airflow/
│   ├── dags/
│   │   ├── dag_scrape_raw.py      # DAG ingestão bruta (VAZIO)
│   │   ├── dag_transform.py       # DAG transformação (VAZIO)
│   │   └── dag_analysis.py        # DAG análise (VAZIO)
│   ├── plugins/
│   └── logs/
├── db/
│   └── init/
│       ├── 01_raw_schema.sql      # Schema raw (VAZIO)
│       ├── 02_dwh_schema.sql      # Schema dim/fact (VAZIO)
│       └── 03_analytics_schema.sql # Schema analytics (VAZIO)
├── analysis/
│   ├── notebooks/
│   └── models/
├── docker-compose.yml             # PRONTO
├── .env                           # PRONTO (não vai pro git)
├── .env.example                   # PRONTO
├── .gitignore                     # PRONTO
└── README.md                      # PRONTO
```

## Containers Docker (todos rodando)
- brasileirao_postgres    → porta 5434
- brasileirao_pgadmin     → http://localhost:5050
- brasileirao_airflow_webserver → http://localhost:8080 (user: airflow / pass: airflow)
- brasileirao_airflow_scheduler → interno

## Credenciais locais
- Postgres: user=brasileirao / pass=brasileirao123 / db=brasileirao_db
- PgAdmin: admin@brasileirao.com / admin123
- Airflow: airflow / airflow

## Plano de commits
- [x] commit 1 — chore: initial project structure and .gitignore
- [x] commit 2 — infra: add docker-compose with postgres, airflow and pgadmin
- [ ] commit 3 — infra: add database init scripts (raw, dwh, analytics schemas)
- [ ] commit 4 — feat: add fbref match scraper (results and goals)
- [ ] commit 5 — feat: add fbref player stats scraper
- [ ] commit 6 — feat: add fbref advanced metrics scraper (xG, possession)
- [ ] commit 7 — feat: add airflow DAG for raw data ingestion
- [ ] commit 8 — feat: add airflow DAG for staging transformation
- [ ] commit 9 — feat: add airflow DAG for analytics pipeline
- [ ] commit 10 — docs: add README with architecture and setup guide

## Próximo passo
Commit 3 — criar os schemas SQL do PostgreSQL:
- 01_raw_schema.sql: tabelas brutas (raw_matches, raw_players, raw_advanced)
- 02_dwh_schema.sql: modelo estrela (dim_teams, dim_players, fact_matches, fact_stats)
- 03_analytics_schema.sql: tabelas de análise (analytics_xg, analytics_win_factors)

## Convenção de commits
- feat: nova funcionalidade
- infra: configuração de infraestrutura
- chore: setup inicial
- docs: documentação
- fix: correção
- refactor: refatoração
