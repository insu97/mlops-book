import os

from airflow.models import Variable

airflow_dags_path = Variable.get('AIRFLOW_DAGS_PATH')


# 모델 존재 여부를 확인하고 모델을 불러오거나 새로 생성하는 함수
def check_model(**kwargs):
    model_dir = f"{airflow_dags_path}/models/book_recommend/model"  # 모델 디렉토리
    model_path = os.path.join(model_dir, "book_recommend.joblib")  # 모델 경로

    # 모델 디렉토리가 존재하지 않으면 생성
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)
        print(f"모델 디렉토리가 생성되었습니다: {model_dir}")

    if os.path.exists(model_path):
        # 기존 모델 불러오기
        print(f"모델이 존재합니다. 모델 경로: {model_path}")
        # model = joblib.load(model_path)
        return "minibatch_model"
    else:
        # 모델 생성 및 저장
        print(f"모델이 존재하지 않습니다.")
        # model = KMeans(n_clusters=5, random_state=42)  # 새로운 KMeans 모델 생성
        # joblib.dump(model, model_path)  # 모델 저장
        # print(f"새로운 모델이 생성되고 저장되었습니다. 모델 경로: {model_path}")
        return "new_model_create"

    # Task Instance XCom에 결과 반환
    # XCom에 경로만 저장
    # return {"model_path": model_path}
