# WicketWise: An AI Agent for In-depth IPL Data Insights through Structured Data and Visual Reports

**WicketWise** is an LLM-powered web application that enables users to extract deep insights from historical IPL data through natural language queries. Built with a modular agent-based architecture, the app supports structured query generation, visual summaries, and statistical reports.

---

## List of Supported Features

1. **Summary Generator**  
   Generates comprehensive statistical summaries for a player or team using structured data. Useful for quick insights and overview reports.

2. **Head-to-Head Analyzer**  
   Compares the historical performance of two players or teams when they faced each other. Useful for evaluating rivalries and matchup advantages.

3. **Query Answering**  
   Answers direct, fact-based user queries like:  
   *“How many runs did Virat Kohli score at Chinnaswamy Stadium?”*

4. **What-if Analysis**  
   Uses trends and past performance to simulate hypothetical scenarios. Example:  
   *“What would Virat Kohli’s batting average be if he played for CSK?”*

---

## Dataset Used

- IPL Dataset (2008–2016):  
  [IPL Database on Kaggle](https://www.kaggle.com/datasets/harsha547/ipldatabase)

This structured dataset includes detailed ball-by-ball and match-level statistics for IPL matches across multiple seasons.

---

## Agents and Architecture

WicketWise operates using a series of modular AI agents, each responsible for a specific task:

- **Summary Planner**: Plans steps for generating summaries based on user input.
- **H2H Planner**: Handles logic for player/team comparisons.
- **Query Planner**: Designs the workflow for answering direct queries.
- **What-If Planner**: Plans hypothetical analysis tasks.
- **Dataset Selection Agent**: Identifies relevant tables for the current query.
- **Text-to-SQL Agent**: Converts user questions into SQL queries.
- **SQL Debugging Agent**: Fixes or retries SQL queries on failure (up to 3 attempts).
- **Hypothetical Analysis Agent**: Handles simulations using past data.
- **Result Formatting Agent**: Presents output in a clean and readable format.

Few-shot learning via Retrieval-Augmented Generation (RAG) is used to enhance the performance of Dataset Selection and Text-to-SQL agents.

---

## System Flow

1. User selects a feature on the frontend.
2. Relevant planner agent is triggered.
3. Dataset Selection Agent identifies required tables.
4. Text-to-SQL Agent generates a SQL query.
5. SQL Debugging Agent ensures query correctness.
6. Final data is passed to Result Formatting Agent for display.

---

## Evaluation and Results

We tested WicketWise on 51 queries of varying complexity. The evaluation used ground truth data derived from manually verified SQL outputs.

### Evaluation Summary

| Result Type       | Count |
|-------------------|-------|
| Fully Correct     | 22    |
| Partially Correct | 12    |
| Incorrect         | 17    |

### Observations

- **Summary Generator**: Very effective, especially for batsmen summaries. 6/8 summaries were fully accurate.
- **Query Answering**: Moderate performance — only 9 out of 26 were correct. Coverage gaps in RAG examples may have contributed.
- **Head-to-Head Analyzer**: Reliable performance with accurate data retrieval for most inputs.
- **What-if Analysis**: Limited success due to API and embedding limitations in the free tier.

---

## Installation & Running the App

### Prerequisites

- Node.js v18 or higher
- npm
- langchain, GoogleGenerativeAi python framework
- For installing libraries use:
  ```bash
  pip install langchain langchain_google_genai typing fastapi pydantic sqlite3
- To just run the backend use:
  ```bash
  uvicorn main:app --reload
- To run the complete app use:
  ```bash
  npm run dev
  
### Steps

1. Clone the repository

```bash
git clone https://github.com/ishaan-technogeek/wicketwise.git
cd wicketwise

