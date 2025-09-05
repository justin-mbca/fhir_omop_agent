# Database utility stubs for OMOP and external DBs

def connect_omop_db(db_path="omop_demo.db"):
    import sqlite3
    return sqlite3.connect(db_path)
