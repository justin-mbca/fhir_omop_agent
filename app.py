

import streamlit as st
import streamlit.components.v1 as components
import json
import pandas as pd
import sqlite3
import os
from core.fhir_to_omop import fhir_to_omop_sql, client
from core.qa_copilot import run_quality_checks
from utils.db_utils import get_db_engine
from utils.fhir_utils import extract_patient_id
from utils.config_utils import load_config
from core.orchestration.mcp_orchestrator import MCPOrchestrator

# Initialize SQLAlchemy engine for database access
engine = get_db_engine()

# --- General Data Upload (CSV, Excel, JSON) ---
st.title("Healthcare Data Interoperability Toolkit")
st.header("Upload Healthcare Data (CSV, Excel, JSON)")
uploaded_data = st.file_uploader(
    "Upload your healthcare data file",
    type=["csv", "xlsx", "json"],
    help="Supported formats: CSV, Excel (.xlsx), JSON"
)

if uploaded_data is not None:
    filetype = uploaded_data.name.split('.')[-1].lower()
    try:
        if filetype == "csv":
            df = pd.read_csv(uploaded_data)
        elif filetype == "xlsx":
            df = pd.read_excel(uploaded_data)
        elif filetype == "json":
            # Try to load as JSON array or object
            data = json.load(uploaded_data)
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # If dict, try to find a list value
                for v in data.values():
                    if isinstance(v, list):
                        df = pd.DataFrame(v)
                        break
                else:
                    df = pd.DataFrame([data])
            else:
                st.error("Unsupported JSON structure.")
                df = None
        else:
            st.error("Unsupported file type.")
            df = None
        if df is not None:
            st.success(f"Loaded {len(df)} rows, {len(df.columns)} columns.")
            st.dataframe(df.head(20))
            st.markdown("---")
            st.header("Map Columns to FHIR Resources/Fields")
            # Example FHIR resources and fields (expand as needed)
            fhir_resources = {
                "Patient": ["id", "name", "gender", "birthDate"],
                "Observation": ["id", "code", "value", "effectiveDateTime"],
                "Condition": ["id", "code", "onsetDateTime", "subject"],
                "Procedure": ["id", "code", "performedDateTime", "subject"]
            }
            mapping = {}
            for col in df.columns:
                st.subheader(f"Column: `{col}`")
                resource = st.selectbox(f"Select FHIR resource for `{col}`", list(fhir_resources.keys()), key=f"resource_{col}")
                field = st.selectbox(f"Select FHIR field for `{col}`", fhir_resources[resource], key=f"field_{col}")
                ai_suggest = st.button(f"AI Suggest for `{col}`", key=f"ai_{col}")
                if ai_suggest:
                    # Placeholder for AI suggestion logic
                    st.info(f"[AI] Suggestion: Map `{col}` to {resource}.{field}")
                mapping[col] = {"resource": resource, "field": field}
            st.markdown("---")
            st.write("### Current Mapping")
            st.json(mapping)
    except Exception as e:
        st.error(f"Failed to load file: {e}")

# --- Cohort Selection & Filtering ---
st.markdown("---")
st.header("Cohort Selection & Filtering")
st.write("Interactively filter OMOP tables and view the results. Useful for cohort discovery and data exploration.")

table_options = ["person", "observation", "condition_occurrence", "procedure_occurrence"]
selected_table = st.selectbox("Select OMOP table to filter", table_options)

df = None
try:
    df = pd.read_sql(f"SELECT * FROM {selected_table}", engine)
except Exception as e:
    st.info(f"Could not load {selected_table} table: {e}")

