FROM apache/airflow:2.7.1

USER root

# 시스템 패키지 설치
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

USER airflow

# 프로젝트 의존성 설치
COPY requirements.txt /opt/airflow/requirements.txt
RUN pip install --no-cache-dir -r /opt/airflow/requirements.txt

# DAG 및 기타 필요한 파일 복사
COPY dags /opt/airflow/dags
COPY plugins /opt/airflow/plugins
COPY config /opt/airflow/config

# 환경 변수 설정
ENV AIRFLOW__CORE__LOAD_EXAMPLES=False
