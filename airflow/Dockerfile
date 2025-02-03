# 베이스 이미지
FROM python:3.10-slim

# 작업 디렉토리 설정
WORKDIR /app

# 의존성 파일 복사
COPY airflow/requirements.txt .

# 의존성 설치
RUN pip install --upgrade pip

# 필요한 시스템 패키지 설치
RUN apt-get update && apt-get install -y \
    pkg-config \
    libmariadb-dev


RUN pip install --no-cache-dir -r requirements.txt

# 프로젝트 파일 복사
COPY . .

# Airflow 실행
CMD ["airflow", "scheduler"]
