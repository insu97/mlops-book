from airflow.providers.mysql.hooks.mysql import MySqlHook
import joblib
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from airflow.models import Variable
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import pandas as pd

def predict(**kwargs):
    query = kwargs['params']['query']

    # 1. 모델 불러오기
    airflow_dags_path = Variable.get('AIRFLOW_DAGS_PATH')
    model_dir = f"{airflow_dags_path}/models/book_recommend/model"
    model_path = os.path.join(model_dir, "book_recommend.joblib")
    tfidf_path = os.path.join(model_dir, "tfidf_vectorizer.joblib")

    model = joblib.load(model_path)
    tfidf_vectorizer = joblib.load(tfidf_path)

    # 2. DataBase 불러오기
    mysql_hook = MySqlHook(mysql_conn_id='book_db')
    sql_query = "SELECT title, description, isbn13 FROM books"
    df = mysql_hook.get_pandas_df(sql_query)

    # 3. TF-IDF로 책 설명을 벡터화
    tfidf_matrix = tfidf_vectorizer.transform(df["description"].fillna(''))

    # 4. 쿼리 벡터화 및 유사도 계산
    query_vector = tfidf_vectorizer.transform([query])
    similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()

    # 5. 클러스터 예측
    cluster_labels = model.predict(tfidf_matrix)
    query_cluster = model.predict(query_vector)[0]

    # 6. 클러스터와 유사도를 결합한 추천
    df['cluster'] = cluster_labels
    df['similarity'] = similarities

    # 개선사항 1: 유사도 임계값 도입
    similarity_threshold = 0.1
    df_filtered = df[df['similarity'] > similarity_threshold]

    # 개선사항 2: 클러스터와 유사도의 가중치 조정
    df_filtered['score'] = df_filtered['similarity'] * 0.7 + (df_filtered['cluster'] == query_cluster).astype(int) * 0.3

    # 개선사항 3: 다양성 추가
    def diversify_recommendations(recommendations, n=5):
        clusters = recommendations['cluster'].unique()
        result = pd.DataFrame()
        for cluster in clusters:
            cluster_books = recommendations[recommendations['cluster'] == cluster]
            result = pd.concat([result, cluster_books.head(max(1, n // len(clusters)))])
        return result.head(n)

    # 점수에 따라 정렬하고 다양성을 고려하여 추천
    recommended_books = diversify_recommendations(df_filtered.sort_values('score', ascending=False))

    # 결과로 상위 5개 책 추천
    recommended_books = recommended_books[['title', 'description', 'isbn13']].head(5)

    return recommended_books
