import os
from airflow.models import DagBag

def test_dag_loaded():
    dag_folder = os.path.join(os.getcwd(), "airflow/dags")
    
    dagbag = DagBag(
        dag_folder=dag_folder,
        include_examples=False
    )
    
    # Import 에러 확인
    assert not dagbag.import_errors, f"DAG Import Errors: {dagbag.import_errors}"
    
    # DAG 존재 여부 확인
    assert len(dagbag.dags) > 0, f"No DAGs found in {dag_folder}"
    
    # 특정 DAG 검증
    dag = dagbag.get_dag('book_mlops')
    assert dag is not None, "Target DAG not found"
    assert len(dag.tasks) >= 3, "At least 3 tasks required"
