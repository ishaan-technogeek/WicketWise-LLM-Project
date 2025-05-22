from abc import ABC, abstractmethod

class Planner(ABC):
    @abstractmethod
    def plan(self, user_input: str) -> dict:
        pass
from langchain.chains import LLMChain
from .dataset_selection import DatasetSelectionAgent
from .schema_cleaning import SchemaCleaningAgent
from .text_to_sql import TextToSQLAgent
from .sql_debugging import SQLDebuggingAgent
from .result_formatting import ResultFormattingAgent
import os
from database import create_connection # Import create_connection from database.py
from langchain_google_genai import ChatGoogleGenerativeAI
import re
from typing import Dict, Any
from langchain.prompts import PromptTemplate  # Import PromptTemplate

class SummaryPlanner(Planner):
    def __init__(self, api_key: str = "AIzaSyCGZvV_wKpFeW2KFFnvSTi4-5HuZVeea50"):
        # Use same API key for both extraction and SQL agents
        self.api_key = "AIzaSyCGZvV_wKpFeW2KFFnvSTi4-5HuZVeea50"
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set for SummaryPlanner")

        # LLMChain for name extraction
        extract_prompt = PromptTemplate(
            template="""
Given this user request:

  "{user_query}"

Extract the single player name or team name whose career summary is being requested.
Return **only** the name, with no extra words.
If you cannot find one, return an empty string.
""",
            input_variables=["user_query"]
        )
        self.extract_chain = LLMChain(
            llm=ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=self.api_key
            ),
            prompt=extract_prompt
        )

        # Other agents
        self.ds_agent  = DatasetSelectionAgent()
        self.sc_agent  = SchemaCleaningAgent()
        self.tts_agent = TextToSQLAgent()
        self.dbg_agent = SQLDebuggingAgent(api_key=self.api_key)
        self.fmt_agent = ResultFormattingAgent(api_key=self.api_key)

    def plan(self, user_query: str) -> Dict[str, Any]:
        # 1) Extract the player/team name via LLM
        raw_name = self.extract_chain.run(user_query=user_query).strip()
        player_name = raw_name or None

        if not player_name:
            return {"error": "Could not identify a player or team name in the query."}

        # 2) Build schema, generate SQL, debug & execute, format — as before
        conn = create_connection("wicketwise.db")
        try:
            ds_info = self.ds_agent.select_dataset(user_query, connection=conn)
            cleaned = self.sc_agent.clean_schema(ds_info)

            # Build schema_str
            schema_lines = [
                f"{tbl}({', '.join(cleaned['fields'].get(tbl, []))})"
                for tbl in cleaned["tables"]
            ]
            schema_str = "Tables:\n" + "\n".join(schema_lines)

            print("Schema String: Successfully built schema string.")

            # Generate and run SQL
            sql_query = self.tts_agent.generate_sql(
                user_query=f"get career statistics for {player_name}",
                schema_info=schema_str
            )
            results, executed_sql = self.dbg_agent.debug_sql(
                sql_query=sql_query,
                connection=conn,
                schema=schema_str
            )

            # Format final summary
            summary, needs_chart = self.fmt_agent.format_results(
                query_results=results,
                original_query=user_query,
                executed_sql=executed_sql
            )

            return {
                "summary": summary,
                "needs_chart": needs_chart
            }
        finally:
            conn.close()