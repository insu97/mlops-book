from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
import joblib
import os

from models.book_mlops.support.model.model_version import ModelVersion
from models.book_mlops.support.model.repository.model_logger_repository import ModelLoggerRepository

from airflow.models import Variable

airflow_dags_path = Variable.get('AIRFLOW_DAGS_PATH')
feature_store_url = os.getenv('FEATURE_STORE_URL', "mysql+pymysql://root:root@localhost/book_db")
model_logger = ModelLoggerRepository()


def new_model_create(**kwargs):
    ti = kwargs['ti']
    df_json = ti.xcom_pull(key='db', task_ids='db_update')
    df = pd.read_json(df_json)

    book_descriptions = df["description"].fillna("")

    # TF-IDF 벡터화
    tfidf_vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
    tfidf_matrix = tfidf_vectorizer.fit_transform(book_descriptions)

    # KMeans 클러스터링
    num_clusters = max(min(len(df) // 10, 20), 1)
    kmeans = MiniBatchKMeans(n_clusters=num_clusters, random_state=42)
    kmeans.fit(tfidf_matrix)

    # 모델 버전 관리
    model_version = ModelVersion("book_recommend")
    next_version = model_version.get_next_ct_model_version()

    # ✅ 기존 모델 버전 삭제 (초기화)
    model_logger.logging_init("book_recommend", next_version)

    # ✅ 모델 학습 시작 로깅
    model_logger.logging_started("book_recommend", next_version)

    # 모델 저장 경로 설정
    model_dir = f"{airflow_dags_path}/models/book_recommend/model/{next_version}"
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, "book_recommend.joblib")
    tfidf_path = os.path.join(model_dir, "tfidf_vectorizer.joblib")

    joblib.dump(kmeans, model_path)
    joblib.dump(tfidf_vectorizer, tfidf_path)

    # ✅ 모델 학습 완료 로깅
    model_logger.logging_finished("book_recommend", next_version)

    return model_path, tfidf_path
