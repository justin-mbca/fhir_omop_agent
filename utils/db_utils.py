# Database utility stubs for OMOP and external DBs


# Unified database utility for SQLite and PostgreSQL
import os
import sqlite3
from sqlalchemy import create_engine

def connect_omop_db(db_path="omop_demo.db"):
    """Connect to OMOP SQLite DB (legacy, for backward compatibility)."""
    return sqlite3.connect(db_path)

def get_db_engine(db_type='sqlite', db_path='omop_demo.db', pg_settings=None):
    """
    Returns a SQLAlchemy engine for SQLite or PostgreSQL.
    db_type: 'sqlite' or 'postgresql'
    db_path: path to SQLite DB (if used)
    pg_settings: dict with keys user, password, host, port, db (if PostgreSQL)
    """
    if db_type == 'sqlite':
        return create_engine(f'sqlite:///{db_path}')
    elif db_type == 'postgresql':
        if pg_settings is None:
            # Try to get from environment variables
            pg_settings = {
                'user': os.getenv('DB_USER', 'clinical_user'),
                'password': os.getenv('DB_PASS', 'StrongPassword123'),
                'host': os.getenv('DB_HOST', 'localhost'),
                'port': os.getenv('DB_PORT', '5432'),
                'db': os.getenv('DB_NAME', 'clinical_demo'),
            }
        url = f"postgresql+psycopg2://{pg_settings['user']}:{pg_settings['password']}@{pg_settings['host']}:{pg_settings['port']}/{pg_settings['db']}"
        return create_engine(url)
    else:
        raise ValueError(f"Unsupported db_type: {db_type}")