if df is not None:
    st.write(f"**{selected_table} table: {len(df)} rows**")
    # Show filter widgets for common columns
    filter_cols = [col for col in df.columns if df[col].dtype in ["int64", "float64"] or "date" in col or "concept_id" in col]
    filters = {}
    for col in filter_cols:
        if "date" in col:
            min_date = pd.to_datetime(df[col], errors="coerce").min()
            max_date = pd.to_datetime(df[col], errors="coerce").max()
            # Default to full range if possible
            if pd.isnull(min_date) or pd.isnull(max_date):
                val = (None, None)
            else:
                val = st.date_input(f"Filter {col}", value=(min_date, max_date), min_value=min_date, max_value=max_date)
            filters[col] = val
        elif "concept_id" in col:
            unique_vals = sorted(df[col].dropna().unique())
            if unique_vals:
                val = st.multiselect(f"Filter {col}", unique_vals, default=unique_vals)
                filters[col] = val
            else:
                st.info(f"Column {col} has no options to select.")
                filters[col] = None
        else:
            min_val = int(df[col].min()) if not pd.isnull(df[col].min()) else 0
            max_val = int(df[col].max()) if not pd.isnull(df[col].max()) else 0
            if min_val < max_val:
                val = st.slider(f"Filter {col}", min_val, max_val, (min_val, max_val))
                filters[col] = val
            else:
                st.info(f"Column {col} has a single value: {min_val}")
                filters[col] = (min_val, max_val)
    # Apply filters
    df_filtered = df.copy()
    for col, val in filters.items():
        if "date" in col:
            if isinstance(val, tuple) and len(val) == 2:
                df_filtered = df_filtered[(pd.to_datetime(df_filtered[col], errors="coerce") >= pd.to_datetime(val[0])) & (pd.to_datetime(df_filtered[col], errors="coerce") <= pd.to_datetime(val[1]))]
            # else: skip filtering for this column
        elif "concept_id" in col:
            if val is not None:
                df_filtered = df_filtered[df_filtered[col].isin(val)]
            # else: skip filtering for this column
        else:
            if isinstance(val, tuple) and len(val) == 2:
                df_filtered = df_filtered[(df_filtered[col] >= val[0]) & (df_filtered[col] <= val[1])]
            # else: skip filtering for this column
    st.dataframe(df_filtered)
    st.write(f"Filtered rows: {len(df_filtered)}")



import streamlit as st
import streamlit.components.v1 as components
import json
import pandas as pd
import sqlite3
import os
from core.fhir_to_omop import fhir_to_omop_sql, client
from core.qa_copilot import run_quality_checks
from utils.db_utils import get_db_engine
from utils.fhir_utils import extract_patient_id
from utils.config_utils import load_config
from core.orchestration.mcp_orchestrator import MCPOrchestrator

# Load config at the very top so it's available for sidebar and all logic
config = load_config()

st.sidebar.header("Database Backend")
default_backend = config['database']['backend']
db_type = st.sidebar.selectbox("Select database backend", ["sqlite", "postgresql"], index=0 if default_backend=="sqlite" else 1)
if db_type == "sqlite":
    default_sqlite = config['database']['sqlite_path']
    db_path = st.sidebar.text_input("SQLite DB Path", value=default_sqlite)
    pg_settings = None
else:
    pg_conf = config['database']['postgresql']
    db_path = None
    pg_settings = {
        'user': st.sidebar.text_input("PostgreSQL User", value=pg_conf.get('user', 'clinical_user')),
        'password': st.sidebar.text_input("PostgreSQL Password", type="password", value=pg_conf.get('password', 'StrongPassword123')),
        'host': st.sidebar.text_input("PostgreSQL Host", value=pg_conf.get('host', 'localhost')),
        'port': st.sidebar.text_input("PostgreSQL Port", value=str(pg_conf.get('port', '5432'))),
        'db': st.sidebar.text_input("PostgreSQL DB Name", value=pg_conf.get('db', 'clinical_demo')),
    }

# Load config and instantiate orchestrator
config = load_config()
orchestrator = MCPOrchestrator(config_path="config.yaml")

import requests
from core.etl import run_etl, run_analytics
st.header("ETL & Analytics Jobs")
st.write("Run OMOP ETL and analytics directly from the app. Uses sample data and your selected backend (default: SQLite).")

col1, col2 = st.columns(2)
with col1:
    if st.button("Run ETL (Load Sample Data)"):
        with st.spinner("Running ETL job..."):
            try:
                orchestrator.run_etl()
                st.success("ETL complete: data loaded to OMOP tables.")
            except Exception as e:
                st.error(f"ETL failed: {e}")
with col2:
    if st.button("Run Analytics (Generate Charts)"):
        with st.spinner("Running analytics job..."):
            try:
                orchestrator.run_analytics()
                st.success("Analytics complete: charts saved to docs/.")
                st.subheader("Analytics Results (Charts)")
                chart_dir = os.path.join(os.path.dirname(__file__), "docs")
                chart_files = [
                    ("Persons by Gender", "persons_by_gender.png"),
                    ("Age Distribution", "age_distribution.png"),
                    ("Observations per Year", "observations_per_year.png"),
                    ("Top 10 Conditions", "top_conditions.png"),
                    ("Conditions per Person", "conditions_per_person.png"),
                    ("Condition Occurrences by Year", "condition_by_year.png"),
                    ("Top 10 Procedures", "top_procedures.png"),
                    ("Procedures per Person", "procedures_per_person.png"),
                    ("Procedures by Year", "procedure_by_year.png")
                ]
                for title, fname in chart_files:
                    fpath = os.path.join(chart_dir, fname)
                    if os.path.exists(fpath):
                        st.markdown(f"**{title}:**")
                        st.image(fpath)
                    else:
                        st.info(f"Chart not found: {fname}")
            except Exception as e:
                st.error(f"Analytics failed: {e}")
