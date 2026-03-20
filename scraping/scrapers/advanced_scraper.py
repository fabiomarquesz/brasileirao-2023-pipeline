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
HTML_FILES = {
    "expected":  Path(__file__).resolve().parents[1] / "data" / "raw_html" / "expected.html",
    "shooting":  Path(__file__).resolve().parents[1] / "data" / "raw_html" / "advanced.html",
    "possession": Path(__file__).resolve().parents[1] / "data" / "raw_html" / "possession.html",
}

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
# Lê um HTML local
# ─────────────────────────────────────────
def load_page(path: Path) -> BeautifulSoup:
    log.info(f"Lendo: {path.name}")
    with open(path, "r", encoding="utf-8") as f:
        return BeautifulSoup(f, "lxml")


# ─────────────────────────────────────────
# Parseia tabela genérica por time
# ─────────────────────────────────────────
def parse_team_table(soup: BeautifulSoup, table_id: str) -> dict:
    result = {}
    table  = soup.find("table", {"id": table_id})
    if not table:
        log.warning(f"Tabela {table_id} não encontrada.")
        return result

    rows = table.find("tbody").find_all("tr")
    for row in rows:
        if row.get("class") and "thead" in row.get("class"):
            continue

        def get(stat):
            cell = row.find(attrs={"data-stat": stat})
            return cell.get_text(strip=True) if cell else None

        team = get("team")
        if not team:
            continue

        result[team] = row
    return result


# ─────────────────────────────────────────
# Coleta e combina métricas avançadas por time
# ─────────────────────────────────────────
def parse_advanced_stats(soups: dict) -> list[dict]:
    stats = []

    # Tabelas por fonte
    standard  = parse_team_table(soups["expected"],   "stats_squads_standard_for")
    shooting  = parse_team_table(soups["shooting"],   "stats_squads_shooting_for")
    misc      = parse_team_table(soups["expected"],   "stats_squads_misc_for")
    possession_tbl = parse_team_table(soups["possession"], "stats_squads_possession_for")

    all_teams = set(standard.keys()) | set(shooting.keys())
    log.info(f"Times encontrados: {len(all_teams)}")

    for team in sorted(all_teams):
        try:
            def get_from(row, stat):
                if row is None:
                    return None
                cell = row.find(attrs={"data-stat": stat})
                return cell.get_text(strip=True) if cell else None

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

            std_row  = standard.get(team)
            sht_row  = shooting.get(team)
            msc_row  = misc.get(team)
            pos_row  = possession_tbl.get(team)

            stats.append({
                "match_url":          None,
                "team":               team,
                "is_home":            None,
                # Posse e standard
                "possession":         to_float(get_from(std_row, "possession")),
                "xg":                 None,  # FBref não disponibiliza xG para Série A
                "xg_against":         None,
                # Chutes
                "shots":              to_int(get_from(sht_row, "shots")),
                "shots_on_target":    to_int(get_from(sht_row, "shots_on_target")),
                # Métricas avançadas de posse
                "deep_completions":   to_int(get_from(pos_row, "carries_into_final_third")),
                "ppda":               None,  # Não disponível diretamente no FBref
                # Misc
                "corners":            None,
                "fouls":              to_int(get_from(msc_row, "fouls")),
                "offsides":           to_int(get_from(msc_row, "offsides")),
            })

        except Exception as e:
            log.warning(f"Erro ao parsear time {team}: {e}")
            continue

    log.info(f"Times parseados: {len(stats)}")
    return stats


# ─────────────────────────────────────────
# Salva no banco
# ─────────────────────────────────────────
def save_advanced_stats(stats: list[dict]):
    conn = get_connection()
    cur  = conn.cursor()

    insert_sql = """
        INSERT INTO raw.advanced_stats (
            match_url, team, is_home,
            possession, xg, xg_against,
            shots, shots_on_target,
            deep_completions, ppda,
            corners, fouls, offsides
        ) VALUES (
            %(match_url)s, %(team)s, %(is_home)s,
            %(possession)s, %(xg)s, %(xg_against)s,
            %(shots)s, %(shots_on_target)s,
            %(deep_completions)s, %(ppda)s,
            %(corners)s, %(fouls)s, %(offsides)s
        )
        ON CONFLICT DO NOTHING;
    """

    saved = 0
    for stat in stats:
        try:
            cur.execute(insert_sql, stat)
            saved += 1
        except Exception as e:
            log.warning(f"Erro ao salvar {stat.get('team')}: {e}")
            conn.rollback()
            continue

    conn.commit()
    cur.close()
    conn.close()
    log.info(f"Stats avançadas salvas: {saved}/{len(stats)}")


# ─────────────────────────────────────────
# Main
# ─────────────────────────────────────────
def run():
    log.info("Iniciando scraping de métricas avançadas — Brasileirão 2023")

    soups = {key: load_page(path) for key, path in HTML_FILES.items()}
    stats = parse_advanced_stats(soups)

    if stats:
        save_advanced_stats(stats)

    log.info("Scraping de métricas avançadas finalizado.")


if __name__ == "__main__":
    run()
