# 베이스 이미지
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사
COPY airflow/requirements.txt .
COPY airflow/ /app/dags/
COPY airflow/models/book_mlops/main.py /app/dags/

# 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    pkg-config \
    libmariadb-dev \
    build-essential \
    default-libmysqlclient-dev \
    default-mysql-client \
    mariadb-client  # ← 추가

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install pytest

# 프로젝트 파일 복사
COPY . .

# 환경 변수에 따라 실행 모드 결정
CMD ["bash", "-c", "if [ \"$RUN_AIRFLOW\" != \"true\" ]; then pytest; else airflow scheduler; fi"]
