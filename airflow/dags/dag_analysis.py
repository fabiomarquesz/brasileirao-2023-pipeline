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
# Funções de análise
# ─────────────────────────────────────────
def load_team_performance():
    hook = PostgresHook(postgres_conn_id="brasileirao_postgres")
    hook.run("""
        INSERT INTO analytics.team_performance (
            team_id, matches_played, wins, draws, losses,
            goals_scored, goals_conceded, goal_diff, points,
            win_rate, avg_xg_for, avg_xg_against,
            avg_possession, avg_ppda
        )
        SELECT
            dt.team_id,
            COUNT(DISTINCT fm.match_id)                                         AS matches_played,
            COUNT(DISTINCT CASE WHEN
                (fm.home_team_id = dt.team_id AND fm.result = 'HOME_WIN') OR
                (fm.away_team_id = dt.team_id AND fm.result = 'AWAY_WIN')
                THEN fm.match_id END)                                           AS wins,
            COUNT(DISTINCT CASE WHEN fm.result = 'DRAW'
                THEN fm.match_id END)                                           AS draws,
            COUNT(DISTINCT CASE WHEN
                (fm.home_team_id = dt.team_id AND fm.result = 'AWAY_WIN') OR
                (fm.away_team_id = dt.team_id AND fm.result = 'HOME_WIN')
                THEN fm.match_id END)                                           AS losses,
            SUM(CASE WHEN fm.home_team_id = dt.team_id THEN fm.home_goals
                     ELSE fm.away_goals END)                                    AS goals_scored,
            SUM(CASE WHEN fm.home_team_id = dt.team_id THEN fm.away_goals
                     ELSE fm.home_goals END)                                    AS goals_conceded,
            SUM(CASE WHEN fm.home_team_id = dt.team_id
                     THEN fm.home_goals - fm.away_goals
                     ELSE fm.away_goals - fm.home_goals END)                    AS goal_diff,
            SUM(CASE
                WHEN (fm.home_team_id = dt.team_id AND fm.result = 'HOME_WIN') OR
                     (fm.away_team_id = dt.team_id AND fm.result = 'AWAY_WIN') THEN 3
                WHEN fm.result = 'DRAW' THEN 1
                ELSE 0 END)                                                     AS points,
            ROUND(
                COUNT(DISTINCT CASE WHEN
                    (fm.home_team_id = dt.team_id AND fm.result = 'HOME_WIN') OR
                    (fm.away_team_id = dt.team_id AND fm.result = 'AWAY_WIN')
                    THEN fm.match_id END)::numeric /
                NULLIF(COUNT(DISTINCT fm.match_id), 0) * 100, 2
            )                                                                   AS win_rate,
            AVG(CASE WHEN fm.home_team_id = dt.team_id THEN fm.home_xg
                     ELSE fm.away_xg END)                                       AS avg_xg_for,
            AVG(CASE WHEN fm.home_team_id = dt.team_id THEN fm.away_xg
                     ELSE fm.home_xg END)                                       AS avg_xg_against,
            AVG(fas.possession)                                                 AS avg_possession,
            AVG(fas.ppda)                                                       AS avg_ppda
        FROM dwh.dim_teams dt
        JOIN dwh.fact_matches fm
            ON fm.home_team_id = dt.team_id OR fm.away_team_id = dt.team_id
        LEFT JOIN dwh.fact_advanced_stats fas
            ON fas.team_id = dt.team_id
        GROUP BY dt.team_id
        ON CONFLICT DO NOTHING;
    """)


def load_win_factors():
    hook = PostgresHook(postgres_conn_id="brasileirao_postgres")
    hook.run("""
        INSERT INTO analytics.win_factors (
            match_id, team_id, result,
            xg_diff, possession, shot_accuracy,
            ppda, corners, fouls, is_home
        )
        SELECT
            fm.match_id,
            dt.team_id,
            CASE
                WHEN (fm.home_team_id = dt.team_id AND fm.result = 'HOME_WIN') OR
                     (fm.away_team_id = dt.team_id AND fm.result = 'AWAY_WIN') THEN 'WIN'
                WHEN fm.result = 'DRAW' THEN 'DRAW'
                ELSE 'LOSS'
            END                                                     AS result,
            CASE WHEN fm.home_team_id = dt.team_id
                 THEN fm.home_xg - fm.away_xg
                 ELSE fm.away_xg - fm.home_xg END                   AS xg_diff,
            fas.possession,
            fas.shot_accuracy,
            fas.ppda,
            fas.corners,
            fas.fouls,
            fm.home_team_id = dt.team_id                            AS is_home
        FROM dwh.fact_matches fm
        JOIN dwh.dim_teams dt
            ON dt.team_id = fm.home_team_id OR dt.team_id = fm.away_team_id
        LEFT JOIN dwh.fact_advanced_stats fas
            ON fas.team_id = dt.team_id
        ON CONFLICT DO NOTHING;
    """)


def load_player_impact():
    hook = PostgresHook(postgres_conn_id="brasileirao_postgres")
    hook.run("""
        INSERT INTO analytics.player_impact (
            player_id, team_id, matches_played,
            goals, assists, goal_contributions,
            avg_pass_accuracy, avg_shot_accuracy,
            win_rate_when_plays, impact_score
        )
        SELECT
            dp.player_id,
            dp.team_id,
            COUNT(fps.stat_id)                                          AS matches_played,
            SUM(fps.goals)                                              AS goals,
            SUM(fps.assists)                                            AS assists,
            SUM(fps.goals) + SUM(fps.assists)                          AS goal_contributions,
            AVG(fps.pass_accuracy)                                      AS avg_pass_accuracy,
            AVG(CASE WHEN fps.shots > 0
                THEN fps.shots_on_target::numeric / fps.shots * 100
                ELSE NULL END)                                          AS avg_shot_accuracy,
            NULL                                                        AS win_rate_when_plays,
            -- Impact score: gols*3 + assists*2 + contribuições de passe
            ROUND(
                (SUM(fps.goals) * 3 +
                 SUM(fps.assists) * 2 +
                 COALESCE(AVG(fps.pass_accuracy), 0) * 0.1)::numeric
            , 2)                                                        AS impact_score
        FROM dwh.dim_players dp
        JOIN dwh.fact_player_stats fps ON fps.player_id = dp.player_id
        GROUP BY dp.player_id, dp.team_id
        ON CONFLICT DO NOTHING;
    """)


# ─────────────────────────────────────────
# DAG
# ─────────────────────────────────────────
with DAG(
    dag_id="dag_analysis",
    description="Popula tabelas de analytics com métricas calculadas",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,
    catchup=False,
    tags=["analysis", "analytics", "brasileirao"],
) as dag:

    start = EmptyOperator(task_id="start")
    end   = EmptyOperator(task_id="end")

    t_team_performance = PythonOperator(
        task_id="load_team_performance",
        python_callable=load_team_performance,
    )

    t_win_factors = PythonOperator(
        task_id="load_win_factors",
        python_callable=load_win_factors,
    )

    t_player_impact = PythonOperator(
        task_id="load_player_impact",
        python_callable=load_player_impact,
    )

    start >> t_team_performance >> t_win_factors >> t_player_impact >> end
