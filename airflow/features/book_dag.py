from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
import requests
import json
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from airflow.providers.mysql.hooks.mysql import MySqlHook

from support.config import TTBKEY

# Define default arguments for the DAG
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2025, 1, 21),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Create the DAG
dag = DAG(
    'book_recommendation_dag',
    default_args=default_args,
    description='A DAG for book search and recommendation',
    schedule_interval=timedelta(days=1),
)


# Define the functions
def search_books(ttbkey, query, df, queryType="Keyword", start=1, MaxResults=50, sort="Accuracy"):
    url = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
    params = {
        "TTBKey": ttbkey,
        "Query": query,
        "QueryType": queryType,
        "start": start,
        "MaxResults": MaxResults,
        "Sort": sort,
        "Cover": "None",
        "CategoryId": "0",
        "output": "js",
        "SearchTarget": "Book",
        "Version": "20131101",
        "outofStockfilter": 1,
        "RecentPublishFilter": 0,
    }

    response = requests.get(url, params=params)
    data = json.loads(response.text)

    if "item" in data:
        items = []
        for item in data["item"]:
            book_info = {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "author": item.get("author", ""),
                "pubDate": item.get("pubDate", ""),
                "description": item.get("description", ""),
                "isbn": item.get("isbn", ""),
                "isbn13": item.get("isbn13", ""),
                "itemId": item.get("itemId", ""),
                "priceSales": item.get("priceSales", ""),
                "priceStandard": item.get("priceStandard", ""),
                "categoryId": item.get("categoryId", ""),
                "categoryName": item.get("categoryName", ""),
                "publisher": item.get("publisher", ""),
                "customerReviewRank": item.get("customerReviewRank", ""),
            }
            items.append(book_info)

        df = pd.concat([df, pd.DataFrame(items)], ignore_index=True)

    return df


def collect_books(ttbkey, query, max_books=500):
    df = pd.DataFrame(columns=[
        "title", "link", "author", "pubDate", "description", "isbn", "isbn13",
        "itemId", "priceSales", "priceStandard", "categoryId", "categoryName",
        "publisher", "customerReviewRank",
    ])

    start = 1
    max_results_per_call = 50

    while len(df) < max_books:
        df = search_books(ttbkey, query, df, start=start, MaxResults=max_results_per_call)
        start += max_results_per_call
        if len(df) == len(df.drop_duplicates()):
            break

    df = df.head(max_books)
    return df


def recommend_books(df, num_recommendations=5):
    book_descriptions = df["description"].fillna("")

    tfidf_vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
    tfidf_matrix = tfidf_vectorizer.fit_transform(book_descriptions)

    num_clusters = max(min(len(df) // 10, 20), 1)
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    kmeans.fit(tfidf_matrix)

    df["cluster"] = kmeans.labels_

    largest_cluster = df["cluster"].value_counts().idxmax()
    recommended_books = df[df["cluster"] == largest_cluster].head(num_recommendations)

    return recommended_books[["title", "author", "description"]]


def save_books_to_mysql(df, connection_id):
    # Create a MySQL table if it doesn't exist
    create_table_query = """
    CREATE TABLE IF NOT EXISTS books (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255),
        link TEXT,
        author VARCHAR(255),
        pubDate VARCHAR(50),
        description TEXT,
        isbn VARCHAR(50),
        isbn13 VARCHAR(50),
        itemId VARCHAR(50),
        priceSales FLOAT,
        priceStandard FLOAT,
        categoryId VARCHAR(50),
        categoryName VARCHAR(255),
        publisher VARCHAR(255),
        customerReviewRank FLOAT
    );
    """

    # Convert DataFrame to list of tuples and handle NaN values
    data = df.fillna('').applymap(lambda x: str(x) if not isinstance(x, (int, float)) else f"{x:.2f}").values.tolist()

    mysql_hook = MySqlHook(mysql_conn_id=connection_id)

    # 테이블 생성
    mysql_hook.run(create_table_query)

    # 데이터 삽입
    mysql_hook.insert_rows('books', data, target_fields=[
        'title', 'link', 'author', 'pubDate', 'description', 'isbn', 'isbn13', 'itemId',
        'priceSales', 'priceStandard', 'categoryId', 'categoryName', 'publisher', 'customerReviewRank'
    ])


def search_and_collect_books(**kwargs):
    ttbkey = kwargs['params']['ttbkey']
    query = kwargs['params']['query']
    collected_books = collect_books(ttbkey, query)
    kwargs['ti'].xcom_push(key='collected_books', value=collected_books.to_json())


def save_books_to_mysql_task(**kwargs):
    ti = kwargs['ti']
    collected_books_json = ti.xcom_pull(key='collected_books', task_ids='search_and_collect_books')
    collected_books = pd.read_json(collected_books_json)

    # MySQL에 책 정보 저장
    save_books_to_mysql(collected_books, 'book_db')

    # 중복 제거 쿼리 실행
    mysql_hook = MySqlHook(mysql_conn_id='book_db')
    deduplicate_query = """
    DELETE t1 FROM books t1
    INNER JOIN books t2 
    WHERE t1.id > t2.id AND t1.isbn = t2.isbn AND t1.isbn13 = t2.isbn13;
    """
    mysql_hook.run(deduplicate_query)


def generate_recommendations(**kwargs):
    ti = kwargs['ti']
    collected_books = pd.read_json(ti.xcom_pull(key='collected_books', task_ids='search_and_collect_books'))
    recommendations = recommend_books(collected_books)
    print("추천 도서:")
    for i, (_, book) in enumerate(recommendations.iterrows(), 1):
        print(f"{i}. {book['title']} - {book['author']}")
        print(f" 설명: {book['description'][:100]}...")
        print()


# Define the tasks
search_task = PythonOperator(
    task_id='search_and_collect_books',
    python_callable=search_and_collect_books,
    op_kwargs={'params': {'ttbkey': TTBKEY, 'query': 'MLOps'}},
    dag=dag,
)

save_task = PythonOperator(
    task_id='save_books_to_mysql',
    python_callable=save_books_to_mysql_task,
    dag=dag,
)

recommend_task = PythonOperator(
    task_id='generate_recommendations',
    python_callable=generate_recommendations,
    dag=dag,
)

# Set task dependencies
search_task >> save_task >> recommend_task
