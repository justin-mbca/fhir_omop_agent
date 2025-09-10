## Sample Data Files for Testing Upload Feature

You can use the following files in your project to test the "Upload Healthcare Data (CSV, Excel, JSON)" feature:

**CSV files:**
- `person.csv`
- `data/code_mapping_sample.csv`
- `data/condition_sample.csv`
- `data/observation_sample.csv`
- `data/person_sample.csv`
- `data/procedure_sample.csv`
- `data/external/cbioportal_brca_clinical.csv`
- `data/external/oncokb_tp53_variants.csv`

**JSON file:**
- `sample_fhir.json`

**Excel:**
- No `.xlsx` files included by default, but you can convert any CSV to Excel for testing.

**TSV:**
- `data/external/CosmicMutantExport.tsv` (convert to CSV or Excel if needed)

Use these files to test the upload and mapping features in the Streamlit app.
# Healthcare Data Interoperability Toolkit (FHIR Mapper + Validator) — Technical Blueprint

## 1. Stack & Key Libraries

- **Backend:** Python (FastAPI)
	- FastAPI (REST API)
	- Pydantic (data validation)
	- SQLAlchemy (ORM for SQLite/PostgreSQL)
- **FHIR Validation:**  
	- fhir.resources (for FHIR resource models/validation)
	- Optionally: fhirclient, or FHIR-Kit (if needed)
- **Frontend:**  
	- Streamlit (for rapid MVP UI)
	- Optionally: React (for future SaaS)
- **Storage:**  
	- SQLite (MVP, already present)
	- PostgreSQL (for production)
- **AI/LLM:**  
	- OpenAI API (GPT-4, for mapping suggestions/documentation)
- **Other:**  
	- pandas (CSV/Excel/JSON handling)
	- python-multipart (file uploads)

---

## 2. API Endpoints (FastAPI)

| Endpoint                  | Method | Description                                 |
|---------------------------|--------|---------------------------------------------|
| /upload                   | POST   | Upload CSV/Excel/JSON file                  |
| /map-fields               | POST   | Map uploaded fields to FHIR resources       |
| /validate                 | POST   | Validate mapped data against FHIR schema    |
| /export                   | GET    | Download mapped data as FHIR JSON           |
| /ai/suggest-mapping       | POST   | Get AI mapping suggestions for columns      |
| /ai/summarize-mapping     | POST   | Get AI-generated mapping documentation      |
| /auth/register, /auth/login | POST | User registration/login (basic auth)        |

---

## 3. Database Schema (SQLite)

- **users**
	- id (PK)
	- username
	- password_hash
	- email

- **datasets**
	- id (PK)
	- user_id (FK)
	- filename
	- upload_date
	- status (uploaded/mapped/validated/exported)
	- row_count

- **mappings**
	- id (PK)
	- dataset_id (FK)
	- original_field
	- fhir_resource
	- fhir_field
	- ai_suggestion (optional)

- **validation_results**
	- id (PK)
	- dataset_id (FK)
	- is_valid
	- errors (JSON)

---

## 4. UI Wireframe (Streamlit MVP)

- **Sidebar:**  
	- Login/Register
	- Upload Data
	- View Datasets

- **Main Area:**  
	1. Upload file (CSV/Excel/JSON)
	2. Field mapping table (manual + AI suggestions)
	3. Validation results (pass/fail, error messages)
	4. Export/download FHIR JSON
	5. AI-generated mapping summary

---

## 5. Core Workflow

1. **User uploads data file** (CSV/Excel/JSON)
2. **System parses columns** and presents mapping UI
3. **User maps fields** to FHIR resources/fields (with AI suggestions)
4. **Mapped data is validated** against FHIR schema (using fhir.resources)
5. **Validation results** shown (errors, warnings)
6. **User exports** mapped/validated data as FHIR JSON
7. **AI generates documentation** summarizing mapping/validation

---

## 6. AI Integration

- **Mapping Suggestions:**  
	- Use OpenAI API to suggest FHIR fields for each unmapped column (prompt: "Suggest FHIR resource/field for column: [column_name] in healthcare dataset")
- **Documentation Generation:**  
	- Use OpenAI API to summarize mapping and validation results in plain English

---

## 7. Monetization (MVP)

- **Free tier:**  
	- 1 dataset/day, up to 500 rows
- **Paid tier:**  
	- Unlimited datasets, API access, priority support

---

## 8. Next Steps

1. Scaffold FastAPI backend with endpoints above
2. Build Streamlit UI for upload, mapping, validation, export
3. Integrate fhir.resources for validation
4. Add OpenAI API integration for mapping suggestions/documentation
5. Implement user authentication (basic for MVP)
6. Deploy to AWS/Render

---

This blueprint provides a clear roadmap for building your MVP in 30 days. Adjust as needed for your goals and timeline.
