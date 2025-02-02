from models.book_mlops.support.infra.db import Db


class ModelLoggerRepository:
    MODEL_META_DB = Db()

    def __init__(self,
                 db: Db = MODEL_META_DB):
        self._db = db

    def logging_init(self, model_name: str, model_version: str):
        sql = f"""
            delete
              from book_db.book_models
             where model_name = '{model_name}'
               and model_version = '{model_version}'
            """
        self._db.execute(sql=sql)

    def logging_started(self,
                        model_name: str,
                        model_version: str):
        sql = f"""
            insert 
              into book_db.book_models 
                   (model_name, model_version)
            values ('{model_name}', '{model_version}')
            """
        self._db.execute(sql=sql)

    def logging_finished(self,
                         model_name: str,
                         model_version: str):
        sql = f"""
            update book_db.book_models
            set model_version = '{model_version}'
            where model_name = '{model_name}'
               and model_version = '{model_version}'
            """
        self._db.execute(sql=sql)
