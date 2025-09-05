# FHIR → OMOP Agent + QA Copilot


This app demonstrates a local, LLM-powered pipeline for mapping FHIR resources to OMOP tables, running data quality checks, and experimenting with LLM prompts—all from a Streamlit GUI. The project is organized for extensibility, with a modular folder structure for future integrations (e.g., oncology DB, on-premise DB).

## Features

- Modular codebase for easy extension and maintenance
- Fetch FHIR resources (Patient, Condition, Encounter, and more) from the public HAPI FHIR server
- Review FHIR resources in table format
- Map FHIR resources to OMOP tables (person, condition_occurrence, visit_occurrence) using robust Python logic with LLM fallback
- Run QA profiling on OMOP tables (ydata-profiling)
- Generate OMOP SQL from FHIR JSON using LLM (Llama 2, Mistral, TinyLlama via Ollama)
- LLM Prompt Playground: experiment with custom prompts and FHIR JSON
- LLM Chat: ask any question to the LLM (choose model for speed/quality)

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
- **FHIR Resource Viewer:** Fetch and review FHIR resources from the HAPI FHIR server. Select resource type and number of rows.
- **Map to OMOP:** After fetching Patient, Condition, or Encounter, click "Map to OMOP" to populate the OMOP SQLite database (`omop_demo.db`).
- **Run QA:** Select an OMOP table and run data profiling (QA) with ydata-profiling.
- **LLM Mapping Prompt Playground:** Enter a custom prompt, FHIR JSON, and OMOP table to see LLM-generated SQL or mapping.
- **LLM Chat:** Ask any question to the LLM. Choose a smaller model for faster responses.

## Notes

- Modular structure supports future growth and integration with external data sources (e.g., oncology DB, on-premise OMOP).
- The OMOP database is `omop_demo.db` in your project directory. It is dynamic and updated by the app.
- The app uses robust hard-coded mapping for speed, with LLM fallback for flexibility.
- You can add more OMOP tables and FHIR resource mappings as needed.

## Requirements
- Python 3.11+
- Streamlit
- pandas
- ydata-profiling
- requests
- ollama (running locally)

## License
MIT
