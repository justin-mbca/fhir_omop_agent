
import pandas as pd
import matplotlib.pyplot as plt
import os
from utils.db_utils import get_db_engine
from utils.config_utils import load_config

__all__ = ["run_analytics"]

def run_analytics(db_type=None, db_path=None, pg_settings=None, config_path="config.yaml"):
    """
    Analytics and visualization for OMOP CDM tables
    Refactored for MCP orchestrator compatibility.
    """
    config = load_config(config_path)
    db_type = db_type or config['database']['backend']
    if db_type == 'sqlite':
        db_path = db_path or config['database']['sqlite_path']
        engine = get_db_engine(db_type=db_type, db_path=db_path)
    else:
        pg_settings = pg_settings or config['database']['postgresql']
        engine = get_db_engine(db_type=db_type, pg_settings=pg_settings)
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    docs_dir = os.path.join(base_dir, config['docs']['output_dir'])
    # Persons by gender
    gender_df = pd.read_sql("SELECT gender_concept_id, COUNT(*) as count FROM person GROUP BY gender_concept_id", engine)
    plt.figure()
    gender_df.plot.bar(x='gender_concept_id', y='count', legend=False)
    plt.title('Number of Persons by Gender Concept ID')
    plt.xlabel('Gender Concept ID')
    plt.ylabel('Count')
    plt.tight_layout()
    plt.savefig(os.path.join(docs_dir, 'persons_by_gender.png'))
    # Age distribution
    age_df = pd.read_sql("SELECT year_of_birth FROM person", engine)
    age_df['age'] = pd.Timestamp.now().year - age_df['year_of_birth']
    plt.figure()
    age_df['age'].plot.hist(bins=10)
    plt.title('Age Distribution')
    plt.xlabel('Age')
    plt.ylabel('Number of Persons')
    plt.tight_layout()
    plt.savefig(os.path.join(docs_dir, 'age_distribution.png'))
    # Observations per year
    obs_year_df = pd.read_sql("SELECT strftime('%Y', observation_date) AS year, COUNT(*) as count FROM observation GROUP BY year ORDER BY year", engine)
    plt.figure()
    obs_year_df.plot.bar(x='year', y='count', legend=False)
    plt.title('Observations per Year')
    plt.xlabel('Year')
    plt.ylabel('Number of Observations')
    plt.tight_layout()
    plt.savefig(os.path.join(docs_dir, 'observations_per_year.png'))
    print(f"Analytics complete: charts saved to {docs_dir}/.")


# Script usage: python analytics_visualization.py
if __name__ == "__main__":
    run_analytics()
