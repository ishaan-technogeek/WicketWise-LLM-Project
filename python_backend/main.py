from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from agents.summary_planner import SummaryPlanner
from agents.h2h_planner import H2HPlanner
from agents.query_planner import QueryPlanner
from agents.what_if_planner import WhatIfPlanner
from agents.dataset_selection import DatasetSelectionAgent
from agents.schema_cleaning import SchemaCleaningAgent
from agents.text_to_sql import TextToSQLAgent
from agents.sql_debugging import SQLDebuggingAgent
from agents.hypothetical_analysis import HypotheticalAnalysisAgent
from agents.result_formatting import ResultFormattingAgent

from dotenv import load_dotenv
import os

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
class UserInput(BaseModel):
    query: str

app = FastAPI(debug = True)

# Instantiate Planner Agents
summary_planner = SummaryPlanner()
h2h_planner = H2HPlanner()
query_planner = QueryPlanner()
what_if_planner = WhatIfPlanner()

# Instantiate other agents (placeholders for now)
dataset_selection_agent = DatasetSelectionAgent()
schema_cleaning_agent = SchemaCleaningAgent()
text_to_sql_agent = TextToSQLAgent()
sql_debugging_agent = SQLDebuggingAgent()
hypothetical_analysis_agent = HypotheticalAnalysisAgent()
result_formatting_agent = ResultFormattingAgent()

@app.get("/")
def read_root():
    return {"message": "Backend is running"}

@app.post("/summary")   
async def generate_summary(user_input: UserInput):
    try:
        result = summary_planner.plan(user_input.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/h2h")
async def analyze_h2h(user_input: UserInput):
    try:
        result = h2h_planner.plan(user_input.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query")
async def answer_query(user_input: UserInput):
    try:
        result = query_planner.plan(user_input.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/what-if")
async def analyze_what_if(user_input: UserInput):
    try:
        result = what_if_planner.plan(user_input.query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))