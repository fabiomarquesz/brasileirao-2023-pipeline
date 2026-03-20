from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook

default_args = {
    "owner":            "brasileirao",
    "depends_on_past":  False,
    "retries":          1,
    "retry_delay":      timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry":   False,
}


# ─────────────────────────────────────────
# Funções de transformação
# ─────────────────────────────────────────
def load_dim_teams():
    hook = PostgresHook(postgres_conn_id="brasileirao_postgres")
    hook.run("""
        INSERT INTO dwh.dim_teams (team_name)
        SELECT DISTINCT home_team FROM raw.matches
        UNION
        SELECT DISTINCT away_team FROM raw.matches
        ON CONFLICT (team_name) DO NOTHING;
    """)


def load_dim_players():
    hook = PostgresHook(postgres_conn_id="brasileirao_postgres")
    hook.run("""
        INSERT INTO dwh.dim_players (player_name, team_id, position)
        SELECT DISTINCT
            ps.player_name,
            dt.team_id,
            ps.position
        FROM raw.player_stats ps
        LEFT JOIN dwh.dim_teams dt ON dt.team_name = ps.team
        ON CONFLICT DO NOTHING;
    """)


def load_dim_date():
    hook = PostgresHook(postgres_conn_id="brasileirao_postgres")
    hook.run("""
        INSERT INTO dwh.dim_date (
            full_date, day, month, year, quarter,
            day_of_week, day_name, is_weekend
        )
        SELECT DISTINCT
            match_date::date,
            EXTRACT(DAY   FROM match_date::date)::int,
            EXTRACT(MONTH FROM match_date::date)::int,
            EXTRACT(YEAR  FROM match_date::date)::int,
            EXTRACT(QUARTER FROM match_date::date)::int,
            EXTRACT(DOW   FROM match_date::date)::int,
            TO_CHAR(match_date::date, 'Day'),
            EXTRACT(DOW FROM match_date::date) IN (0, 6)
        FROM raw.matches
        WHERE match_date IS NOT NULL
        ON CONFLICT (full_date) DO NOTHING;
    """)


def load_fact_matches():
    hook = PostgresHook(postgres_conn_id="brasileirao_postgres")
    hook.run("""
        INSERT INTO dwh.fact_matches (
            date_id, home_team_id, away_team_id,
            round, home_goals, away_goals,
            home_xg, away_xg, result,
            venue, attendance, referee, match_url
        )
        SELECT
            dd.date_id,
            ht.team_id,
            at.team_id,
            rm.round,
            rm.home_goals,
            rm.away_goals,
            rm.home_xg,
            rm.away_xg,
            CASE
                WHEN rm.home_goals > rm.away_goals THEN 'HOME_WIN'
                WHEN rm.home_goals < rm.away_goals THEN 'AWAY_WIN'
                ELSE 'DRAW'
            END,
            rm.venue,
            rm.attendance,
            rm.referee,
            rm.match_url
        FROM raw.matches rm
        JOIN dwh.dim_date  dd ON dd.full_date = rm.match_date::date
        JOIN dwh.dim_teams ht ON ht.team_name = rm.home_team
        JOIN dwh.dim_teams at ON at.team_name = rm.away_team
        WHERE rm.home_goals IS NOT NULL
        ON CONFLICT DO NOTHING;
    """)


def load_fact_player_stats():
    hook = PostgresHook(postgres_conn_id="brasileirao_postgres")
    hook.run("""
        INSERT INTO dwh.fact_player_stats (
            player_id, team_id,
            minutes_played, goals, assists,
            shots, shots_on_target,
            passes_completed, passes_attempted, pass_accuracy,
            dribbles_completed, dribbles_attempted,
            yellow_cards, red_cards
        )
        SELECT
            dp.player_id,
            dt.team_id,
            ps.minutes_played,
            ps.goals,
            ps.assists,
            ps.shots,
            ps.shots_on_target,
            ps.passes_completed,
            ps.passes_attempted,
            ps.pass_accuracy,
            ps.dribbles_completed,
            ps.dribbles_attempted,
            ps.yellow_cards,
            ps.red_cards
        FROM raw.player_stats ps
        JOIN dwh.dim_players dp ON dp.player_name = ps.player_name
        JOIN dwh.dim_teams   dt ON dt.team_name   = ps.team
        ON CONFLICT DO NOTHING;
    """)


def load_fact_advanced_stats():
    hook = PostgresHook(postgres_conn_id="brasileirao_postgres")
    hook.run("""
        INSERT INTO dwh.fact_advanced_stats (
            team_id, is_home,
            possession, xg, xg_against, xg_diff,
            shots, shots_on_target, shot_accuracy,
            deep_completions, ppda,
            corners, fouls, offsides
        )
        SELECT
            dt.team_id,
            adv.is_home,
            adv.possession,
            adv.xg,
            adv.xg_against,
            CASE
                WHEN adv.xg IS NOT NULL AND adv.xg_against IS NOT NULL
                THEN adv.xg - adv.xg_against
                ELSE NULL
            END,
            adv.shots,
            adv.shots_on_target,
            CASE
                WHEN adv.shots > 0
                THEN ROUND((adv.shots_on_target::numeric / adv.shots) * 100, 2)
                ELSE NULL
            END,
            adv.deep_completions,
            adv.ppda,
            adv.corners,
            adv.fouls,
            adv.offsides
        FROM raw.advanced_stats adv
        JOIN dwh.dim_teams dt ON dt.team_name = adv.team
        ON CONFLICT DO NOTHING;
    """)


# ─────────────────────────────────────────
# DAG
# ─────────────────────────────────────────
with DAG(
    dag_id="dag_transform",
    description="Transforma dados raw para o DWH (dim/fact tables)",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["transform", "dwh", "brasileirao"],
) as dag:

    start = EmptyOperator(task_id="start")
    end   = EmptyOperator(task_id="end")

    t_dim_teams = PythonOperator(
        task_id="load_dim_teams",
        python_callable=load_dim_teams,
    )

    t_dim_players = PythonOperator(
        task_id="load_dim_players",
        python_callable=load_dim_players,
    )

    t_dim_date = PythonOperator(
        task_id="load_dim_date",
        python_callable=load_dim_date,
    )

    t_fact_matches = PythonOperator(
        task_id="load_fact_matches",
        python_callable=load_fact_matches,
    )

    t_fact_players = PythonOperator(
        task_id="load_fact_player_stats",
        python_callable=load_fact_player_stats,
    )

    t_fact_advanced = PythonOperator(
        task_id="load_fact_advanced_stats",
        python_callable=load_fact_advanced_stats,
    )

    start >> [t_dim_teams, t_dim_date] >> t_dim_players
    t_dim_players >> t_fact_matches >> t_fact_players >> t_fact_advanced >> end
