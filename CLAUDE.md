# CLAUDE.md — Contexto do Projeto

## Objetivo
Pipeline de dados completo para análise estatística do Campeonato Brasileiro Série A 2023.
Coletar estatísticas do FBref, armazenar no PostgreSQL via Docker, orquestrar com Airflow
e analisar correlações entre métricas e vitórias/derrotas dos times.

## Stack
- Scraping: Python + BeautifulSoup (fonte: FBref.com — HTML local)
- Orquestração: Apache Airflow 2.8.1
- Banco de dados: PostgreSQL 15 (porta 5434)
- Infra: Docker Compose
- Análise: Pandas, Scikit-learn, Jupyter

## Importante — FBref e Cloudflare
O FBref bloqueia requests automáticos via Cloudflare (403).
Solução adotada: baixar o HTML via DevTools (copy(document.documentElement.outerHTML))
e parsear localmente. HTMLs ficam em scraping/data/raw_html/ (não versionados no git).

## HTMLs necessários (já baixados)
- matches.html    → https://fbref.com/en/comps/24/2023/schedule/2023-Serie-A-Scores-and-Fixtures
- players.html    → https://fbref.com/en/comps/24/2023/stats/2023-Serie-A-Stats
- advanced.html   → https://fbref.com/en/comps/24/2023/shooting/2023-Serie-A-Stats
- possession.html → https://fbref.com/en/comps/24/2023/possession/2023-Serie-A-Stats
- expected.html   → https://fbref.com/en/comps/24/2023/expected/2023-Serie-A-Stats

## Estrutura do projeto
```
brasileirao-2023-pipeline/
├── scraping/
│   ├── scrapers/
│   │   ├── match_scraper.py       # PRONTO — 380 partidas
│   │   ├── player_scraper.py      # PRONTO — 751 jogadores
│   │   └── advanced_scraper.py    # PRONTO — 20 times
│   ├── data/
│   │   └── raw_html/              # HTMLs baixados manualmente (não no git)
│   ├── requirements.txt           # PRONTO
│   └── venv/                      # Ambiente virtual (não vai pro git)
├── airflow/
│   ├── dags/
│   │   ├── dag_scrape_raw.py      # PRONTO
│   │   ├── dag_transform.py       # PRONTO — executado com sucesso
│   │   └── dag_analysis.py        # PRONTO — executado com sucesso
│   ├── plugins/
│   └── logs/
├── db/
│   └── init/
│       ├── 01_raw_schema.sql      # PRONTO
│       ├── 02_dwh_schema.sql      # PRONTO
│       └── 03_analytics_schema.sql # PRONTO
├── analysis/
│   ├── notebooks/                 # PRÓXIMO PASSO
│   └── models/
├── docker-compose.yml             # PRONTO
├── .env                           # PRONTO (não vai pro git)
├── .env.example                   # PRONTO
├── .gitignore                     # PRONTO
└── README.md                      # PRONTO
```

## Containers Docker
- brasileirao_postgres         → porta 5434
- brasileirao_pgadmin          → http://localhost:5050
- brasileirao_airflow_webserver → http://localhost:8080 (user: airflow / pass: airflow)
- brasileirao_airflow_scheduler → interno

## Credenciais locais
- Postgres: user=brasileirao / pass=brasileirao123 / db=brasileirao_db / porta=5434
- PgAdmin: admin@brasileirao.com / admin123
- Airflow: airflow / airflow
- Conexão Airflow→Postgres: Connection Id=brasileirao_postgres, Host=postgres, Port=5432

## Dados no banco
- raw.matches:              380 partidas ✅
- raw.player_stats:         751 jogadores ✅
- raw.advanced_stats:       20 times ✅
- dwh.dim_teams:            20 times ✅
- dwh.dim_players:          populado ✅
- dwh.dim_date:             populado ✅
- dwh.fact_matches:         populado ✅
- dwh.fact_player_stats:    populado ✅
- dwh.fact_advanced_stats:  populado ✅
- analytics.team_performance: populado ✅
- analytics.win_factors:    populado ✅
- analytics.player_impact:  populado ✅

## Como ativar o ambiente virtual
```bash
cd ~/Documentos/brasileirao-2023-pipeline
source scraping/venv/bin/activate
```

## Como rodar os scrapers
```bash
source scraping/venv/bin/activate
python scraping/scrapers/match_scraper.py
python scraping/scrapers/player_scraper.py
python scraping/scrapers/advanced_scraper.py
```

## Como rodar as DAGs
1. Acesse http://localhost:8080
2. Execute em ordem: dag_transform → dag_analysis

## Plano de commits
- [x] commit 1  — chore: initial project structure and .gitignore
- [x] commit 2  — infra: add docker-compose with postgres, airflow and pgadmin
- [x] commit 3  — infra: add database init scripts (raw, dwh, analytics schemas)
- [x] commit 4  — feat: add fbref match scraper (results and goals)
- [x] commit 5  — feat: add fbref player stats scraper
- [x] commit 6  — feat: add fbref advanced metrics scraper (possession, shooting, misc)
- [x] commit 7  — feat: add airflow DAGs for scraping, transformation and analysis pipeline
- [x] commit 8  — docs: add README with architecture and setup guide
- [ ] commit 9  — feat: add EDA notebook (análise exploratória)
- [ ] commit 10 — feat: add win prediction model

## Próximo passo
Criar notebooks de análise exploratória em analysis/notebooks/:
- 01_eda_matches.ipynb      → análise das partidas
- 02_eda_players.ipynb      → análise dos jogadores
- 03_correlations.ipynb     → correlações entre métricas e vitória
- 04_win_prediction.ipynb   → modelo de predição

## Convenção de commits
- feat: nova funcionalidade
- infra: configuração de infraestrutura
- chore: setup inicial
- docs: documentação
- fix: correção
- refactor: refatoração
