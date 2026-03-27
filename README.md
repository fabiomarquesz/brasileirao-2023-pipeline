# ⚽ Brasileirão 2023 — Data Pipeline

Pipeline de dados completo para análise estatística do Campeonato Brasileiro Série A 2023. O projeto coleta dados do FBref, armazena no PostgreSQL via Docker, orquestra com Apache Airflow e analisa correlações entre métricas e resultados dos times.

---

## 📊 Insights encontrados

- Times mandantes vencem **46.8%** das partidas
- Saldo de gols é o maior preditor de pontos (**r=0.94**)
- Chutes no alvo têm mais impacto que chutes totais (**r=0.63 vs r=0.42**)
- Posse de bola tem correlação moderada com pontos (**r=0.54**)
- Média de **2.49 gols** por partida na temporada

---

## 🏗️ Arquitetura
```
FBref.com (HTML local)
       ↓
Scraping Service (Python + BeautifulSoup)
       ↓
Apache Airflow (Orquestração)
       ↓
PostgreSQL 15 (Docker)
  ├── raw        → dados brutos
  ├── dwh        → modelo estrela (dim/fact)
  └── analytics  → métricas calculadas
       ↓
Análise (Pandas, Matplotlib, Seaborn, JupyterLab)
```

---

## 🛠️ Stack

| Camada | Tecnologia |
|---|---|
| Scraping | Python, BeautifulSoup |
| Orquestração | Apache Airflow 2.8.1 |
| Banco de dados | PostgreSQL 15 |
| Infraestrutura | Docker, Docker Compose |
| Análise | Pandas, Matplotlib, Seaborn, Scikit-learn |
| Notebook | JupyterLab |

---

## 📁 Estrutura do projeto
```
brasileirao-2023-pipeline/
├── scraping/
│   ├── scrapers/
│   │   ├── match_scraper.py       # Partidas — 380 registros
│   │   ├── player_scraper.py      # Jogadores — 751 registros
│   │   └── advanced_scraper.py    # Métricas avançadas — 20 times
│   ├── data/raw_html/             # HTMLs do FBref (não versionados)
│   └── requirements.txt
├── airflow/
│   ├── dags/
│   │   ├── dag_scrape_raw.py      # Orquestra os 3 scrapers
│   │   ├── dag_transform.py       # raw → dwh (dim/fact tables)
│   │   └── dag_analysis.py        # dwh → analytics
│   └── Dockerfile
├── db/
│   └── init/
│       ├── 01_raw_schema.sql
│       ├── 02_dwh_schema.sql
│       └── 03_analytics_schema.sql
├── analysis/
│   └── notebooks/
│       └── 01_eda_matches.ipynb
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🗄️ Modelo de dados

### Schema RAW — dados brutos
| Tabela | Descrição | Registros |
|---|---|---|
| raw.matches | Partidas com resultado e placar | 380 |
| raw.player_stats | Estatísticas por jogador | 751 |
| raw.advanced_stats | Métricas avançadas por time | 20 |

### Schema DWH — modelo estrela
| Tabela | Descrição |
|---|---|
| dwh.dim_teams | Dimensão times |
| dwh.dim_players | Dimensão jogadores |
| dwh.dim_date | Dimensão datas |
| dwh.fact_matches | Fato partidas |
| dwh.fact_player_stats | Fato estatísticas jogadores |
| dwh.fact_advanced_stats | Fato métricas avançadas |

### Schema ANALYTICS — métricas calculadas
| Tabela | Descrição |
|---|---|
| analytics.team_performance | Desempenho geral por time |
| analytics.win_factors | Fatores de vitória por partida |
| analytics.player_impact | Impacto dos jogadores |

---

## 🚀 Como rodar

### Pré-requisitos
- Docker e Docker Compose
- Python 3.12+
- Google Chrome

### 1. Clone o repositório
```bash
git clone https://github.com/fabiomarquesz/brasileirao-2023-pipeline.git
cd brasileirao-2023-pipeline
```

### 2. Configure as variáveis de ambiente
```bash
cp .env.example .env
# Edite o .env com suas configurações
```

### 3. Suba a infraestrutura
```bash
docker compose up -d
```

### 4. Baixe os HTMLs do FBref manualmente
> O FBref usa Cloudflare que bloqueia requests automáticos.
> Acesse cada URL no navegador, abra o DevTools (F12) → Console e execute:
> `copy(document.documentElement.outerHTML)`
> Salve o conteúdo em `scraping/data/raw_html/`

| Arquivo | URL |
|---|---|
| matches.html | https://fbref.com/en/comps/24/2023/schedule/2023-Serie-A-Scores-and-Fixtures |
| players.html | https://fbref.com/en/comps/24/2023/stats/2023-Serie-A-Stats |
| advanced.html | https://fbref.com/en/comps/24/2023/shooting/2023-Serie-A-Stats |
| possession.html | https://fbref.com/en/comps/24/2023/possession/2023-Serie-A-Stats |
| expected.html | https://fbref.com/en/comps/24/2023/expected/2023-Serie-A-Stats |

### 5. Crie o ambiente virtual e instale as dependências
```bash
python3 -m venv scraping/venv
source scraping/venv/bin/activate
pip install -r scraping/requirements.txt
pip install jupyterlab
```

### 6. Configure a conexão no Airflow
Acesse http://localhost:8080 (airflow / airflow)
Admin → Connections → Adicionar:

| Campo | Valor |
|---|---|
| Connection Id | brasileirao_postgres |
| Connection Type | Postgres |
| Host | postgres |
| Database | brasileirao_db |
| Login | brasileirao |
| Password | brasileirao123 |
| Port | 5432 |

### 7. Execute as DAGs em ordem
```
dag_scrape_raw  → coleta os dados brutos
dag_transform   → popula o modelo estrela
dag_analysis    → calcula métricas de analytics
```

### 8. Rode os notebooks
```bash
source scraping/venv/bin/activate
jupyter lab analysis/notebooks/
```

---

## 🌐 Acessos

| Serviço | URL | Credenciais |
|---|---|---|
| Airflow | http://localhost:8080 | airflow / airflow |
| PgAdmin | http://localhost:5050 | admin@brasileirao.com / admin123 |
| JupyterLab | http://localhost:8888 | — |

---

## 🏆 Classificação final 2023

| # | Time | Pts | V | E | D | Gols | % Vitórias |
|---|---|---|---|---|---|---|---|
| 1 | Palmeiras | 70 | 20 | 10 | 8 | 64 | 52.6% |
| 2 | Grêmio | 68 | 21 | 5 | 12 | 63 | 55.3% |
| 3 | Atlético Mineiro | 66 | 19 | 9 | 10 | 52 | 50.0% |
| 4 | Flamengo | 66 | 19 | 9 | 10 | 56 | 50.0% |
| 5 | Botafogo | 64 | 18 | 10 | 10 | 58 | 47.4% |

---

## 🔮 Próximos passos

- [ ] Modelo de machine learning para predição de resultados
- [ ] Análise de jogadores por posição
- [ ] Dashboard interativo com Metabase ou Streamlit
- [ ] Expandir para outras temporadas

---

## 👤 Autor

**Fabio Marques** — [@fabiomarquesz](https://github.com/fabiomarquesz)
