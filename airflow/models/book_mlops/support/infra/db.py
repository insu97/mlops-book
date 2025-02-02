import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from pandas import DataFrame
from pandas.io.sql import read_sql

feature_store_url = os.getenv('FEATURE_STORE_URL', "mysql+pymysql://root:root@localhost/book_db")


class Db:
    def __init__(self, url: str = feature_store_url):
        self._engine = create_engine(url)
        self._Session = sessionmaker(bind=self._engine)

    def read_sql(self, sql: str) -> DataFrame:
        """SQL 쿼리 실행 후 DataFrame 반환"""
        with self._engine.connect() as conn:  # ✅ SQLAlchemy 2.0 스타일 적용
            return read_sql(sql, con=conn)

    def execute(self, sql: str, params=None):
        """SQL 실행 (INSERT, UPDATE, DELETE)"""
        with self._Session() as session:  # ✅ Session 사용
            result = session.execute(text(sql), params)
            session.commit()
            return result