# Always show OMOP data preview after ETL/analytics, regardless of which button was clicked
engine = get_db_engine(db_type=db_type, db_path=db_path, pg_settings=pg_settings)

st.subheader("Preview: person table")
try:
    df_person = pd.read_sql("SELECT * FROM person LIMIT 10", engine)
    st.dataframe(df_person)
except Exception as e:
    st.info(f"Could not load person table: {e}")

st.subheader("Preview: observation table")
try:
    df_obs = pd.read_sql("SELECT * FROM observation LIMIT 10", engine)
    st.dataframe(df_obs)
except Exception as e:
    st.info(f"Could not load observation table: {e}")

st.subheader("Preview: condition_occurrence table")
try:
    df_cond = pd.read_sql("SELECT * FROM condition_occurrence LIMIT 10", engine)
    st.dataframe(df_cond)
except Exception as e:
    st.info(f"Could not load condition_occurrence table: {e}")

st.subheader("Preview: procedure_occurrence table")
try:
    df_proc = pd.read_sql("SELECT * FROM procedure_occurrence LIMIT 10", engine)
    st.dataframe(df_proc)
except Exception as e:
    st.info(f"Could not load procedure_occurrence table: {e}")


# --- LLM Q&A Chat Box ---
st.markdown("---")
st.header("Ask the LLM (Chat)")
chat_models = ["mistral", "tinyllama", "llama2"]
chat_model = st.selectbox("Choose LLM model for chat", chat_models, index=0)
user_question = st.text_area("Ask any question to the LLM", value="", height=80)
if st.button("Ask LLM"):
    if user_question.strip():
        st.info(f"Sending question to LLM model: {chat_model} ...")
        response = client.generate(model=chat_model, prompt=user_question)
        st.subheader("LLM Answer")
        st.write(response['response'])
    else:
        st.warning("Please enter a question.")
st.markdown("---")

st.header("LLM Mapping Prompt Playground")
st.write("Use this tool to experiment with LLM prompts for FHIR → OMOP mapping or any data mapping. Enter a prompt and sample data, and see the LLM's output. Useful for learning and tuning.")
mapping_models = ["llama2", "mistral", "tinyllama"]
mapping_model = st.selectbox("Choose LLM model for mapping", mapping_models, index=0)
default_prompt = "You are a biomedical data engineer. Map the following data to OMOP. Suggest the best OMOP table and field mapping for each column. Output as a table with columns: CSV Column, OMOP Table, OMOP Field, Mapping Rationale."
custom_prompt = st.text_area("Prompt to LLM", value=default_prompt, height=100)
sample_data = st.text_area("Sample data (e.g., column names or JSON)", value="['patientId', 'age', 'gender', 'mutation', 'diagnosis']", height=100)

if st.button("Run LLM Mapping"):
    try:
        # Use orchestrator for LLM mapping
        # Accept both JSON and CSV-style input for demo
        try:
            fhir_json = json.loads(sample_data)
        except Exception:
            fhir_json = {"columns": sample_data}
        sql = orchestrator.run_llm_mapping(fhir_json, table="person")
        st.subheader("LLM Output (OMOP SQL Suggestion)")
        st.code(sql)
    except Exception as e:
        st.error(f"Error: {e}")

# --- Oncology Data Loader Demos ---
st.markdown("---")
st.header("Oncology Data Loader Demos")
st.write("Load and preview data from OncoKB, COSMIC, and cBioPortal using built-in loaders.")

oncology_source = st.selectbox("Select Oncology Data Source", ["OncoKB", "COSMIC", "cBioPortal"])

