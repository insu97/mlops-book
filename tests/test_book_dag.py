import unittest
from airflow.models import DagBag

class TestBookDag(unittest.TestCase):
    def test_dag_loaded(self):
        dagbag = DagBag(dag_folder='features', include_examples=False)
        dag = dagbag.get_dag(dag_id='book_dag')
        self.assertIsNotNone(dag)
        self.assertEqual(len(dagbag.import_errors), 0)

if __name__ == '__main__':
    unittest.main()

