import psycopg2
import logging
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pathlib import Path

# Carrega o .env da raiz do projeto
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────
# Configurações
# ─────────────────────────────────────────
HTML_PATH = Path(__file__).resolve().parents[1] / "data" / "raw_html" / "matches.html"

DB_CONFIG = {
    "host":     os.getenv("POSTGRES_HOST", "localhost"),
    "port":     os.getenv("POSTGRES_PORT", "5434"),
    "dbname":   os.getenv("POSTGRES_DB",   "brasileirao_db"),
    "user":     os.getenv("POSTGRES_USER", "brasileirao"),
    "password": os.getenv("POSTGRES_PASSWORD", "brasileirao123"),
}


# ─────────────────────────────────────────
# Conexão com o banco
# ─────────────────────────────────────────
def get_connection():
    return psycopg2.connect(**DB_CONFIG)


# ─────────────────────────────────────────
# Lê o HTML local
# ─────────────────────────────────────────
def load_page() -> BeautifulSoup:
    log.info(f"Lendo arquivo local: {HTML_PATH}")
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        return BeautifulSoup(f, "lxml")


# ─────────────────────────────────────────
# Parseia as partidas da tabela do FBref
# ─────────────────────────────────────────
def parse_matches(soup: BeautifulSoup) -> list:
    matches = []

    table = soup.find("table", {"id": "sched_2023_24_1"})
    if not table:
        log.error("Tabela de partidas não encontrada.")
        return matches

    rows = table.find("tbody").find_all("tr")
    log.info(f"Total de linhas encontradas: {len(rows)}")

    for row in rows:
        if row.get("class") and "spacer" in row.get("class"):
            continue
        if len(row.find_all(["td", "th"])) < 10:
            continue

        try:
            def get(data_stat):
                cell = row.find(attrs={"data-stat": data_stat})
                return cell.get_text(strip=True) if cell else None

            def get_href(data_stat):
                cell = row.find(attrs={"data-stat": data_stat})
                if cell:
                    a = cell.find("a")
                    return "https://fbref.com" + a["href"] if a else None
                return None

            score = get("score")
            if not score or score == "":
                continue

            home_goals, away_goals = None, None
            if "–" in score:
                parts      = score.split("–")
                home_goals = int(parts[0].strip())
                away_goals = int(parts[1].strip())

            attendance = get("attendance")
            home_xg    = get("home_xg")
            away_xg    = get("away_xg")

            matches.append({
                "season":     "2023",
                "round":      get("gameweek"),
                "match_date": get("date") or None,
                "home_team":  get("home_team"),
                "away_team":  get("away_team"),
                "home_goals": home_goals,
                "away_goals": away_goals,
                "home_xg":    float(home_xg) if home_xg else None,
                "away_xg":    float(away_xg) if away_xg else None,
                "venue":      get("venue"),
                "attendance": int(attendance.replace(",", "")) if attendance else None,
                "referee":    get("referee"),
                "match_url":  get_href("match_report"),
            })

        except Exception as e:
            log.warning(f"Erro ao parsear linha: {e}")
            continue

    log.info(f"Partidas parseadas: {len(matches)}")
    return matches


# ─────────────────────────────────────────
# Salva as partidas no banco
# ─────────────────────────────────────────
def save_matches(matches: list[dict]):
    conn = get_connection()
    cur  = conn.cursor()

    insert_sql = """
        INSERT INTO raw.matches (
            season, round, match_date, home_team, away_team,
            home_goals, away_goals, home_xg, away_xg,
            venue, attendance, referee, match_url
        ) VALUES (
            %(season)s, %(round)s, %(match_date)s, %(home_team)s, %(away_team)s,
            %(home_goals)s, %(away_goals)s, %(home_xg)s, %(away_xg)s,
            %(venue)s, %(attendance)s, %(referee)s, %(match_url)s
        )
        ON CONFLICT DO NOTHING;
    """

    saved = 0
    for match in matches:
        try:
            cur.execute(insert_sql, match)
            saved += 1
        except Exception as e:
            log.warning(f"Erro ao salvar partida: {e}")
            conn.rollback()
            continue

    conn.commit()
    cur.close()
    conn.close()
    log.info(f"Partidas salvas no banco: {saved}/{len(matches)}")


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────
def run():
    log.info("Iniciando scraping de partidas — Brasileirão 2023")
    soup    = load_page()
    matches = parse_matches(soup)
    if matches:
        save_matches(matches)
    log.info("Scraping finalizado.")


if __name__ == "__main__":
    run()
