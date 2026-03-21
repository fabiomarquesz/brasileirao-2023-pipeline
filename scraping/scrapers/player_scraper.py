import psycopg2
import logging
import os
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

# ─────────────────────────────────────────
# Configurações
# ─────────────────────────────────────────
HTML_PATH = Path(__file__).resolve().parents[1] / "data" / "raw_html" / "players.html"

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
# Parseia os jogadores da tabela do FBref
# ─────────────────────────────────────────
def parse_players(soup: BeautifulSoup) -> list:
    players = []

    table = soup.find("table", {"id": "stats_standard"})
    if not table:
        log.error("Tabela stats_standard não encontrada.")
        return players

    rows = table.find("tbody").find_all("tr")
    log.info(f"Total de linhas encontradas: {len(rows)}")

    for row in rows:
        # Pula linhas de separação
        if row.get("class") and "thead" in row.get("class"):
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

            player_name = get("player")
            if not player_name:
                continue

            def to_int(val):
                try:
                    return int(val) if val and val != "" else None
                except:
                    return None

            def to_float(val):
                try:
                    return float(val) if val and val != "" else None
                except:
                    return None

            minutes     = get("minutes_90s")
            min_played  = None
            if minutes:
                try:
                    min_played = int(float(minutes) * 90)
                except:
                    pass

            passes_pct  = get("passes_pct")
            dribbles    = get("dribbles_completed")
            dribbles_att= get("dribbles")

            players.append({
                "match_url":           None,
                "team":                get("team"),
                "player_name":         player_name,
                "position":            get("position"),
                "minutes_played":      min_played,
                "goals":               to_int(get("goals")),
                "assists":             to_int(get("assists")),
                "shots":               to_int(get("shots")),
                "shots_on_target":     to_int(get("shots_on_target")),
                "passes_completed":    to_int(get("passes_completed")),
                "passes_attempted":    to_int(get("passes")),
                "pass_accuracy":       to_float(passes_pct),
                "dribbles_completed":  to_int(dribbles),
                "dribbles_attempted":  to_int(dribbles_att),
                "yellow_cards":        to_int(get("cards_yellow")),
                "red_cards":           to_int(get("cards_red")),
            })

        except Exception as e:
            log.warning(f"Erro ao parsear jogador: {e}")
            continue

    log.info(f"Jogadores parseados: {len(players)}")
    return players


# ─────────────────────────────────────────
# Salva os jogadores no banco
# ─────────────────────────────────────────
def save_players(players: list[dict]):
    conn = get_connection()
    cur  = conn.cursor()

    insert_sql = """
        INSERT INTO raw.player_stats (
            match_url, team, player_name, position,
            minutes_played, goals, assists,
            shots, shots_on_target,
            passes_completed, passes_attempted, pass_accuracy,
            dribbles_completed, dribbles_attempted,
            yellow_cards, red_cards
        ) VALUES (
            %(match_url)s, %(team)s, %(player_name)s, %(position)s,
            %(minutes_played)s, %(goals)s, %(assists)s,
            %(shots)s, %(shots_on_target)s,
            %(passes_completed)s, %(passes_attempted)s, %(pass_accuracy)s,
            %(dribbles_completed)s, %(dribbles_attempted)s,
            %(yellow_cards)s, %(red_cards)s
        )
        ON CONFLICT DO NOTHING;
    """

    saved = 0
    for player in players:
        try:
            cur.execute(insert_sql, player)
            saved += 1
        except Exception as e:
            log.warning(f"Erro ao salvar jogador {player.get('player_name')}: {e}")
            conn.rollback()
            continue

    conn.commit()
    cur.close()
    conn.close()
    log.info(f"Jogadores salvos no banco: {saved}/{len(players)}")


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────
def run():
    log.info("Iniciando scraping de jogadores — Brasileirão 2023")
    soup    = load_page()
    players = parse_players(soup)
    if players:
        save_players(players)
    log.info("Scraping de jogadores finalizado.")


if __name__ == "__main__":
    run()
