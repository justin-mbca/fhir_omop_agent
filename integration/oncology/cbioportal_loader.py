# cBioPortal Loader Example
import requests
import pandas as pd

def fetch_cbioportal_study(study_id, base_url="https://www.cbioportal.org/api"):
    # Example: fetch sample clinical data for a study
    url = f"{base_url}/studies/{study_id}/clinical-data"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return pd.DataFrame(data['clinicalData'])

# Example usage:
# df = fetch_cbioportal_study("brca_tcga")
# df.to_csv("data/external/cbioportal_brca_clinical.csv", index=False)
