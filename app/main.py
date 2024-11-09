from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.routes import app_router

app = FastAPI(title="Planet AI API")

# Using CORS to allow requests only from the frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://planet-ai-frontend.vercel.app"],  # frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(app_router)

# Default route
@app.get("/")
async def root():
    return {"message": "Welcome to the Planet AI Backend"}
