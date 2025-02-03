from fastapi import FastAPI
import joblib
import os

app = FastAPI()

# 모델 로드
model_version = os.getenv('MODEL_VERSION', '1.0.0')
model_path = f'models/book_recommend/model/{model_version}/book_recommend.joblib'
tfidf_path = f'models/book_recommend/model/{model_version}/tfidf_vectorizer.joblib'

model = joblib.load(model_path)
tfidf = joblib.load(tfidf_path)

@app.post("/predict")
async def predict(description: str):
    vector = tfidf.transform([description])
    cluster = model.predict(vector)
    return {"cluster": int(cluster[0])}