if oncology_source == "OncoKB":
    st.subheader("OncoKB Variant Loader")
    st.write("You can either use the API (institutional email required) or upload a CSV file (e.g., sample in data/external/oncokb_tp53_variants.csv).")
    api_token = st.text_input("OncoKB API Token", type="password")
    gene = st.text_input("Gene Symbol", value="TP53")
    uploaded_oncokb_csv = st.file_uploader("Upload OncoKB CSV File", type=["csv"])
    if uploaded_oncokb_csv is not None:
        import pandas as pd
        df_oncokb = pd.read_csv(uploaded_oncokb_csv)
        st.write(df_oncokb.head())
    elif st.button("Load OncoKB Variants", key="oncokb_load") and api_token:
        try:
            from integration.oncology.oncokb_loader import fetch_oncokb_variants
            df_oncokb = fetch_oncokb_variants(api_token, gene)
            st.write(df_oncokb.head())
        except Exception as e:
            st.error(f"Failed to load OncoKB data: {e}")
    elif st.button("Load OncoKB Variants", key="oncokb_warn"):
        st.warning("Please enter your OncoKB API token or upload a CSV file.")

elif oncology_source == "COSMIC":
    st.subheader("COSMIC Mutation Loader")
    st.write("Upload a COSMIC TSV file or enter a public COSMIC download URL (if available). Note: Most COSMIC data is distributed as files, not via API.")
    cosmic_file = st.file_uploader("Upload COSMIC TSV File", type=["tsv", "csv"])
    cosmic_url = st.text_input("Or enter COSMIC TSV URL (optional)")
    if cosmic_file is not None:
        try:
            import pandas as pd
            from integration.oncology.cosmic_loader import load_cosmic_mutations
            df_cosmic = load_cosmic_mutations(cosmic_file)
            st.write(df_cosmic.head())
        except Exception as e:
            st.error(f"Failed to load COSMIC data: {e}")
    elif cosmic_url:
        try:
            import pandas as pd
            df_cosmic = pd.read_csv(cosmic_url, sep='\t')
            st.write(df_cosmic.head())
        except Exception as e:
            st.error(f"Failed to load COSMIC data from URL: {e}")

elif oncology_source == "cBioPortal":
    st.subheader("cBioPortal Study Loader")
    st.write("You can use the API (study ID) or upload a CSV file (e.g., sample in data/external/cbioportal_brca_clinical.csv). You can also list and fetch other data types (mutation, copy number, etc.) for a study.")
    study_id = st.text_input("cBioPortal Study ID", value="brca_tcga")
    uploaded_cbio_csv = st.file_uploader("Upload cBioPortal CSV File", type=["csv"])
    if uploaded_cbio_csv is not None:
        import pandas as pd
        df_cbio = pd.read_csv(uploaded_cbio_csv)
        st.write(df_cbio.head())
    elif st.button("Load cBioPortal Study from API"):
        try:
            # import requests  # Removed unnecessary import
            import pandas as pd
            api_url = f"https://www.cbioportal.org/api/studies/{study_id}/clinical-data"
            resp = requests.get(api_url)
            resp.raise_for_status()
            data = resp.json()
            # cBioPortal API returns a list of dicts
            if isinstance(data, list):
                df_cbio = pd.DataFrame(data)
            elif isinstance(data, dict) and 'clinicalData' in data:
                df_cbio = pd.DataFrame(data['clinicalData'])
            else:
                raise ValueError("Unexpected cBioPortal API response format.")
            st.write(df_cbio.head())
        except Exception as e:
            st.error(f"Failed to load cBioPortal data from API: {e}")


    # List available molecular profiles (data types) and fetch data using session state
    if 'cbioportal_profiles' not in st.session_state:
        st.session_state['cbioportal_profiles'] = []
    if 'cbioportal_selected_profile' not in st.session_state:
        st.session_state['cbioportal_selected_profile'] = ''

    if st.button("List Available Data Types (Molecular Profiles)"):
        try:
            # import requests  # Removed unnecessary import
            profiles_url = f"https://www.cbioportal.org/api/studies/{study_id}/molecular-profiles"
            resp = requests.get(profiles_url)
            resp.raise_for_status()
            profiles = resp.json()
            if profiles:
                # Store both profileId and alterationType for endpoint selection
                st.session_state['cbioportal_profiles_full'] = profiles
                profile_ids = [p['molecularProfileId'] for p in profiles]
                st.session_state['cbioportal_profiles'] = profile_ids
                st.success("Profiles loaded. Select a profile below.")
            else:
                st.session_state['cbioportal_profiles'] = []
                st.session_state['cbioportal_profiles_full'] = []
                st.info("No molecular profiles found for this study.")
        except Exception as e:
            st.error(f"Failed to list molecular profiles: {e}")

    if st.session_state['cbioportal_profiles']:
        selected_profile = st.selectbox(
            "Select a molecular profile to fetch data",
            st.session_state['cbioportal_profiles'],
            key="cbioportal_profile_select",
            index=st.session_state['cbioportal_profiles'].index(st.session_state['cbioportal_selected_profile']) if st.session_state['cbioportal_selected_profile'] in st.session_state['cbioportal_profiles'] else 0
        )
        st.session_state['cbioportal_selected_profile'] = selected_profile
        if st.button("Fetch Data for Selected Profile"):
            try:
                # import requests  # Removed unnecessary import
                # Find the selected profile's alteration type
                profiles_full = st.session_state.get('cbioportal_profiles_full', [])
                profile_info = next((p for p in profiles_full if p['molecularProfileId'] == selected_profile), None)
                if not profile_info:
                    st.error("Profile info not found.")
                else:
                    alteration_type = profile_info.get('molecularAlterationType', '').upper()
                    # Get sample list
                    sample_list_url = f"https://www.cbioportal.org/api/studies/{study_id}/sample-lists"
                    sample_resp = requests.get(sample_list_url)
                    sample_resp.raise_for_status()
                    sample_lists = sample_resp.json()
                    if sample_lists:
                        sample_list_id = sample_lists[0]['sampleListId']
                        # Choose endpoint based on alteration type
                        if alteration_type == 'MUTATION_EXTENDED':
                            endpoint = 'mutations'
                        elif alteration_type == 'COPY_NUMBER_ALTERATION':
                            endpoint = 'discrete-copy-number'
                        elif alteration_type == 'MRNA_EXPRESSION':
                            endpoint = 'mRNA-expr'
                        else:
                            endpoint = None
                        if endpoint:
                            data_url = f"https://www.cbioportal.org/api/molecular-profiles/{selected_profile}/{endpoint}?sampleListId={sample_list_id}"
                            data_resp = requests.get(data_url)
                            data_resp.raise_for_status()
                            data = data_resp.json()
                            st.write(f"Data for {selected_profile} ({alteration_type}, first 10 records):")
                            st.write(data[:10] if isinstance(data, list) else data)
                        else:
                            st.info(f"No supported endpoint for alteration type: {alteration_type}")
                    else:
                        st.info("No sample lists found for this study.")
            except Exception as e:
                st.error(f"Failed to fetch data for selected profile: {e}")


