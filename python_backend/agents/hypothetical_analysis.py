# hypothetical_analysis.py

import os
import re
from typing import Any, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

class HypotheticalAnalysisAgent:
    def __init__(self, api_key: Optional[str] = None):
        # Load API key
        self.api_key = "AIzaSyCGZvV_wKpFeW2KFFnvSTi4-5HuZVeea50"
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set for HypotheticalAnalysisAgent")

        # Initialize LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.api_key
        )

        # Build a prompt + chain
        prompt = PromptTemplate(
            template="""
You are a data scientist specialized in “what-if” projections for cricket statistics.

Real Data:
{real_data}

Hypothetical Scenario:
{scenario}

Based on the real data above, analyze how the hypothetical scenario would change the outcome.
Provide your reasoning step by step and then summarize the projected result.
""",
            input_variables=["real_data", "scenario"]
        )
        self.chain = LLMChain(llm=self.llm, prompt=prompt)

    def _strip_markdown(self, text: str) -> str:
        # Remove fenced code blocks and backticks
        text = re.sub(r"```(?:\w+)?", "", text)
        return text.strip("`\n ")

    def analyze(self, query_results: Any, what_if_scenario: str) -> str:
        """
        Performs hypothetical reasoning based on query results and a what-if scenario.

        Args:
            query_results: The results (list of tuples or dict) from the DB.
            what_if_scenario: A string describing the scenario.

        Returns:
            A string containing the projected outcome and reasoning.
        """
        # 1) Serialize the real data for the prompt
        # If it's a dict of lists, stringify each key
        if isinstance(query_results, dict):
            real_data = "\n".join(f"{k}: {v}" for k, v in query_results.items())
        else:
            # e.g. list of row tuples
            real_data = "\n".join(str(r) for r in query_results)

        # 2) Run the chain
        raw = self.chain.run(real_data=real_data, scenario=what_if_scenario)

        # 3) Clean up any markdown
        return self._strip_markdown(raw)
