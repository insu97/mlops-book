import os
import shutil
from airflow.models import Variable

airflow_dags_path = Variable.get('AIRFLOW_DAGS_PATH')


def deploy_model(**kwargs):
    model_path = kwargs['ti'].xcom_pull(task_ids='new_model_create')[0]
    tfidf_path = kwargs['ti'].xcom_pull(task_ids='new_model_create')[1]

    # Example: Move models to production server or deployment folder
    deployment_path = f"{airflow_dags_path}/models/book_recommend/deployment/"
    os.makedirs(deployment_path, exist_ok=True)
    shutil.copy(model_path, deployment_path)
    shutil.copy(tfidf_path, deployment_path)

    # Here you can add other deployment logic, such as triggering APIs or updating version control
    print(f"Model and TF-IDF vectorizer deployed to {deployment_path}")
