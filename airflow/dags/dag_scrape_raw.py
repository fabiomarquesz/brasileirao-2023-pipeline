from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.empty import EmptyOperator
import sys
import os

sys.path.insert(0, "/opt/airflow/scraping")

default_args = {
    "owner":            "brasileirao",
    "depends_on_past":  False,
    "retries":          1,
    "retry_delay":      timedelta(minutes=5),
    "email_on_failure": False,
    "email_on_retry":   False,
}

with DAG(
    dag_id="dag_scrape_raw",
    description="Scraping dos dados brutos do FBref — Brasileirão 2023",
    default_args=default_args,
    start_date=datetime(2024, 1, 1),
    schedule_interval=None,  # Manual — dados históricos
    catchup=False,
    tags=["scraping", "raw", "brasileirao"],
) as dag:

    start = EmptyOperator(task_id="start")
    end   = EmptyOperator(task_id="end")

    def run_match_scraper():
        from scrapers.match_scraper import run
        run()

    def run_player_scraper():
        from scrapers.player_scraper import run
        run()

    def run_advanced_scraper():
        from scrapers.advanced_scraper import run
        run()

    scrape_matches = PythonOperator(
        task_id="scrape_matches",
        python_callable=run_match_scraper,
    )

    scrape_players = PythonOperator(
        task_id="scrape_players",
        python_callable=run_player_scraper,
    )

    scrape_advanced = PythonOperator(
        task_id="scrape_advanced",
        python_callable=run_advanced_scraper,
    )

    start >> scrape_matches >> scrape_players >> scrape_advanced >> end
