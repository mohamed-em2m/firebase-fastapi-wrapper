from fastapi import FastAPI
from firebase_functions import https_fn
from firebase_fastapi_wrapper.wrapper import FastAPIWrapper

# 1. Create your FastAPI app
app = FastAPI()

@app.get("/hello")
def hello():
    return {"message": "Hello from FastAPI inside Firebase Functions!"}

@app.get("/users/{user_id}")
def get_user(user_id: str):
    return {"user_id": user_id, "name": "John Doe"}

# 2. Wrap it with FastAPIWrapper
firebase_handler = FastAPIWrapper(app)

# 3. Expose as a Firebase HTTPS Function
@https_fn.on_request()
def handle_request(req: https_fn.Request):
    return firebase_handler(req)
