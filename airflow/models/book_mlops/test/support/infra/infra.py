import os
import unittest

os.environ['FEATURE_STORE_URL'] = f"mysql+pymysql://root:root@localhost/book_db"


class TestDb(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        from models.book_mlops.support.infra.db import Db
        cls.db = Db()

    def test_read_sql(self):
        sql = """select 1"""
        actual = self.db.read_sql(sql=sql)
        self.assertEqual([[1]], actual.values)

    def test_execute(self):
        sql = """DROP TABLE IF EXISTS book_db.test_db"""
        self.db.execute(sql=sql)

        sql = """CREATE TABLE book_db.test_db AS SELECT 1 AS value"""
        self.db.execute(sql=sql)

        sql = """INSERT INTO book_db.test_db (value) VALUES (1)"""
        actual = self.db.execute(sql=sql)
        self.assertEqual(1, actual.rowcount)  # rowcount 사용 가능

        sql = """DROP TABLE book_db.test_db"""
        self.db.execute(sql=sql)


if __name__ == '__main__':
    unittest.main()
