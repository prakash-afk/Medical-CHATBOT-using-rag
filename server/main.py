from fastapi import FastAPI
from auth.routes import router as auth_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth", tags=["auth"])  

@app.get("/health")
def health():    return {"status": "ok"}

def main():
    print("Hello from server!")


if __name__ == "__main__":
    main()
