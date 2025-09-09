"""
ETL script for OMOP CDM using both PostgreSQL and SQLite
Refactored for MCP orchestrator compatibility.
"""

import pandas as pd
import os
import sqlalchemy
from sqlalchemy import create_engine
from utils.db_utils import get_db_engine
from utils.config_utils import load_config

__all__ = ["run_etl"]

def load_omop_schema(engine, schema_path):
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    with engine.connect() as conn:
        for stmt in schema_sql.strip().split(';'):
            if stmt.strip():
                conn.execute(sqlalchemy.text(stmt))

def run_etl(db_type=None, db_path=None, pg_settings=None, config_path="config.yaml"):
    """
    db_type: 'sqlite' or 'postgresql' (overrides config if set)
    db_path: path to SQLite DB (if used, overrides config)
    pg_settings: dict for PostgreSQL (overrides config)
    config_path: path to config.yaml
    """
    config = load_config(config_path)
    # Determine DB settings
    db_type = db_type or config['database']['backend']
    if db_type == 'sqlite':
        db_path = db_path or config['database']['sqlite_path']
        engine = get_db_engine(db_type=db_type, db_path=db_path)
    else:
        pg_settings = pg_settings or config['database']['postgresql']
        engine = get_db_engine(db_type=db_type, pg_settings=pg_settings)
    # Data paths
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, config['data']['base_dir'])
    person_df = pd.read_csv(os.path.join(data_dir, config['data']['person_sample']))
    observation_df = pd.read_csv(os.path.join(data_dir, config['data']['observation_sample']))
    condition_df = pd.read_csv(os.path.join(data_dir, config['data']['condition_sample']))
    procedure_df = pd.read_csv(os.path.join(data_dir, config['data']['procedure_sample']))
    mapping_path = os.path.join(data_dir, config['data']['code_mapping_sample'])
    # Generalized mapping: map any code to OMOP standard concept_id using mapping file
    def map_to_standard_concept(val, mapping_dict):
        try:
            return int(val)
        except Exception:
            return int(mapping_dict[val]) if val in mapping_dict else None

    if os.path.exists(mapping_path):
        mapping_df = pd.read_csv(mapping_path)
        code_map = dict(zip(mapping_df['source_code'], mapping_df['standard_concept_id']))
        # Map *_concept_id fields for all standardized tables
        observation_df['observation_concept_id'] = observation_df['observation_concept_id'].apply(lambda v: map_to_standard_concept(v, code_map))
        condition_df['condition_concept_id'] = condition_df['condition_concept_id'].apply(lambda v: map_to_standard_concept(v, code_map))
        procedure_df['procedure_concept_id'] = procedure_df['procedure_concept_id'].apply(lambda v: map_to_standard_concept(v, code_map))

    # --- Automatic OMOP table creation for SQLite ---
    if db_type == 'sqlite':
        import sqlite3
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        # Drop and recreate person table
        cur.execute("DROP TABLE IF EXISTS person;")
        cur.execute("""
        CREATE TABLE person (
            person_id INTEGER PRIMARY KEY,
            gender_concept_id INTEGER,
            year_of_birth INTEGER,
            month_of_birth INTEGER,
            day_of_birth INTEGER,
            race_concept_id INTEGER,
            ethnicity_concept_id INTEGER
        )
        """)
        # Drop and recreate observation table
        cur.execute("DROP TABLE IF EXISTS observation;")
        cur.execute("""
        CREATE TABLE observation (
            observation_id INTEGER PRIMARY KEY,
            person_id INTEGER,
            observation_concept_id INTEGER,
            observation_date TEXT,
            value_as_number REAL,
            value_as_string TEXT
        )
        """)
        # Drop and recreate condition_occurrence table
        cur.execute("DROP TABLE IF EXISTS condition_occurrence;")
        cur.execute("""
        CREATE TABLE condition_occurrence (
            condition_occurrence_id INTEGER PRIMARY KEY,
            person_id INTEGER,
            condition_concept_id INTEGER,
            condition_start_date TEXT,
            condition_source_value TEXT
        )
        """)
        # Drop and recreate procedure_occurrence table
        cur.execute("DROP TABLE IF EXISTS procedure_occurrence;")
        cur.execute("""
        CREATE TABLE procedure_occurrence (
            procedure_occurrence_id INTEGER PRIMARY KEY,
            person_id INTEGER,
            procedure_concept_id INTEGER,
            procedure_date TEXT,
            procedure_source_value TEXT
        )
        """)
        conn.commit()
        conn.close()
    # Data quality checks (as before)
    errors = []
    if not person_df['person_id'].notnull().all():
        errors.append("Missing person_id in person data")
    if not observation_df['person_id'].notnull().all():
        errors.append("Missing person_id in observation data")
    if not condition_df['person_id'].notnull().all():
        errors.append("Missing person_id in condition data")
    if not procedure_df['person_id'].notnull().all():
        errors.append("Missing person_id in procedure data")
    if person_df['person_id'].duplicated().any():
        errors.append("Duplicate person_id found in person data")
    from datetime import datetime
    current_year = datetime.now().year
    if (person_df['year_of_birth'] > current_year).any():
        errors.append("year_of_birth in the future found in person data")
    if not observation_df['person_id'].isin(person_df['person_id']).all():
        errors.append("Observation references person_id not in person table")
    if not condition_df['person_id'].isin(person_df['person_id']).all():
        errors.append("Condition references person_id not in person table")
    if not procedure_df['person_id'].isin(person_df['person_id']).all():
        errors.append("Procedure references person_id not in person table")
    if observation_df['observation_concept_id'].isnull().any():
        errors.append("Unmapped observation_concept_id found in observation data")
    if condition_df['condition_concept_id'].isnull().any():
        errors.append("Unmapped condition_concept_id found in condition data")
    if procedure_df['procedure_concept_id'].isnull().any():
        errors.append("Unmapped procedure_concept_id found in procedure data")
    if errors:
        print("Data Quality Issues Found:")
        for err in errors:
            print(f"- {err}")
        raise ValueError("Data quality checks failed. See errors above.")
    # Load data into database
    person_df.to_sql('person', engine, if_exists='append', index=False)
    observation_df.to_sql('observation', engine, if_exists='append', index=False)
    condition_df.to_sql('condition_occurrence', engine, if_exists='append', index=False)
    procedure_df.to_sql('procedure_occurrence', engine, if_exists='append', index=False)
    print("ETL complete: data loaded to OMOP tables.")


# Script usage: python etl_load.py
if __name__ == "__main__":
    run_etl()