st.title("FHIR → OMOP Agent + QA Copilot")

# --- FHIR Resource Viewer ---
st.header("View FHIR Resources from HAPI FHIR Server")
FHIR_BASE = "https://hapi.fhir.org/baseR4"
resource_types = [
    "Account", "ActivityDefinition", "AdverseEvent", "AllergyIntolerance", "Appointment", "AppointmentResponse", "AuditEvent", "Basic", "Binary", "BiologicallyDerivedProduct", "BodyStructure", "Bundle", "CapabilityStatement", "CarePlan", "CareTeam", "CatalogEntry", "ChargeItem", "ChargeItemDefinition", "Claim", "ClaimResponse", "ClinicalImpression", "CodeSystem", "Communication", "CommunicationRequest", "CompartmentDefinition", "Composition", "ConceptMap", "Condition", "Consent", "Contract", "Coverage", "CoverageEligibilityRequest", "CoverageEligibilityResponse", "DetectedIssue", "Device", "DeviceDefinition", "DeviceMetric", "DeviceRequest", "DeviceUseStatement", "DiagnosticReport", "DocumentManifest", "DocumentReference", "EffectEvidenceSynthesis", "Encounter", "Endpoint", "EnrollmentRequest", "EnrollmentResponse", "EpisodeOfCare", "EventDefinition", "Evidence", "EvidenceVariable", "ExampleScenario", "ExplanationOfBenefit", "FamilyMemberHistory", "Flag", "Goal", "GraphDefinition", "Group", "GuidanceResponse", "HealthcareService", "ImagingStudy", "Immunization", "ImmunizationEvaluation", "ImmunizationRecommendation", "ImplementationGuide", "InsurancePlan", "Invoice", "Library", "Linkage", "List", "Location", "Measure", "MeasureReport", "Media", "Medication", "MedicationAdministration", "MedicationDispense", "MedicationKnowledge", "MedicationRequest", "MedicationStatement", "MedicinalProduct", "MedicinalProductAuthorization", "MedicinalProductContraindication", "MedicinalProductIndication", "MedicinalProductIngredient", "MedicinalProductInteraction", "MedicinalProductManufactured", "MedicinalProductPackaged", "MedicinalProductPharmaceutical", "MedicinalProductUndesirableEffect", "MessageDefinition", "MessageHeader", "MolecularSequence", "NamingSystem", "NutritionOrder", "Observation", "ObservationDefinition", "OperationDefinition", "OperationOutcome", "Organization", "OrganizationAffiliation", "Parameters", "Patient", "PaymentNotice", "PaymentReconciliation", "Person", "PlanDefinition", "Practitioner", "PractitionerRole", "Procedure", "Provenance", "Questionnaire", "QuestionnaireResponse", "RelatedPerson", "RequestGroup", "ResearchDefinition", "ResearchElementDefinition", "ResearchStudy", "ResearchSubject", "RiskAssessment", "RiskEvidenceSynthesis", "Schedule", "SearchParameter", "ServiceRequest", "Slot", "Specimen", "SpecimenDefinition", "StructureDefinition", "StructureMap", "Subscription", "Substance", "SubstanceNucleicAcid", "SubstancePolymer", "SubstanceProtein", "SubstanceReferenceInformation", "SubstanceSourceMaterial", "SubstanceSpecification", "SupplyDelivery", "SupplyRequest", "Task", "TerminologyCapabilities", "TestReport", "TestScript", "ValueSet", "VerificationResult", "VisionPrescription"
]
resource_type = st.selectbox("Select FHIR resource type", resource_types)
num_rows = st.slider("Number of resources to fetch", 1, 20, 5)
if 'resources' not in st.session_state:
    st.session_state['resources'] = []
