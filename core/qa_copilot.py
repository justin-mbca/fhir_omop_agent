import pandas as pd
from ydata_profiling import ProfileReport

def run_quality_checks(csv_path: str, output_html: str):
    """
    Runs basic data profiling QA checks on OMOP-style dataset.
    """
    df = pd.read_csv(csv_path)
    profile = ProfileReport(df, title="OMOP QA Report", explorative=True)
    profile.to_file(output_html)
    return output_html

