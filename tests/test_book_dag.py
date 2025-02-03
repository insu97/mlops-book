import os
from airflow.models import DagBag

def test_dag_loaded():
    # 환경 변수 강제 설정
    os.environ["AIRFLOW__DATABASE__SQL_ALCHEMY_CONN"] = "sqlite:///test_airflow.db"
    os.environ["AIRFLOW__CORE__DAGS_FOLDER"] = os.path.join(os.getcwd(), "airflow/dags")
    
    dagbag = DagBag(
        dag_folder=os.environ['AIRFLOW__CORE__DAGS_FOLDER'], 
        include_examples=False
    )
    
    assert len(dagbag.dags) > 0, "DAG 파일을 찾을 수 없음"
    dag = dagbag.get_dag('book_mlops')
    assert dag is not None, "DAG 로드 실패"
    assert len(dag.tasks) >= 3, "최소 3개 태스크 필요"
