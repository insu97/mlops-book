from airflow.providers.mysql.hooks.mysql import MySqlHook
import joblib
import os
from airflow.models import Variable
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.metrics.pairwise import euclidean_distances
import pandas as pd
import numpy as np


def predict(**kwargs):
    query = kwargs['params']['query']

    # 1. 모델 불러오기
    airflow_dags_path = Variable.get('AIRFLOW_DAGS_PATH')
    model_dir = f"{airflow_dags_path}/models/book_recommend/model"
    model_path = os.path.join(model_dir, "book_recommend.joblib")
    tfidf_path = os.path.join(model_dir, "tfidf_vectorizer.joblib")

    model = joblib.load(model_path)
    tfidf_vectorizer = joblib.load(tfidf_path)

    # 2. 데이터베이스 불러오기
    mysql_hook = MySqlHook(mysql_conn_id='book_db')
    sql_query = "SELECT title, description, isbn13 FROM books"
    df = mysql_hook.get_pandas_df(sql_query)

    # 3. 결측값 처리
    df['description'] = df['description'].fillna('')

    # 4. TF-IDF로 책 설명을 벡터화
    tfidf_matrix = tfidf_vectorizer.transform(df["description"])

    # 5. 쿼리 벡터화 및 유사도 계산
    query_vector = tfidf_vectorizer.transform([query])
    # distances = euclidean_distances(query_vector, tfidf_matrix).flatten()
    similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()

    # 6. 클러스터 예측
    cluster_labels = model.predict(tfidf_matrix)
    query_cluster = model.predict(query_vector)[0]

    # 7. 클러스터와 유사도를 결합한 추천
    df['cluster'] = cluster_labels
    # df['distance'] = distances
    df['similarity'] = similarities

    def adjust_threshold(df, initial_threshold=0.5, max_threshold=1.0):  # 0.5, 2
        threshold = initial_threshold
        while threshold <= max_threshold:
            df_filtered = df[df['similarity'] > threshold]  # distance <
            if not df_filtered.empty:
                return threshold, df_filtered
            threshold += 0.1
        return max_threshold, df[df['similarity'] < max_threshold]  # distance

    # 동적 임계값 적용
    similarity_threshold, df_filtered = adjust_threshold(df)

    # 데이터가 없는 경우 에러 처리
    if df_filtered.empty:
        raise ValueError("No books meet the similarity threshold, even after lowering it.")

    # df_filtered['score'] = (
    #         (1 / (1 + df_filtered['distance'])) * 0.7 +  # 유사성(거리 기반)
    #         (df_filtered['distance'] == query_cluster).astype(int) * 0.3  # 같은 클러스터에 속하는지 여부 (cluster 비교)
    # )

    df_filtered['score'] = (
            df_filtered['similarity'] * 0.7 +  # ✅ 올바른 계산
            (df_filtered['cluster'] == query_cluster).astype(int) * 0.3
    )

    # 다양성 추가 함수 개선
    def diversify_recommendations(recommendations, n=5):
        clusters = recommendations['cluster'].unique()
        result = pd.DataFrame()
        for cluster in clusters:
            cluster_books = recommendations[recommendations['cluster'] == cluster]
            result = pd.concat([result, cluster_books.head(max(1, n // len(clusters)))])
        return result.head(n)

    # 추천 결과 다양화 적용
    recommended_books = diversify_recommendations(df_filtered.sort_values('score', ascending=False))

    # 디버깅: 추천 결과 확인
    print("Recommended books:", recommended_books)

    # 필요한 컬럼만 선택
    try:
        recommended_books = recommended_books[['title', 'description', 'isbn13']].head(5)
    except KeyError as e:
        print("KeyError:", e)
        print("Available columns:", recommended_books.columns)
        raise

    return recommended_books