if 'last_resource_type' not in st.session_state:
    st.session_state['last_resource_type'] = None

if st.button("Fetch FHIR Resources"):
    url = f"{FHIR_BASE}/{resource_type}?_count={num_rows}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        bundle = resp.json()
        resources = [entry["resource"] for entry in bundle.get("entry", [])]
        st.session_state['resources'] = resources
        st.session_state['last_resource_type'] = resource_type
    except Exception as e:
        st.error(f"Failed to fetch FHIR resources: {e}")

# Always show table if resources are present in session_state
resources = st.session_state['resources']
last_resource_type = st.session_state['last_resource_type']
if resources:
    st.write(f"Showing {len(resources)} {last_resource_type} resources:")
    try:
        import pandas as pd
        df = pd.json_normalize(resources)
        st.dataframe(df)
    except Exception as e:
        st.info("Could not display as table. Showing raw JSON instead.")
        st.json(resources)

# --- Map to OMOP ---

# Hybrid mapping: try hard-coded, fallback to LLM if error
def map_patient_to_person(resource):
    try:
        # Map FHIR Patient resource to OMOP person table (7 columns)
        # Fallback to None if not present
        def to_int(val):
            try:
                return int(val)
            except (TypeError, ValueError):
                return None

        birth_date = resource.get('birthDate')
        year = to_int(birth_date[:4]) if birth_date else None
        month = to_int(birth_date[5:7]) if birth_date and len(birth_date) >= 7 else None
        day = to_int(birth_date[8:10]) if birth_date and len(birth_date) >= 10 else None

        # OMOP expects integer person_id, gender_concept_id, race_concept_id, ethnicity_concept_id
        person_id = to_int(resource.get('id'))
        gender_concept_id = None  # Could map from gender string if desired
        race_concept_id = None
        ethnicity_concept_id = None

        return (
            person_id,
            gender_concept_id,
            year,
            month,
            day,
            race_concept_id,
            ethnicity_concept_id
        )
    except Exception:
        # Fallback: use LLM to generate SQL, parse values
        sql = fhir_to_omop_sql(resource, 'person')
        import re
        m = re.search(r"VALUES ?\((.*?)\)", sql, re.DOTALL)
        if m:
            vals = [v.strip().strip("'\"") for v in m.group(1).split(',')]
            # Pad/truncate to 7 values
            vals = (vals + [None]*7)[:7]
            return tuple(vals)
        return (None, None, None, None, None, None, None)

def map_condition_to_condition_occurrence(resource):
    try:
        subject = resource.get('subject', {})
        code = resource.get('code', {})
        coding = code.get('coding', [{}])[0]
        return (
            resource.get('id'),
            subject.get('reference'),
            coding.get('code'),
            coding.get('system'),
            resource.get('onsetDateTime'),
            resource.get('recordedDate')
        )
    except Exception:
        sql = fhir_to_omop_sql(resource, 'condition_occurrence')
        import re
        m = re.search(r"VALUES ?\((.*?)\)", sql, re.DOTALL)
        if m:
            vals = [v.strip().strip("'\"") for v in m.group(1).split(',')]
            return tuple(vals)
        return (None, None, None, None, None, None)

