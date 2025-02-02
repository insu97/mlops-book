FROM apache/airflow:2.10.4
# Dockerfile 수정
COPY /airflow/requirements.txt /airflow/
RUN pip install --no-cache-dir "apache-airflow==2.10.4" -r /airflow/requirements.txt
