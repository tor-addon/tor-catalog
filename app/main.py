from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router

app = FastAPI(title="Tor Catalog")

# CORS for Stremio
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Mode développement local (port 8000)
    port = int(os.environ.get("PORT", 8001))
    # En production, on désactive le reload auto pour les performances
    reload = os.environ.get("ENV", "development") == "development"
    
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=reload)