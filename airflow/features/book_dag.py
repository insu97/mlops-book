"""Book recommendation DAG for Airflow."""
import json
from datetime import datetime, timedelta

import pandas as pd
import requests
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.mysql.hooks.mysql import MySqlHook
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

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

def search_books(ttbkey, query, df, query_type="Keyword", start=1, max_results=50, sort="Accuracy"):
    """
    Search for books using the Aladin API.

    Args:
        ttbkey (str): API key for Aladin.
        query (str): Search query.
        df (pd.DataFrame): DataFrame to store results.
        query_type (str): Type of query (default: "Keyword").
        start (int): Starting index for results (default: 1).
        max_results (int): Maximum number of results per call (default: 50).
        sort (str): Sorting order (default: "Accuracy").

    Returns:
        pd.DataFrame: Updated DataFrame with search results.
    """
    url = "http://www.aladin.co.kr/ttb/api/ItemSearch.aspx"
    params = {
        "TTBKey": ttbkey,
        "Query": query,
        "QueryType": query_type,
        "start": start,
        "MaxResults": max_results,
        "Sort": sort,
        "Cover": "None",
        "CategoryId": "0",
        "output": "js",
        "SearchTarget": "Book",
        "Version": "20131101",
        "outofStockfilter": 1,
        "RecentPublishFilter": 0,
    }

    response = requests.get(url, params=params, timeout=10)
    data = json.loads(response.text)

    if "item" in data:
        items = []
        for item in data["item"]:
            book_info = {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "author": item.get("author", ""),
                "pub_date": item.get("pubDate", ""),
                "description": item.get("description", ""),
                "isbn": item.get("isbn", ""),
                "isbn13": item.get("isbn13", ""),
                "item_id": item.get("itemId", ""),
                "price_sales": item.get("priceSales", ""),
                "price_standard": item.get("priceStandard", ""),
                "category_id": item.get("categoryId", ""),
                "category_name": item.get("categoryName", ""),
                "publisher": item.get("publisher", ""),
                "customer_review_rank": item.get("customerReviewRank", ""),
            }
            items.append(book_info)

        df = pd.concat([df, pd.DataFrame(items)], ignore_index=True)

    return df

def collect_books(ttbkey, query, max_books=500):
    """
    Collect books from Aladin API.

    Args:
        ttbkey (str): API key for Aladin.
        query (str): Search query.
        max_books (int): Maximum number of books to collect.

    Returns:
        pd.DataFrame: Collected book data.
    """
    df = pd.DataFrame(columns=[
        "title", "link", "author", "pub_date", "description", "isbn", "isbn13",
        "item_id", "price_sales", "price_standard", "category_id", "category_name",
        "publisher", "customer_review_rank",
    ])

    start = 1
    max_results_per_call = 50

    while len(df) < max_books:
        df = search_books(ttbkey, query, df, start=start, max_results=max_results_per_call)
        start += max_results_per_call
        if len(df) == len(df.drop_duplicates()):
            break

    return df.head(max_books)

def recommend_books(df, num_recommendations=5):
    """
    Recommend books based on clustering.

    Args:
        df (pd.DataFrame): DataFrame containing book data.
        num_recommendations (int): Number of books to recommend.

    Returns:
        pd.DataFrame: Recommended books.
    """
    book_descriptions = df["description"].fillna("")

    tfidf_vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
    tfidf_matrix = tfidf_vectorizer.fit_transform(book_descriptions)

    num_clusters = min(len(df) // 10, 20)
    kmeans = KMeans(n_clusters=num_clusters, random_state=42)
    kmeans.fit(tfidf_matrix)

    df["cluster"] = kmeans.labels_

    largest_cluster = df["cluster"].value_counts().idxmax()
    recommended_books = df[df["cluster"] == largest_cluster].head(num_recommendations)

    return recommended_books[["title", "author", "description"]]

def save_books_to_mysql(df, connection_id):
    """
    Save books to MySQL database.

    Args:
        df (pd.DataFrame): DataFrame containing book data.
        connection_id (str): MySQL connection ID.
    """
    create_table_query = """
    CREATE TABLE IF NOT EXISTS books (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255),
        link TEXT,
        author VARCHAR(255),
        pub_date VARCHAR(50),
        description TEXT,
        isbn VARCHAR(50),
        isbn13 VARCHAR(50),
        item_id VARCHAR(50),
        price_sales FLOAT,
        price_standard FLOAT,
        category_id VARCHAR(50),
        category_name VARCHAR(255),
        publisher VARCHAR(255),
        customer_review_rank FLOAT
    );
    """

    data = df.fillna('').applymap(lambda x: str(x) if not isinstance(x, (int, float)) else f"{x:.2f}").values.tolist()

    mysql_hook = MySqlHook(mysql_conn_id=connection_id)

    mysql_hook.run(create_table_query)

    mysql_hook.insert_rows('books', data, target_fields=[
        'title', 'link', 'author', 'pub_date', 'description', 'isbn', 'isbn13', 'item_id',
        'price_sales', 'price_standard', 'category_id', 'category_name', 'publisher', 'customer_review_rank'
    ])

def search_and_collect_books(**kwargs):
    """
    Search and collect books using Aladin API.

    Args:
        **kwargs: Keyword arguments passed by Airflow.
    """
    ttbkey = kwargs['params']['ttbkey']
    query = kwargs['params']['query']
    collected_books = collect_books(ttbkey, query)
    kwargs['ti'].xcom_push(key='collected_books', value=collected_books.to_json())

def save_books_to_mysql_task(**kwargs):
    """
    Save collected books to MySQL database.

    Args:
        **kwargs: Keyword arguments passed by Airflow.
    """
    ti = kwargs['ti']
    collected_books_json = ti.xcom_pull(key='collected_books', task_ids='search_and_collect_books')
    collected_books = pd.read_json(collected_books_json)

    save_books_to_mysql(collected_books, 'book_db')

def generate_recommendations(**kwargs):
    """
    Generate book recommendations.

    Args:
        **kwargs: Keyword arguments passed by Airflow.
    """
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
    op_kwargs={'params': {'ttbkey': TTBKEY, 'query': '파이썬'}},
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
