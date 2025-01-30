import pendulum
from datetime import datetime

from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator, BranchPythonOperator
import sys
import os

sys.path.append("/home/runner/work/mlops-book/mlops-book/airflow/support")
from support.config import TTBKEY
from models.book_recommend.data.data_extract import search_and_collect_books
from models.book_recommend.model.check_model import check_model
from models.book_recommend.model.new_model_create import new_model_create
from models.book_recommend.data.save_books_to_database import save_books_to_database_task
from models.book_recommend.model.predict import predict
from models.book_recommend.model.minibatch_model import minibatch_model

local_timezone = pendulum.timezone('Asia/Seoul')

query = "주식"

dag = DAG(dag_id="book_recommend_model",
          default_args={
              "owner": "insu",
              "depends_on_past": False,
              "email": ["parkinsu9701@gmail.com"],
          },
          description="책 추천 모델",
          schedule=None,
          start_date=datetime(2025, 1, 1, tzinfo=local_timezone),
          catchup=False,
          tags=["mlops", "recommend"]
          )

# Define the tasks
search_task = PythonOperator(
    task_id='search_and_collect_books',
    python_callable=search_and_collect_books,
    op_kwargs={'params': {'ttbkey': TTBKEY, 'query': query}},
    dag=dag,
)

check_model_task = BranchPythonOperator(
    task_id='check_model',
    python_callable=check_model,
    provide_context=True,
    dag=dag,
)

new_model_create = PythonOperator(
    task_id="new_model_create",
    python_callable=new_model_create,
    op_kwargs={'params': {'query': query}},
    dag=dag,
)

minibatch_model = PythonOperator(
    task_id='minibatch_model',
    python_callable=minibatch_model,
    op_kwargs={'params': {'query': query}},
    dag=dag,
)

save_books_to_database_task = PythonOperator(
    task_id="save_books_to_database",
    python_callable=save_books_to_database_task,
    trigger_rule="none_failed_min_one_success",
    dag=dag,
)

predict_task = PythonOperator(
    task_id="predict",
    python_callable=predict,
    op_kwargs={'params': {'query': query}},
    dag=dag,
)

# 태스크 의존성 설정
search_task >> check_model_task
check_model_task >> [new_model_create, minibatch_model]
[new_model_create, minibatch_model] >> save_books_to_database_task >> predict_task
