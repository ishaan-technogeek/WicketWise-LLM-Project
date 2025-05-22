# result_formatting.py

import os
import logging
from typing import Any, List, Tuple, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

logger = logging.getLogger(__name__)

class ResultFormattingAgent:
    def __init__(self, api_key: Optional[str] = None):
        # Load API key
        self.api_key = "AIzaSyCGZvV_wKpFeW2KFFnvSTi4-5HuZVeea50"
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set for ResultFormattingAgent")

        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.api_key
        )

        # Build a reusable prompt + chain that now includes executed_sql
        prompt_template = PromptTemplate(
            template="""
You are a helpful assistant that summarizes cricket data, focusing on readability
and clarity.

User Query:
{original_query}

Executed SQL:
{executed_sql}

Raw Results:
{query_results}

{analysis_section}

Provide a concise summary that directly answers the user's question, labeling columns as needed.
""",
            input_variables=[
                "original_query",
                "executed_sql",
                "query_results",
                "analysis_section"
            ]
        )

        self.chain = LLMChain(llm=self.llm, prompt=prompt_template)

    def format_results(
        self,
        query_results: Any,
        original_query: str,
        executed_sql: str,
        analysis_results: Optional[str] = None
    ) -> Tuple[str, bool]:
        """
        Formats the query results and optional analysis into a natural-language summary.

        Returns:
            (summary_text, needs_chart)
        """
        # Build the analysis section text
        if analysis_results:
            analysis_section = f"Hypothetical Analysis:\n{analysis_results}"
        else:
            analysis_section = ""  # always supply the variable

        # Run the chain, now passing executed_sql
        summary = self.chain.run(
            original_query=original_query,
            executed_sql=executed_sql,
            query_results=query_results,
            analysis_section=analysis_section
        ).strip()

        # Decide if a chart is needed
        needs_chart = self._determine_if_chart_needed(
            original_query, query_results, analysis_results
        )
        logger.debug(f"ResultFormattingAgent: needs_chart={needs_chart}")

        return summary, needs_chart

    def _determine_if_chart_needed(
        self,
        original_query: str,
        query_results: Any,
        analysis_results: Optional[str]
    ) -> bool:
        """
        Heuristic:
        - Multiple rows → chart
        - 'vs' in query → chart
        - analysis present → chart
        """
        # Multiple data points?
        if isinstance(query_results, List) and len(query_results) > 1:
            return True

        # Head-to-head or comparison?
        if "vs" in original_query.lower() or "head to head" in original_query.lower():
            return True

        # Hypothetical analysis included?
        if analysis_results:
            return True

        return False
