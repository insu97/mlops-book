import os
import sys
from airflow.models import DagBag

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class TestBookDag:
    def test_dag_loaded(self):
        dagbag = DagBag(dag_folder=os.environ.get('AIRFLOW__CORE__DAGS_FOLDER', ''), include_examples=False)
        dag = dagbag.get_dag('book_mlops')
        assert dag is not None
        assert len(dagbag.import_errors) == 0, f"DAG import errors: {dagbag.import_errors}"

