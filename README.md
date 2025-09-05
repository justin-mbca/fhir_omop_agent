# FHIR → OMOP Agent + QA Copilot


This app demonstrates a local, LLM-powered pipeline for mapping FHIR resources to OMOP tables, running data quality checks, and experimenting with LLM prompts—all from a Streamlit GUI. The project is organized for extensibility, with a modular folder structure for future integrations (e.g., oncology DB, on-premise DB).

## Features

- Modular codebase for easy extension and maintenance
- LLM Chat: ask any question to the LLM (choose model for speed/quality)
- LLM Mapping Prompt Playground: experiment with custom prompts and any data (e.g., CSV columns, FHIR JSON) for OMOP mapping suggestions
- Oncology Data Loader Demos:
   - OncoKB: Load via API (institutional email required) or upload CSV
   - COSMIC: Upload TSV/CSV or load from public URL
   - cBioPortal: Load clinical/molecular data via API (study ID) or upload CSV; list and fetch available molecular profiles (mutation, copy number, mRNA, etc.)
- Fetch FHIR resources (Patient, Condition, Encounter, and more) from the public HAPI FHIR server
- Review FHIR resources in table format
- Map FHIR resources to OMOP tables (person, condition_occurrence, visit_occurrence) using robust Python logic with LLM fallback
- Run QA profiling on OMOP tables (ydata-profiling)
- Generate OMOP SQL from FHIR JSON using LLM (Llama 2, Mistral, TinyLlama via Ollama)

## Project Structure

```
fhir_omop_agent/
├── app.py                  # Main Streamlit app
├── core/                   # Core logic: mapping, QA, FHIR/OMOP sample generation
│   ├── fhir_to_omop.py
│   ├── qa_copilot.py
│   ├── fetch_fhir_samples.py
│   └── generate_omop_samples.py
├── utils/                  # Utility functions (db_utils.py, fhir_utils.py)
├── integration/            # Future integrations (oncology, on_premise)
│   ├── oncology/
│   └── on_premise/
├── data/                   # Sample FHIR/OMOP data, external data
│   ├── sample_fhir/
│   ├── sample_omop/
│   └── external/
├── mermaid_diagram.md      # System architecture diagram
└── README.md
```

## Setup
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   # Or manually: streamlit pandas ydata-profiling requests ollama
   ```
2. **Install Ollama and pull models:**
   ```bash
   # Install Ollama from https://ollama.com/
   ollama pull llama2
   ollama pull mistral
   ollama pull tinyllama
   ```
3. **Run the app:**
   ```bash
   streamlit run fhir_omop_agent/app.py
   ```

## Extending the Project

- Add new mapping logic or QA modules in `core/`
- Add utility functions in `utils/`
- Integrate external or on-premise data sources in `integration/`
- Place sample or external data in `data/`


## Usage

- **LLM Chat:** Ask any question to the LLM (choose model for speed/quality).
- **LLM Mapping Prompt Playground:** Enter a custom prompt and sample data (e.g., CSV columns, FHIR JSON) to get OMOP mapping suggestions from the LLM.
- **Oncology Data Loader Demos:**
   - **OncoKB:** Enter API token and gene, or upload a CSV file. Preview and analyze variant data.
   - **COSMIC:** Upload a COSMIC TSV/CSV file or enter a public URL. Preview and analyze mutation data.
   - **cBioPortal:** Enter a study ID to fetch clinical/molecular data via API, or upload a CSV. List and fetch available molecular profiles (mutation, copy number, mRNA, etc.).
- **FHIR Resource Viewer:** Fetch and review FHIR resources from the HAPI FHIR server. Select resource type and number of rows.
- **Map to OMOP:** After fetching Patient, Condition, or Encounter, click "Map to OMOP" to populate the OMOP SQLite database (`omop_demo.db`).
- **Run QA:** Select an OMOP table and run data profiling (QA) with ydata-profiling.

## Notes

- Modular structure supports future growth and integration with external data sources (e.g., oncology DB, on-premise OMOP, cBioPortal, COSMIC, OncoKB).
- The OMOP database is `omop_demo.db` in your project directory. It is dynamic and updated by the app.
- The app uses robust hard-coded mapping for speed, with LLM fallback for flexibility.
- You can add more OMOP tables and FHIR resource mappings as needed.
- LLM features (chat, mapping playground) are available at the top of the app for rapid prototyping and mapping suggestions.

## Requirements
- Python 3.11+
- Streamlit
- pandas
- ydata-profiling
- requests
- ollama (running locally)

## License
MIT
