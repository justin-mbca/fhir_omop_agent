
import streamlit as st
import streamlit.components.v1 as components
import json
import pandas as pd
import sqlite3
import requests
from core.fhir_to_omop import fhir_to_omop_sql, client
from core.qa_copilot import run_quality_checks
from utils.db_utils import connect_omop_db
from utils.fhir_utils import extract_patient_id


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
        return (
            resource.get('id'),
            resource.get('gender'),
            resource.get('birthDate'),
            resource.get('deceasedDateTime')
        )
    except Exception:
        # Fallback: use LLM to generate SQL, parse values
        sql = fhir_to_omop_sql(resource, 'person')
        import re
        m = re.search(r"VALUES ?\((.*?)\)", sql, re.DOTALL)
        if m:
            vals = [v.strip().strip("'\"") for v in m.group(1).split(',')]
            return tuple(vals)
        return (None, None, None, None)

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
                    person_id TEXT PRIMARY KEY,
                    gender TEXT,
                    birth_date TEXT,
                    deceased_date TEXT
                )
            """)
            rows = [map_patient_to_person(r) for r in resources]
            cur.executemany("INSERT OR REPLACE INTO person VALUES (?, ?, ?, ?)", rows)
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
    st.subheader("Generated OMOP SQL")
    sql_output = fhir_to_omop_sql(fhir_data, table="condition_occurrence")
    st.code(sql_output, language="sql")

    # Option to run SQL directly
    st.subheader("Run SQL Insert into OMOP SQLite DB")
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
        run_quality_checks(csv_path, output_path)
        st.success(f"QA Report generated: {output_path}")
        with open(output_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        components.html(html_content, height=800, scrolling=True)
else:
    st.info("No OMOP tables found in omop_demo.db.")
conn.close()
