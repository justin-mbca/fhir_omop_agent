# ETL script for OMOP CDM using both PostgreSQL and SQLite
# Adapted from clinical_data_demo/etl/etl_load.py for integration

import pandas as pd
import os
import sqlalchemy
from sqlalchemy import create_engine
from utils.db_utils import get_db_engine

# Load OMOP CDM schema (PostgreSQL only)
def load_omop_schema(engine, schema_path):
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema_sql = f.read()
    with engine.connect() as conn:
        for stmt in schema_sql.strip().split(';'):
            if stmt.strip():
                conn.execute(sqlalchemy.text(stmt))

# Load sample data and mapping, run QA, and load to DB
def run_etl(db_type='sqlite', db_path='omop_demo.db', pg_settings=None):
    """
    db_type: 'sqlite' or 'postgresql'
    db_path: path to SQLite DB (if used)
    pg_settings: dict with keys user, password, host, port, db (if PostgreSQL)
    """
    engine = get_db_engine(db_type=db_type, db_path=db_path, pg_settings=pg_settings)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    data_dir = os.path.join(base_dir, 'data')
    person_df = pd.read_csv(os.path.join(data_dir, 'person_sample.csv'))
    observation_df = pd.read_csv(os.path.join(data_dir, 'observation_sample.csv'))
    mapping_path = os.path.join(data_dir, 'code_mapping_sample.csv')
    if os.path.exists(mapping_path):
        mapping_df = pd.read_csv(mapping_path)
        obs_map = dict(zip(mapping_df['source_code'], mapping_df['standard_concept_id']))
        def map_concept_id(val):
            try:
                return int(val)
            except:
                return int(obs_map[val]) if val in obs_map else None
        observation_df['observation_concept_id'] = observation_df['observation_concept_id'].apply(map_concept_id)
    # Data quality checks (as before)
    errors = []
    if not person_df['person_id'].notnull().all():
        errors.append("Missing person_id in person data")
    if not observation_df['person_id'].notnull().all():
        errors.append("Missing person_id in observation data")
    if person_df['person_id'].duplicated().any():
        errors.append("Duplicate person_id found in person data")
    from datetime import datetime
    current_year = datetime.now().year
    if (person_df['year_of_birth'] > current_year).any():
        errors.append("year_of_birth in the future found in person data")
    if not observation_df['person_id'].isin(person_df['person_id']).all():
        errors.append("Observation references person_id not in person table")
    if observation_df['observation_concept_id'].isnull().any():
        errors.append("Unmapped observation_concept_id found in observation data")
    if errors:
        print("Data Quality Issues Found:")
        for err in errors:
            print(f"- {err}")
        raise ValueError("Data quality checks failed. See errors above.")
    # Load data into database
    person_df.to_sql('person', engine, if_exists='append', index=False)
    observation_df.to_sql('observation', engine, if_exists='append', index=False)
    print("ETL complete: data loaded to OMOP tables.")
