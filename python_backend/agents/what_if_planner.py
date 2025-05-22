from agents.planner import Planner
from typing import Dict, Any
import re
from .dataset_selection import DatasetSelectionAgent
from .schema_cleaning import SchemaCleaningAgent
from .text_to_sql import TextToSQLAgent
from .sql_debugging import SQLDebuggingAgent
from .hypothetical_analysis import HypotheticalAnalysisAgent
from .result_formatting import ResultFormattingAgent
from database import create_connection

class WhatIfPlanner(Planner):
    def plan(self, user_input: str) -> Dict[str, Any]:
        """
        Creates a plan for the What-If Analysis feature.
        Returns a dict with:
          - "summary": formatted LLM summary,
          - "needs_chart": bool,
          - or {"error": "..."} on failure.
        """
        try:
            # 1) Basic parsing (optional—you could rely entirely on the LLM)
            player_match = re.search(r"If (.*?) played", user_input, re.IGNORECASE)
            player_name = player_match.group(1).strip() if player_match else None

            # 2) Instantiate agents
            ds_agent   = DatasetSelectionAgent()
            sc_agent   = SchemaCleaningAgent()
            tts_agent  = TextToSQLAgent()
            dbg_agent  = SQLDebuggingAgent(api_key=tts_agent.api_key)
            hypo_agent = HypotheticalAnalysisAgent(api_key=tts_agent.api_key)
            fmt_agent  = ResultFormattingAgent(api_key=tts_agent.api_key)

            # 3) Select & clean schema
            conn = create_connection("wicketwise.db")
            ds_info = ds_agent.select_dataset(user_input, connection=conn)
            cleaned = sc_agent.clean_schema(ds_info)

            # 4) Build schema_str
            schema_lines = []
            for tbl in cleaned["tables"]:
                cols = cleaned["fields"].get(tbl, [])
                schema_lines.append(f"{tbl}({', '.join(cols)})")
            schema_str = "Tables:\n" + "\n".join(schema_lines)

            # 5) Generate SQL for the real-data pull
            sql_query = tts_agent.generate_sql(
                user_query=user_input,
                schema_info=schema_str
            )

            # 6) Debug & execute SQL → real_data_results + executed_sql
            real_data_results, executed_sql = dbg_agent.debug_sql(
                sql_query=sql_query,
                connection=conn,
                schema=schema_str
            )

            # 7) Hypothetical analysis
            # Pass just the results dict/list and the scenario string
            hypothetical_text = hypo_agent.analyze(
                query_results=real_data_results,
                what_if_scenario=user_input
            )

            # 8) Format everything together
            summary, needs_chart = fmt_agent.format_results(
                query_results=real_data_results,
                original_query=user_input,
                executed_sql=executed_sql,
                analysis_results=hypothetical_text
            )

            return {
                "summary": summary,
                "needs_chart": needs_chart
            }

        except Exception as e:
            return {"error": str(e)}

        finally:
            if 'conn' in locals() and conn:
                conn.close()