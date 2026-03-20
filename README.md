# Brasileirão 2023 — Data Pipeline

Pipeline de dados completo para análise estatística do Campeonato Brasileiro Série A 2023.
Coleta estatísticas do FBref, armazena no PostgreSQL via Docker, orquestra com Airflow
e analisa correlações entre métricas e vitórias/derrotas dos times.

## Arquitetura
```
FBref.com (HTML local)
       ↓
Scraping Service (Python + BeautifulSoup)
       ↓
Apache Airflow (Orquestração)
       ↓
PostgreSQL (Docker)
  ├── raw        → dados brutos
  ├── dwh        → modelo estrela (dim/fact)
  └── analytics  → métricas calculadas
       ↓
Análise e Modelagem (Pandas, Scikit-learn)
```

## Stack

| Camada | Tecnologia |
|---|---|
| Scraping | Python, BeautifulSoup |
| Orquestração | Apache Airflow 2.8.1 |
| Banco de dados | PostgreSQL 15 |
| Infraestrutura | Docker, Docker Compose |
| Análise | Pandas, Scikit-learn, Jupyter |

## Dados coletados

| Tabela | Registros | Descrição |
|---|---|---|
| raw.matches | 380 | Partidas com resultado e placar |
| raw.player_stats | 751 | Estatísticas por jogador na temporada |
| raw.advanced_stats | 20 | Métricas avançadas por time |

## Métricas disponíveis

- **Por partida:** resultado, gols, rodada, público, árbitro
- **Por jogador:** gols, assistências, minutos, passes, dribles, cartões
- **Por time:** posse, chutes, precisão, faltas, impedimentos, carries

## Como rodar

### Pré-requisitos
- Docker e Docker Compose instalados
- Python 3.12+
- Google Chrome

### 1. Clone o repositório
```bash
git clone https://github.com/SEU_USUARIO/brasileirao-2023-pipeline.git
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
> O FBref usa Cloudflare. Acesse cada URL no navegador,
> abra o DevTools (F12) → Console e execute:
> `copy(document.documentElement.outerHTML)`
> Salve o conteúdo em `scraping/data/raw_html/`

| Arquivo | URL |
|---|---|
| matches.html | https://fbref.com/en/comps/24/2023/schedule/2023-Serie-A-Scores-and-Fixtures |
| players.html | https://fbref.com/en/comps/24/2023/stats/2023-Serie-A-Stats |
| advanced.html | https://fbref.com/en/comps/24/2023/shooting/2023-Serie-A-Stats |
| possession.html | https://fbref.com/en/comps/24/2023/possession/2023-Serie-A-Stats |
| expected.html | https://fbref.com/en/comps/24/2023/expected/2023-Serie-A-Stats |

### 5. Ative o ambiente virtual e rode os scrapers
```bash
python3 -m venv scraping/venv
source scraping/venv/bin/activate
pip install -r scraping/requirements.txt

python scraping/scrapers/match_scraper.py
python scraping/scrapers/player_scraper.py
python scraping/scrapers/advanced_scraper.py
```

### 6. Configure a conexão no Airflow
Acesse http://localhost:8080 (airflow/airflow)
Admin → Connections → Adicionar:
- **Connection Id:** brasileirao_postgres
- **Connection Type:** Postgres
- **Host:** postgres
- **Database:** brasileirao_db
- **Login:** brasileirao
- **Password:** brasileirao123
- **Port:** 5432

### 7. Execute as DAGs em ordem
1. `dag_transform` → popula o DWH
2. `dag_analysis` → popula as tabelas de analytics

## Acessos

| Serviço | URL | Credenciais |
|---|---|---|
| Airflow | http://localhost:8080 | airflow / airflow |
| PgAdmin | http://localhost:5050 | admin@brasileirao.com / admin123 |

## Resultado — Classificação final 2023

| # | Time | Pontos | Vitórias | % Vitórias |
|---|---|---|---|---|
| 1 | Palmeiras | 70 | 20 | 52.6% |
| 2 | Grêmio | 68 | 21 | 55.3% |
| 3 | Atlético Mineiro | 66 | 19 | 50.0% |
| 4 | Flamengo | 66 | 19 | 50.0% |
| 5 | Botafogo | 64 | 18 | 47.4% |

## Próximos passos

- [ ] Análise exploratória (EDA) nos notebooks
- [ ] Modelo de predição de vitória/derrota
- [ ] Correlação entre métricas e resultado
- [ ] Dashboard de visualização
