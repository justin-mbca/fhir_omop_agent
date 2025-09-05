# OncoKB Loader Example
import requests
import pandas as pd

def fetch_oncokb_variants(api_token, gene='TP53'):
    url = f"https://www.oncokb.org/api/v1/genes/{gene}/variants"
    headers = {"Authorization": f"Bearer {api_token}"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    variants = response.json()
    return pd.DataFrame(variants)

# Example usage:
# df = fetch_oncokb_variants(api_token="YOUR_ONCOKB_TOKEN")
# df.to_csv("data/external/oncokb_tp53_variants.csv", index=False)
