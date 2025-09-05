import sqlite3
import random
import datetime

def generate_condition_occurrence_samples(n=10):
    samples = []
    for i in range(n):
        person_id = random.randint(1, 5)
        condition_concept_id = random.choice([31967, 201826, 432791, 313217, 457661])
        condition_start_date = datetime.date(2023, 1, 1) + datetime.timedelta(days=random.randint(0, 365))
        condition_type_concept_id = random.choice([32020, 32021, 32022])
        stop_reason = random.choice(['', 'resolved', 'referred'])
        provider_id = random.randint(1, 3)
        visit_occurrence_id = random.randint(1, 10)
        sample = (
            person_id,
            condition_concept_id,
            str(condition_start_date),
            condition_type_concept_id,
            stop_reason,
            provider_id,
            visit_occurrence_id
        )
        samples.append(sample)
    return samples

def insert_samples_to_db(samples, db_path="omop_demo.db"):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    # Drop the table if it exists to avoid schema conflicts
    cur.execute("DROP TABLE IF EXISTS condition_occurrence;")
    cur.execute("""
        CREATE TABLE condition_occurrence (
            person_id INTEGER,
            condition_concept_id INTEGER,
            condition_start_date TEXT,
            condition_type_concept_id INTEGER,
            stop_reason TEXT,
            provider_id INTEGER,
            visit_occurrence_id INTEGER
        )
    """)
    cur.executemany("""
        INSERT INTO condition_occurrence (
            person_id, condition_concept_id, condition_start_date, condition_type_concept_id, stop_reason, provider_id, visit_occurrence_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, samples)
    conn.commit()
    conn.close()

if __name__ == "__main__":
    samples = generate_condition_occurrence_samples(n=20)
    insert_samples_to_db(samples)
    print(f"Inserted {len(samples)} sample rows into condition_occurrence table in omop_demo.db.")