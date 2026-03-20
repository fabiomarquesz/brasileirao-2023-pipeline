# CLAUDE.md — Contexto do Projeto

## Objetivo
Pipeline de dados completo para análise estatística do Campeonato Brasileiro Série A 2023.
Coletar estatísticas do FBref, armazenar no PostgreSQL via Docker, orquestrar com Airflow
e analisar correlações entre métricas e vitórias/derrotas dos times.

## Stack
- Scraping: Python + BeautifulSoup + soccerdata (fonte: FBref.com — HTML local)
- Orquestração: Apache Airflow 2.8.1
- Banco de dados: PostgreSQL 15 (porta 5434)
- Infra: Docker Compose
- Análise: Pandas, Scikit-learn, Jupyter

## Importante — FBref e Cloudflare
O FBref bloqueia requests automáticos via Cloudflare (403).
Solução adotada: baixar o HTML manualmente no navegador e parsear localmente.
HTMLs ficam em scraping/data/raw_html/ (não versionados no git).

## Estrutura do projeto
```
brasileirao-2023-pipeline/
├── scraping/
│   ├── scrapers/
│   │   ├── match_scraper.py       # PRONTO — lê matches.html local
│   │   ├── player_scraper.py      # VAZIO
│   │   └── advanced_scraper.py    # VAZIO
│   ├── data/
│   │   └── raw_html/
│   │       └── matches.html       # HTML baixado manualmente do FBref
│   ├── requirements.txt           # PRONTO
│   └── venv/                      # Ambiente virtual (não vai pro git)
├── airflow/
│   ├── dags/
│   │   ├── dag_scrape_raw.py      # VAZIO
│   │   ├── dag_transform.py       # VAZIO
│   │   └── dag_analysis.py        # VAZIO
│   ├── plugins/
│   └── logs/
├── db/
│   └── init/
│       ├── 01_raw_schema.sql      # PRONTO
│       ├── 02_dwh_schema.sql      # PRONTO
│       └── 03_analytics_schema.sql # PRONTO
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
- brasileirao_postgres       → porta 5434
- brasileirao_pgadmin        → http://localhost:5050
- brasileirao_airflow_webserver → http://localhost:8080 (user: airflow / pass: airflow)
- brasileirao_airflow_scheduler → interno

## Credenciais locais
- Postgres: user=brasileirao / pass=brasileirao123 / db=brasileirao_db / porta=5434
- PgAdmin: admin@brasileirao.com / admin123
- Airflow: airflow / airflow

## Dados no banco
- raw.matches: 380 partidas do Brasileirão 2023 ✅
- raw.player_stats: vazio (próximo passo)
- raw.advanced_stats: vazio (próximo passo)
- Observação: home_xg e away_xg estão vazios — FBref não exibe xG na tabela
  de resultados. Serão coletados via páginas individuais de cada partida.

## HTMLs necessários (baixar manualmente no navegador)
- matches.html → https://fbref.com/en/comps/24/2023/schedule/2023-Serie-A-Scores-and-Fixtures
- players.html → https://fbref.com/en/comps/24/2023/stats/2023-Serie-A-Stats (a baixar)
- advanced.html → https://fbref.com/en/comps/24/2023/shooting/2023-Serie-A-Stats (a baixar)

## Como ativar o ambiente virtual
```bash
cd ~/Documentos/brasileirao-2023-pipeline
source scraping/venv/bin/activate
```

## Plano de commits
- [x] commit 1 — chore: initial project structure and .gitignore
- [x] commit 2 — infra: add docker-compose with postgres, airflow and pgadmin
- [x] commit 3 — infra: add database init scripts (raw, dwh, analytics schemas)
- [x] commit 4 — feat: add fbref match scraper (results and goals)
- [ ] commit 5 — feat: add fbref player stats scraper
- [ ] commit 6 — feat: add fbref advanced metrics scraper (xG, possession)
- [ ] commit 7 — feat: add airflow DAG for raw data ingestion
- [ ] commit 8 — feat: add airflow DAG for staging transformation
- [ ] commit 9 — feat: add airflow DAG for analytics pipeline
- [ ] commit 10 — docs: add README with architecture and setup guide

## Próximo passo
Commit 5 — player_scraper.py
Baixar manualmente: https://fbref.com/en/comps/24/2023/stats/2023-Serie-A-Stats
Salvar como scraping/data/raw_html/players.html
Parsear estatísticas por jogador e salvar em raw.player_stats

## Convenção de commits
- feat: nova funcionalidade
- infra: configuração de infraestrutura
- chore: setup inicial
- docs: documentação
- fix: correção
- refactor: refatoração
