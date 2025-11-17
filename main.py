from fastapi import FastAPI
from api.v1.auth_router import router as auth_router
from api.v1.file_router import router as file_router
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register Routers
app.include_router(auth_router)
app.include_router(file_router)

@app.get("/")
def root():
    return {"message": "FastAPI with Supabase + MinIO ready !!!"}
