
```mermaid
flowchart TD
    %% User Interaction
    U1([User: Streamlit GUI])

    %% Data Sources
    FHIR1([FHIR Server])
    ONCOKB([OncoKB API/CSV])
    COSMIC([COSMIC TSV/CSV/URL])
    CBIO([cBioPortal API/CSV])

    %% LLM/AI
    LLM1([LLM: Llama 2 / Mistral / TinyLlama])
    LLM2([LLM: Mapping/QA/Chat])

    %% OMOP/DB
    OMOP1([OMOP SQLite DB])
    QA([QA Copilot: ydata-profiling])

    %% Data Flow
    U1 -- "Fetch FHIR" --> FHIR1
    U1 -- "Load Oncology Data" --> ONCOKB
    U1 -- "Load Oncology Data" --> COSMIC
    U1 -- "Load Oncology Data" --> CBIO
    U1 -- "LLM Chat" --> LLM1
    U1 -- "LLM Mapping Playground" --> LLM2
    U1 -- "Map to OMOP (AI/hard-coded)" --> LLM2
    LLM2 -- "Suggest OMOP mapping / SQL" --> U1
    LLM1 -- "Answer / SQL" --> U1
    U1 -- "Insert/Map to OMOP" --> OMOP1
    U1 -- "Run QA" --> QA
    OMOP1 -- "Table Data" --> QA
    QA -- "QA Report" --> U1

    %% AI Emphasis
    classDef ai fill:#ffe4b2,stroke:#e67e22,stroke-width:2px;
    LLM1,LLM2,QA class ai;

    %% Notes
    %% LLM1: Used for chat, prompt playground, and mapping suggestions
    %% LLM2: Used for mapping, QA, and SQL generation
    %% QA: Automated profiling and data quality (AI-powered)
```

**Diagram: Technical & Data Process with AI/LLM Emphasis**
- User can interact with FHIR, OMOP, and oncology data sources (OncoKB, COSMIC, cBioPortal) via the GUI.
- LLM/AI is used for chat, mapping suggestions, QA, and SQL generation at multiple steps (highlighted in orange).
- Data flows from sources through AI-powered mapping and QA into OMOP, with results and reports returned to the user.
