import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "database": os.getenv("DB_NAME", "clothing_store"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("LOCAL_DB_PASSWORD"),
}


def get_connection():
    """On Render, DATABASE_URL is set. Locally, falls back to DB_CONFIG."""
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        return psycopg2.connect(database_url)

    return psycopg2.connect(**DB_CONFIG)
