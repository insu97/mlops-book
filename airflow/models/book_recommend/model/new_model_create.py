from sklearn.cluster import MiniBatchKMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import pandas as pd
from airflow.models import Variable
import joblib
import os

airflow_dags_path = Variable.get('AIRFLOW_DAGS_PATH')

def new_model_create(num_recommendations=5, **kwargs):
    query = kwargs['params']['query']

    ti = kwargs['ti']
    df = pd.read_json(ti.xcom_pull(key='collected_books', task_ids='search_and_collect_books'))
    book_descriptions = df["description"].fillna("")

    # TF-IDF 벡터화
    tfidf_vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
    tfidf_matrix = tfidf_vectorizer.fit_transform(book_descriptions)

    # KMeans 클러스터링
    num_clusters = max(min(len(df) // 10, 20), 1)
    kmeans = MiniBatchKMeans(n_clusters=num_clusters, random_state=42)
    kmeans.fit(tfidf_matrix)

    # 모델 저장
    model_dir = f"{airflow_dags_path}/models/book_recommend/model"
    model_path = os.path.join(model_dir, "book_recommend.joblib")
    tfidf_path = os.path.join(model_dir, "tfidf_vectorizer.joblib")

    joblib.dump(kmeans, model_path)
    joblib.dump(tfidf_vectorizer, tfidf_path)

    return model_path, tfidf_path