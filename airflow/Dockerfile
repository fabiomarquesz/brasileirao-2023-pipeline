FROM apache/airflow:2.8.1

USER airflow

COPY ../scraping/requirements.txt /tmp/requirements.txt

RUN pip install --no-cache-dir \
    beautifulsoup4==4.12.3 \
    lxml==5.1.0 \
    psycopg2-binary==2.9.9 \
    python-dotenv==1.0.0
