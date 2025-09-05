import json
from ollama import Client

client = Client()

def fhir_to_omop_sql(fhir_json: dict, table: str):
    """
    Maps FHIR JSON resource to OMOP SQL INSERT statement using Llama 2 via Ollama.
    """
    prompt = f"""
    You are a biomedical data engineer.
    Map the following FHIR resource to an OMOP {table} INSERT statement.
    Use OMOP CDM v5.3 fields. If a field is missing, insert NULL.

    FHIR resource:
    {json.dumps(fhir_json, indent=2)}
    """
    response = client.generate(model='llama2', prompt=prompt)
    return response['response']

