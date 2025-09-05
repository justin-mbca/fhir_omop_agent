```mermaid
graph TD
    subgraph User
        A1[Streamlit GUI]
    end
    subgraph FHIR
        B1[HAPI FHIR Server]
    end
    subgraph OMOP
        C1[SQLite DB: omop_demo.db]
        C2[QA Copilot (ydata-profiling)]
    end
    subgraph LLMs
        D1[Llama 2 (Ollama)]
        D2[Mistral (Ollama)]
        D3[TinyLlama (Ollama)]
    end

    A1 -- Fetch FHIR resources --> B1
    A1 -- Review & select resources --> A1
    A1 -- Map to OMOP (hard-coded or LLM fallback) --> C1
    A1 -- Run QA on OMOP table --> C2
    C2 -- QA report --> A1
    A1 -- LLM Prompt Playground --> D1
    A1 -- LLM Prompt Playground --> D2
    A1 -- LLM Prompt Playground --> D3
    A1 -- LLM Chat (model selectable) --> D1
    A1 -- LLM Chat (model selectable) --> D2
    A1 -- LLM Chat (model selectable) --> D3
    D1 -- SQL/Answer --> A1
    D2 -- SQL/Answer --> A1
    D3 -- SQL/Answer --> A1
```

**Diagram: FHIR → OMOP Agent + QA Copilot (with LLM chat and model selection)**
- Shows Streamlit GUI, FHIR server, OMOP DB, QA, and multiple LLMs.
- Reflects new features: LLM chat, prompt playground, model selection, and robust mapping.
