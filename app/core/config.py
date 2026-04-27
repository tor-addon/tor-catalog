from pydantic_settings import BaseSettings
from typing import Dict

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=env_path)

class Settings(BaseSettings):
    TMDB_API_KEY: str = os.getenv("TMDB_API_KEY", "")
    # Provider mapping
    PROVIDERS: Dict[str, int] = {
        "Netflix": 8,
        "Prime Video": 119,
        "Disney+": 337,
        "Apple TV": 350,
        "Canal+": 381,
        "Paramount+": 531,
        "HBO Max": 1899,
        "Hulu": 15,
        "Peacock": 386,
        "MUBI": 331,
        "Starz": 11
    }

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'
        extra = 'ignore'

import os
from pathlib import Path
# Load .env manually if python-dotenv/pydantic is acting up with paths
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent
env_path = os.path.join(BASE_DIR, '.env')
load_dotenv(dotenv_path=env_path)

settings = Settings()