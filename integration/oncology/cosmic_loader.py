# COSMIC Loader Example
import pandas as pd

def load_cosmic_mutations(file_path):
    # COSMIC data is often distributed as TSV/CSV
    df = pd.read_csv(file_path, sep='\t')
    # Filter or map columns as needed for OMOP or analysis
    return df

# Example usage:
# df = load_cosmic_mutations("data/external/CosmicMutantExport.tsv")
# print(df.head())
