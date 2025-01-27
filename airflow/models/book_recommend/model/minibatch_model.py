import os
import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from airflow.models import Variable


def minibatch_model(**kwargs):
    # 1. 모델 불러오기
    airflow_dags_path = Variable.get('AIRFLOW_DAGS_PATH')
    model_dir = f"{airflow_dags_path}/models/book_recommend/model"
    model_path = os.path.join(model_dir, "book_recommend.joblib")
    tfidf_path = os.path.join(model_dir, "tfidf_vectorizer.joblib")

    model = joblib.load(model_path)
    tfidf_vectorizer = joblib.load(tfidf_path)

    # 2. 검색한 데이터 불러오기
    ti = kwargs['ti']
    df = pd.read_json(ti.xcom_pull(key='collected_books', task_ids='search_and_collect_books'))

    # 3. 텍스트 데이터를 벡터화 (TfidfVectorizer 사용)
    tfidf_matrix = tfidf_vectorizer.transform(df["description"].fillna(''))  # description 컬럼 벡터화

    # 4. 모델을 partial_fit으로 학습 (벡터화된 데이터로 학습)
    model.partial_fit(tfidf_matrix)

    # 5. 모델 저장
    joblib.dump(model, model_path)

    return model_path
