import sqlite3
import re
from typing import List, Any, Tuple
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
import os

class SQLDebuggingAgent:
    def __init__(self, api_key: str =None, retries: int = 3):
        self.api_key = "AIzaSyCGZvV_wKpFeW2KFFnvSTi4-5HuZVeea50"
        if not self.api_key:
            raise ValueError("API key must be provided to SQLDebuggingAgent")
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.api_key
        )

        
        self.debug_prompt = PromptTemplate(
            input_variables=["sql_query", "error_message", "schema"],
            template=(
                "You are an expert SQL assistant. A user submitted the following SQL query, "
                "which failed with the provided error message.\n\n"
                "SQL Query:\n{sql_query}\n\n"
                "Error Message:\n{error_message}\n\n"
                "Database Schema:\n{schema}\n\n"
                "Please do the following:\n"
                "1. Analyze the error message and the SQL query in the context of the given schema.\n"
                "2. Identify and explain the likely cause of the error.\n"
                "3. Suggest a corrected SQL query that resolves the issue.\n"
                "   - If you notice possible mistakes in table or column or players names (especially those related to popular cricket players or teams), "
                "     use your best judgment to correct them based on the schema.\n"
                "4. If you are unable to fix the query, simply respond with 'ERROR'.\n\n"
                
            )
        )


        self.debug_chain = LLMChain(
            llm=self.llm,
            prompt=self.debug_prompt
        )
        self.retries = retries

    def _strip_markdown(self, text: str) -> str:
        # Remove fenced code blocks ```sql ... ```
        text = re.sub(r"```(?:sql)?", "", text).strip()
        # Remove any remaining backticks
        return text.strip("` \n")

    # def debug_sql(
    #     self,
    #     sql_query: str,
    #     connection: sqlite3.Connection,
    #     schema: str
    # ) -> List[Any]:
    #     """
    #     Attempts to execute a SQL query and uses the LLM to debug it on failure.

    #     :param sql_query: Initial SQL string from TextToSQLAgent.
    #     :param connection: sqlite3.Connection to the target DB.
    #     :param schema: The textual schema context passed to the LLM.
    #     :returns: List of rows on successful execution.
    #     :raises: Exception if debugging fails after retries or LLM returns [ERROR].
    #     """
    #     last_error = None

    #     for attempt in range(1, self.retries + 1):
    #         try:
    #             cursor = connection.cursor()
    #             cursor.execute(sql_query)
    #             print(f"SQL executed successfully: {sql_query}")
    #             # Fetch all results
    #             print(cursor.fetchall())
    #             return cursor.fetchall()
    #         except sqlite3.Error as e:
    #             last_error = str(e)
    #             # If this was our last attempt, break out
    #             if attempt == self.retries:
    #                 break
    #             print(f"Attempt {attempt} failed: {last_error}")
    #             # Otherwise, ask the LLM for a corrected query
    #             llm_reply = self.debug_chain.run(
    #                 sql_query=sql_query,
    #                 error_message=last_error,
    #                 schema=schema
    #             )
    #             corrected = self._strip_markdown(llm_reply)

    #             if corrected.strip().upper() == "ERROR":
    #                 # LLM says it cannot fix it
    #                 break

    #             # Use the corrected SQL for the next attempt
    #             sql_query = corrected

    #     # If we get here, all attempts failed
    #     raise Exception(
    #         f"SQLDebuggingAgent: Query failed after {self.retries} attempts.\n"
    #         f"Last error was: {last_error}\n"
    #         f"Last SQL tried:\n{sql_query}"
    #     )
    
    def debug_sql(
        self,
        sql_query: str,
        connection: sqlite3.Connection,
        schema: str
    ) -> Tuple[List[Any], str]:
        """
        Returns:
          - results: the fetched rows
          - final_sql: the SQL string that actually executed (possibly corrected)
        """
        last_error = None

        for attempt in range(1, self.retries + 1):
            try:
                cursor = connection.cursor()
                cursor.execute(sql_query)
                results = cursor.fetchall()

                # treat zero‐hits as an error if you like...
                if not results:
                    raise sqlite3.Error("No rows returned")

                return results, sql_query

            except sqlite3.Error as e:
                last_error = str(e)
                if attempt == self.retries:
                    break

                # ask LLM to fix it
                llm_reply = self.debug_chain.run(
                    sql_query=sql_query,
                    error_message=last_error,
                    schema=schema
                )
                corrected = self._strip_markdown(llm_reply)
                if corrected.strip().upper() == "ERROR":
                    break
                sql_query = corrected

        raise Exception(
            f"SQL failed after {self.retries} attempts.\n"
            f"Last error: {last_error}\n"
            f"Last SQL tried:\n{sql_query}"
        )