def map_encounter_to_visit_occurrence(resource):
    try:
        subject = resource.get('subject', {})
        period = resource.get('period', {})
        type_list = resource.get('type', [{}])
        coding = type_list[0].get('coding', [{}])[0]
        return (
            resource.get('id'),
            subject.get('reference'),
            period.get('start'),
            period.get('end'),
            coding.get('code')
        )
    except Exception:
        sql = fhir_to_omop_sql(resource, 'visit_occurrence')
        import re
        m = re.search(r"VALUES ?\((.*?)\)", sql, re.DOTALL)
        if m:
            vals = [v.strip().strip("'\"") for v in m.group(1).split(',')]
            return tuple(vals)
        return (None, None, None, None, None)

if resources and last_resource_type in ["Patient", "Condition", "Encounter"]:
    if st.button(f"Map {last_resource_type} to OMOP"):
        conn = sqlite3.connect("omop_demo.db")
        cur = conn.cursor()
        if last_resource_type == "Patient":
            cur.execute("""
                CREATE TABLE IF NOT EXISTS person (
                    person_id INTEGER PRIMARY KEY,
                    gender_concept_id INTEGER,
                    year_of_birth INTEGER,
                    month_of_birth INTEGER,
                    day_of_birth INTEGER,
                    race_concept_id INTEGER,
                    ethnicity_concept_id INTEGER
                )
            """)
            rows = [map_patient_to_person(r) for r in resources]
            cur.executemany("INSERT OR REPLACE INTO person VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
            st.success(f"Inserted {len(rows)} Patient resources into OMOP person table.")
        elif last_resource_type == "Condition":
            cur.execute("""
                CREATE TABLE IF NOT EXISTS condition_occurrence (
                    condition_id TEXT PRIMARY KEY,
                    person_ref TEXT,
                    code TEXT,
                    code_system TEXT,
                    onset_date TEXT,
                    recorded_date TEXT
                )
            """)
            rows = [map_condition_to_condition_occurrence(r) for r in resources]
            cur.executemany("INSERT OR REPLACE INTO condition_occurrence VALUES (?, ?, ?, ?, ?, ?)", rows)
            st.success(f"Inserted {len(rows)} Condition resources into OMOP condition_occurrence table.")
        elif last_resource_type == "Encounter":
            cur.execute("""
                CREATE TABLE IF NOT EXISTS visit_occurrence (
                    visit_id TEXT PRIMARY KEY,
                    person_ref TEXT,
                    start_date TEXT,
                    end_date TEXT,
                    type_code TEXT
                )
            """)
            rows = [map_encounter_to_visit_occurrence(r) for r in resources]
            cur.executemany("INSERT OR REPLACE INTO visit_occurrence VALUES (?, ?, ?, ?, ?)", rows)
            st.success(f"Inserted {len(rows)} Encounter resources into OMOP visit_occurrence table.")
        conn.commit()
        conn.close()

st.markdown("---")


uploaded_file = st.file_uploader("Upload FHIR JSON", type="json")

if uploaded_file:
    fhir_data = json.load(uploaded_file)
    from utils.fhir_utils import validate_fhir_resource, fhir_condition_to_omop_row, fhir_patient_to_omop_row, fhir_observation_to_omop_row
    is_valid, errors = validate_fhir_resource(fhir_data)
    st.subheader("FHIR Schema Validation Result")
    if is_valid:
        st.success("FHIR resource is valid!")
    else:
        st.error("FHIR resource is INVALID.")
        st.write(errors)

    resource_type = fhir_data.get("resourceType")
    omop_row = None
    table_name = None
    create_sql = None
    insert_sql = None
    if resource_type == "Condition":
        omop_row = fhir_condition_to_omop_row(fhir_data)
        table_name = "condition_occurrence"
        create_sql = """
            CREATE TABLE IF NOT EXISTS condition_occurrence (
                condition_occurrence_id TEXT PRIMARY KEY,
                person_id TEXT,
                condition_concept_id TEXT,
                condition_start_date TEXT,
                condition_type_concept_id INTEGER,
                condition_source_value TEXT
            )
        """
        insert_sql = """
            INSERT OR REPLACE INTO condition_occurrence (
                condition_occurrence_id, person_id, condition_concept_id, condition_start_date, condition_type_concept_id, condition_source_value
            ) VALUES (?, ?, ?, ?, ?, ?)
        """
    elif resource_type == "Patient":
        omop_row = fhir_patient_to_omop_row(fhir_data)
        table_name = "person"
        create_sql = """
            CREATE TABLE IF NOT EXISTS person (
                person_id TEXT PRIMARY KEY,
                gender_concept_id INTEGER,
                year_of_birth INTEGER,
                month_of_birth INTEGER,
                day_of_birth INTEGER,
                race_concept_id INTEGER,
                ethnicity_concept_id INTEGER
            )
        """
        insert_sql = """
            INSERT OR REPLACE INTO person (
                person_id, gender_concept_id, year_of_birth, month_of_birth, day_of_birth, race_concept_id, ethnicity_concept_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """
    elif resource_type == "Observation":
        omop_row = fhir_observation_to_omop_row(fhir_data)
        table_name = "observation"
        create_sql = """
            CREATE TABLE IF NOT EXISTS observation (
                observation_id TEXT PRIMARY KEY,
                person_id TEXT,
                observation_concept_id TEXT,
                observation_date TEXT,
                observation_type_concept_id INTEGER,
                value_as_number REAL,
                value_as_string TEXT,
                value_as_concept_id TEXT,
                observation_source_value TEXT
            )
        """
        insert_sql = """
            INSERT OR REPLACE INTO observation (
                observation_id, person_id, observation_concept_id, observation_date, observation_type_concept_id, value_as_number, value_as_string, value_as_concept_id, observation_source_value
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

    if omop_row:
        st.subheader(f"OMOP Row (Deterministic Mapping for {resource_type})")
        st.write(omop_row)
        st.subheader(f"Insert OMOP Row into SQLite DB (Deterministic Mapping for {resource_type})")
        if st.button(f"Insert OMOP {resource_type} Row"):
            try:
                conn = sqlite3.connect("omop_demo.db")
                cur = conn.cursor()
                # Always drop and recreate the table to ensure correct schema
                cur.execute(f"DROP TABLE IF EXISTS {table_name}")
                cur.execute(create_sql)
                cur.execute(insert_sql, omop_row)
                conn.commit()
                st.success(f"OMOP {resource_type} row inserted into omop_demo.db! (Table recreated)")
            except Exception as e:
                st.error(f"OMOP {resource_type} row insert failed: {e}")
            finally:
                conn.close()

    st.subheader("Generated OMOP SQL (LLM)")
    sql_output = fhir_to_omop_sql(fhir_data, table=table_name or "condition_occurrence")
    st.code(sql_output, language="sql")

    # Option to run SQL directly (LLM SQL)
    st.subheader("Run SQL Insert into OMOP SQLite DB (LLM SQL)")
    if st.button("Run SQL Insert"):
        try:
            conn = sqlite3.connect("omop_demo.db")
            cur = conn.cursor()
            cur.execute(sql_output)
            conn.commit()
            st.success("SQL executed and data inserted into omop_demo.db!")
        except Exception as e:
            st.error(f"SQL execution failed: {e}")
        finally:
            conn.close()

st.markdown("---")

st.subheader("Run QA on OMOP Table (from SQLite DB)")
conn = sqlite3.connect("omop_demo.db")
tables = pd.read_sql_query("SELECT name FROM sqlite_master WHERE type='table';", conn)
table_list = tables['name'].tolist()
if table_list:
    selected_table = st.selectbox("Select OMOP table", table_list)
    if st.button("Run QA Copilot on Table"):
        df = pd.read_sql_query(f"SELECT * FROM {selected_table}", conn)
        csv_path = f"{selected_table}.csv"
        df.to_csv(csv_path, index=False)
        output_path = f"qa_report_{selected_table}.html"
        orchestrator.run_qa(csv_path, output_path)
        st.success(f"QA Report generated: {output_path}")
        with open(output_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        components.html(html_content, height=800, scrolling=True)
else:
    st.info("No OMOP tables found in omop_demo.db.")

conn.close()

# --- Full MCP Pipeline Button ---
st.markdown("---")
st.header("Run Full MCP Pipeline (Demo)")
if st.button("Run Full MCP Pipeline"):
    # Example: orchestrate all steps with sample FHIR JSON and table
    fhir_json = {"resourceType": "Patient", "id": "123", "gender": "female", "birthDate": "1980-01-01"}
    qa_csv = "person.csv"
    qa_html = "qa_report_person.html"
    results = orchestrator.orchestrate(
        steps=['etl', 'llm_mapping', 'qa', 'analytics'],
        fhir_json=fhir_json,
        table="person",
        qa_csv=qa_csv,
        qa_html=qa_html
    )
    st.success("Full MCP pipeline complete!")
    st.json(results)
