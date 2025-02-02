import os
import unittest

os.environ['FEATURE_STORE_URL'] = f"mysql+pymysql://root:root@localhost/book_db"


class TestModelCtLogger(unittest.TestCase):

    @classmethod
    def setUpClass(cls) -> None:
        from models.book_mlops.support.model.repository.model_logger_repository import ModelLoggerRepository
        cls.model_ct_logger = ModelLoggerRepository()

    def test_01_logging_started(self):
        model_name = "ineligible_loan_model"
        model_version = "1.0.1"
        self.model_ct_logger.logging_started(model_name, model_version)

    def test_02_logging_finished(self):
        model_name = "ineligible_loan_model"
        model_version = "1.0.1"
        self.model_ct_logger.logging_finished(model_name, model_version)


if __name__ == '__main__':
    unittest.main()
