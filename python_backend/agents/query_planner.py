# query_planner.py

from typing import Dict, Any
from .dataset_selection import DatasetSelectionAgent
from .schema_cleaning import SchemaCleaningAgent
from .text_to_sql import TextToSQLAgent
from .sql_debugging import SQLDebuggingAgent
from .result_formatting import ResultFormattingAgent
from database import create_connection
from abc import ABC, abstractmethod

class Planner(ABC):
    @abstractmethod
    def plan(self, user_input: str) -> dict:
        pass
class QueryPlanner(Planner):
    def plan(self, user_input: str) -> Dict[str, Any]:
        """
        Creates a plan for answering a direct query.

        Args:
            user_input: The user's query string.

        Returns:
            A dict containing:
              - "summary": formatted LLM summary,
              - "needs_chart": whether a chart should be generated,
              - or {"error": "..."} on failure.
        """
        try:
            # 1) Instantiate agents
            ds_agent  = DatasetSelectionAgent()
            sc_agent  = SchemaCleaningAgent()
            tts_agent = TextToSQLAgent()
            dbg_agent = SQLDebuggingAgent(api_key=tts_agent.api_key)
            fmt_agent = ResultFormattingAgent(api_key=tts_agent.api_key)

            # 2) Select dataset
            ds_info = ds_agent.select_dataset(user_input)

            # 3) Clean schema
            cleaned = sc_agent.clean_schema(ds_info)

            # 4) Build a schema string for the LLM
            schema_lines = []
            for tbl in cleaned["tables"]:
                cols = cleaned["fields"].get(tbl, [])
                schema_lines.append(f"{tbl}({', '.join(cols)})")
            schema_str = "Tables:\n" + "\n".join(schema_lines)

            # 5) Generate SQL from natural language + schema
            sql_query = tts_agent.generate_sql(
                user_query=user_input,
                schema_info=schema_str
            )

            # 6) Debug & execute SQL, capturing both results and the final SQL
            conn = create_connection("wicketwise.db")
            try:
                query_results, executed_sql = dbg_agent.debug_sql(
                    sql_query=sql_query,
                    connection=conn,
                    schema=schema_str
                )
            finally:
                conn.close()

            # 7) Format the results, passing along the executed SQL for context
            summary, needs_chart = fmt_agent.format_results(
                query_results=query_results,
                original_query=user_input,
                executed_sql=executed_sql
            )

            return {
                "summary": summary,
                "needs_chart": needs_chart
            }

        except Exception as e:
            return {"error": str(e)}
