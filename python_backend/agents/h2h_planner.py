# h2h_planner.py

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
class H2HPlanner(Planner):
    def plan(self, user_input: str) -> Dict[str, Any]:
        """
        Plans a Head-to-Head analysis based on user input.

        Returns a dict with:
          - "summary": the formatted summary string,
          - "needs_chart": bool,
          - or {"error": "..."} on failure.
        """
        # 1) Parse teams
        teams = user_input.lower().split(" vs ")
        if len(teams) != 2:
            return {"error": "Query must be in format 'TeamA vs TeamB'"}
        team1, team2 = teams

        conn = None
        try:
            conn = create_connection("wicketwise.db")

            # 2) Instantiate agents
            ds_agent  = DatasetSelectionAgent()
            sc_agent  = SchemaCleaningAgent()
            sql_agent = TextToSQLAgent()
            dbg_agent = SQLDebuggingAgent(api_key=sql_agent.api_key)
            fmt_agent = ResultFormattingAgent(api_key=sql_agent.api_key)

            combined_results: Dict[str, Any] = {}
            executed_sqls: Dict[str, str]   = {}

            # 3) For each ordering (team1 vs team2, then team2 vs team1)
            for a, b in ((team1, team2), (team2, team1)):
                # 3a) Select dataset
                ds = ds_agent.select_dataset(f"Given the following input: {a} vs {b}, first determine whether {a} and {b} are teams or individual players."
                f" Then provide the tables for player mentioned {a} and {b} for the role of batsman, bowler, allrounder, wicketkeeper,etc"
                "and for teams, head to head analysis.", conn)

                # 3b) Clean schema
                cleaned = sc_agent.clean_schema(ds)

                # 3c) Build schema_str for the LLM
                schema_lines = []
                for tbl in cleaned["tables"]:
                    cols = cleaned["fields"].get(tbl, [])
                    schema_lines.append(f"{tbl}({', '.join(cols)})")
                schema_str = "Tables:\n" + "\n".join(schema_lines)

                # 3d) Generate SQL
                sql_q = sql_agent.generate_sql(
                    user_query=f"Given the following input: {a} vs {b}, first determine whether {a} and {b} are teams or individual players."
                f" I want complete statistical analysis of {a} and {b} for the role of batsman, bowler, allrounder, wicketkeeper,etc"
                "and for teams, head to head analysis.",
                    schema_info=schema_str
                )

                # 3e) Debug + execute SQL
                results, executed_sql = dbg_agent.debug_sql(
                    sql_query=sql_q,
                    connection=conn,
                    schema=schema_str
                )

                # 3f) Accumulate
                key = f"{a}_vs_{b}"
                combined_results[key] = results
                executed_sqls[key]     = executed_sql

            # 4) Combine all executed_sqls into one string for the formatter
            executed_sql_str = "\n\n".join(
                f"{k}:\n{v}" for k, v in executed_sqls.items()
            )

            # 5) Format final summary
            summary, needs_chart = fmt_agent.format_results(
                query_results=combined_results,
                original_query=user_input,
                executed_sql=executed_sql_str
            )

            return {
                "summary": summary,
                "needs_chart": needs_chart
            }

        except Exception as e:
            return {"error": str(e)}

        finally:
            if conn:
                conn.close()

# from .planner import Planner
# from typing import Dict, Any

# from .dataset_selection import DatasetSelectionAgent
# from .schema_cleaning import SchemaCleaningAgent
# from .text_to_sql import TextToSQLAgent
# from .sql_debugging import SQLDebuggingAgent
# from .result_formatting import ResultFormattingAgent
# from database import create_connection # Assuming database.py is in the parent directory

# class H2HPlanner(Planner):
#     def plan(self, user_input: str) -> Dict[str, Any]:
#         """
#         Plans the steps for a Head-to-Head analysis based on user input.

#         Args:
#             user_input: The user's query (e.g., "Team A vs Team B").

#         Returns:
#             A dictionary with keys:
#               - "summary": natural-language summary,
#               - "needs_chart": bool,
#               - or "error" if something went wrong.
#         """
#         teams = user_input.lower().split(" vs ")
#         if len(teams) != 2:
#             return {"error": "Query must be in format 'TeamA vs TeamB'"}

#         team1, team2 = teams

#         conn = None
#         try:
#             conn = create_connection('wicketwise.db')

#             # instantiate agents (pass API keys if your constructors require them)
#             ds_agent    = DatasetSelectionAgent()
#             sc_agent    = SchemaCleaningAgent()
#             sql_agent   = TextToSQLAgent()
#             dbg_agent   = SQLDebuggingAgent(api_key=sql_agent.api_key)
#             fmt_agent   = ResultFormattingAgent(api_key=sql_agent.api_key)

#             combined_results = {}

#             for a, b in ((team1, team2), (team2, team1)):
#                 # 1. select dataset
#                 ds      = ds_agent.select_dataset(f"{a} vs {b} analysis", conn)
#                 # 2. clean schema
#                 schema  = sc_agent.clean_schema(ds)
#                 # 3. generate SQL (user_query first, then schema)
#                 sql_q   = sql_agent.generate_sql(
#                     user_query=f"Analyze {a} vs {b}",
#                     schema_info=schema
#                 )
#                 # 4. debug & execute SQL (pass sql, connection, schema)
#                 results = dbg_agent.debug_sql(
#                     sql_query=sql_q,
#                     connection=conn,
#                     schema=schema
#                 )
#                 combined_results[f"{a}_vs_{b}"] = results

#             # 5. format the combined results
#             summary, needs_chart = fmt_agent.format_results(
#                 query_results=combined_results,
#                 original_query=user_input
#             )

#             return {
#                 "summary": summary,
#                 "needs_chart": needs_chart
#             }

#         except Exception as e:
#             return {"error": str(e)}
#         finally:
#             if conn:
#                 conn.close()