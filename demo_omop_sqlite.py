import sqlite3

# Minimal OMOP condition_occurrence table schema for demo
schema = """
CREATE TABLE IF NOT EXISTS condition_occurrence (
    condition_id INTEGER PRIMARY KEY,
    subject_id INTEGER,
    encounter_id INTEGER,
    start_date_time TEXT,
    stop_date_time TEXT,
    status TEXT,
    code TEXT,
    code_system TEXT,
    code_value TEXT,
    display_name TEXT,
    concept_code TEXT,
    concept_definition TEXT,
    severity INTEGER,
    onset_datetime TEXT
);
"""

# Example SQL insert (from your GUI output)
sql_insert = """
INSERT INTO condition_occurrence (
    condition_id, 
    subject_id, 
    encounter_id, 
    start_date_time, 
    stop_date_time, 
    status, 
    code, 
    code_system, 
    code_value, 
    display_name, 
    concept_code, 
    concept_definition, 
    severity, 
    onset_datetime
) VALUES (
  12345, -- condition ID
  67890, -- subject ID
   NULL, -- encounter ID (omitted since no encounter is provided)
   '2020-05-01', -- onset date/time
  NULL, -- stop date/time (omitted since no stop date is provided)
  'active', -- status
  '44054006', -- code
  'http://snomed.info/sct', -- code system
  'Diabetes mellitus type 2', -- code value
  'Diabetes mellitus type 2', -- display name
  NULL, -- concept code (omitted since no concept code is provided)
  NULL, -- concept definition (omitted since no concept definition is provided)
  1, -- severity
  '2020-05-01' -- onset date/time
);
"""

def main():
    conn = sqlite3.connect('omop_demo.db')
    cur = conn.cursor()
    cur.execute(schema)
    cur.execute(sql_insert)
    conn.commit()
    # Show inserted row
    cur.execute("SELECT * FROM condition_occurrence")
    for row in cur.fetchall():
        print(row)
    conn.close()

if __name__ == "__main__":
    main()
