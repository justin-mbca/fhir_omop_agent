"""
MCP Orchestrator: Coordinates the modular FHIR → OMOP + QA pipeline steps.
Option 2: In-process, extensible Python orchestrator class.
"""



import os
from core.etl import etl_load
from core.etl import analytics_visualization
from core.fhir_to_omop import fhir_to_omop_sql
from core.qa_copilot import run_quality_checks
from utils import config_utils
from utils import db_utils


class MCPOrchestrator:
    def __init__(self, config_path='config.yaml'):
        self.config = config_utils.load_config(config_path)
        # For DB, use SQLAlchemy engine for compatibility
        db_type = self.config['database']['backend']
        if db_type == 'sqlite':
            db_path = self.config['database']['sqlite_path']
            self.db_engine = db_utils.get_db_engine(db_type=db_type, db_path=db_path)
        else:
            pg_settings = self.config['database']['postgresql']
            self.db_engine = db_utils.get_db_engine(db_type=db_type, pg_settings=pg_settings)

    def run_etl(self):
        """Run ETL pipeline: FHIR/Oncology → OMOP."""
        etl_load.run_etl(config_path="config.yaml")

    def run_analytics(self):
        """Run analytics and visualization on OMOP data."""
        analytics_visualization.run_analytics(config_path="config.yaml")

    def run_llm_mapping(self, fhir_json, table):
        """Run LLM mapping: FHIR JSON to OMOP SQL using Llama 2 via Ollama."""
        return fhir_to_omop_sql(fhir_json, table)

    def run_qa(self, csv_path, output_html):
        """Run QA profiling on OMOP table using ydata-profiling."""
        return run_quality_checks(csv_path, output_html)

    def orchestrate(self, steps=None, fhir_json=None, table=None, qa_csv=None, qa_html=None):
        """Run a sequence of pipeline steps. Steps: [etl, llm_mapping, qa, analytics]"""
        steps = steps or ['etl', 'llm_mapping', 'qa', 'analytics']
        results = {}
        # Get data and docs paths from config
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), self.config['data']['base_dir'])
        docs_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), self.config['docs']['output_dir'])
        # Default QA file paths if not provided
        if qa_csv is None:
            qa_csv = os.path.join(data_dir, self.config['data']['person_sample'])
        if qa_html is None:
            qa_html = os.path.join(docs_dir, 'person_profile_report.html')
        for step in steps:
            if step == 'etl':
                self.run_etl()
                results['etl'] = 'complete'
            elif step == 'llm_mapping' and fhir_json and table:
                results['llm_mapping'] = self.run_llm_mapping(fhir_json, table)
            elif step == 'qa' and qa_csv and qa_html:
                results['qa'] = self.run_qa(qa_csv, qa_html)
            elif step == 'analytics':
                self.run_analytics()
                results['analytics'] = 'complete'
        return results

# Example usage (script mode):
if __name__ == '__main__':
    orchestrator = MCPOrchestrator()
    orchestrator.orchestrate()
