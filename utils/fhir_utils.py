def fhir_patient_to_omop_row(fhir_patient):
    """
    Deterministically map a FHIR Patient resource to an OMOP person row (as a tuple).
    OMOP v5.3: (person_id, gender_concept_id, year_of_birth, month_of_birth, day_of_birth, race_concept_id, ethnicity_concept_id)
    Note: Concept IDs should be mapped from vocabularies; here we use placeholders.
    """
    person_id = fhir_patient.get('id')
    gender = fhir_patient.get('gender')
    # Placeholder gender_concept_id: 8507=Male, 8532=Female, 0=Unknown
    gender_concept_id = 8507 if gender == 'male' else 8532 if gender == 'female' else 0
    birth_date = fhir_patient.get('birthDate', '')
    year_of_birth = int(birth_date[:4]) if len(birth_date) >= 4 else None
    month_of_birth = int(birth_date[5:7]) if len(birth_date) >= 7 else None
    day_of_birth = int(birth_date[8:10]) if len(birth_date) >= 10 else None
    # Placeholders for race/ethnicity
    race_concept_id = 0
    ethnicity_concept_id = 0
    return (
        person_id,
        gender_concept_id,
        year_of_birth,
        month_of_birth,
        day_of_birth,
        race_concept_id,
        ethnicity_concept_id
    )

def fhir_observation_to_omop_row(fhir_observation):
    """
    Deterministically map a FHIR Observation resource to an OMOP observation row (as a tuple).
    OMOP v5.3: (observation_id, person_id, observation_concept_id, observation_date, observation_type_concept_id, value_as_number, value_as_string, value_as_concept_id, observation_source_value)
    Note: Concept IDs should be mapped from vocabularies; here we use placeholders.
    """
    observation_id = fhir_observation.get('id')
    subject_ref = fhir_observation.get('subject', {}).get('reference', '')
    person_id = subject_ref.split('/')[-1] if subject_ref.startswith('Patient/') else None
    code_coding = fhir_observation.get('code', {}).get('coding', [])
    code = code_coding[0].get('code') if code_coding else None
    observation_concept_id = code if code else None  # Placeholder
    observation_date = fhir_observation.get('effectiveDateTime')
    observation_type_concept_id = 44814721  # Placeholder: EHR observation
    value_as_number = fhir_observation.get('valueQuantity', {}).get('value') if 'valueQuantity' in fhir_observation else None
    value_as_string = fhir_observation.get('valueString')
    value_as_concept_id = None
    observation_source_value = code
    return (
        observation_id,
        person_id,
        observation_concept_id,
        observation_date,
        observation_type_concept_id,
        value_as_number,
        value_as_string,
        value_as_concept_id,
        observation_source_value
    )
def fhir_condition_to_omop_row(fhir_condition):
    """
    Deterministically map a FHIR Condition resource to an OMOP condition_occurrence row (as a tuple).
    This assumes a minimal OMOP v5.3 schema: (condition_occurrence_id, person_id, condition_concept_id, condition_start_date, condition_type_concept_id, condition_source_value)
    Note: In real OMOP, concept IDs must be mapped from codes using a vocabulary table. Here, we use placeholders.
    """
    # Extract fields
    condition_occurrence_id = fhir_condition.get('id')
    # Extract person_id from subject reference (e.g., 'Patient/1' -> 1)
    subject_ref = fhir_condition.get('subject', {}).get('reference', '')
    person_id = subject_ref.split('/')[-1] if subject_ref.startswith('Patient/') else None
    # Extract SNOMED code (should map to OMOP concept_id in real ETL)
    code_coding = fhir_condition.get('code', {}).get('coding', [])
    snomed_code = None
    if code_coding:
        snomed_code = code_coding[0].get('code')
    # Placeholder: use SNOMED code as concept_id (should map to integer OMOP concept_id)
    condition_concept_id = snomed_code if snomed_code else None
    # Extract onset date
    condition_start_date = fhir_condition.get('onsetDateTime')
    # Use a default type concept ID (e.g., 32020 = EHR problem list entry)
    condition_type_concept_id = 32020
    # Use the code as the source value
    condition_source_value = snomed_code
    return (
        condition_occurrence_id,
        person_id,
        condition_concept_id,
        condition_start_date,
        condition_type_concept_id,
        condition_source_value
    )
# FHIR parsing and helper stubs


def extract_patient_id(resource):
    return resource.get('id')

def validate_fhir_resource(resource_dict):
    """
    Validate a FHIR resource dict using fhir.resources.
    Returns (is_valid, errors) where errors is a list of error messages (empty if valid).
    """
    try:
        resource_type = resource_dict.get('resourceType')
        if not resource_type:
            return False, ["Missing 'resourceType' in resource."]
        # Dynamically import the correct FHIR resource class
        try:
            import importlib
            module = importlib.import_module(f"fhir.resources.{resource_type.lower()}")
            resource_class = getattr(module, resource_type)
            resource_class(**resource_dict)  # Will raise if invalid
            return True, []
        except Exception as e:
            return False, [str(e)]
    except Exception as e:
        return False, [f"Validation error: {e}"]
