FROM apache/airflow:2.10.4
COPY airflow/requirements.txt /
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r airflow/requirements.txt
