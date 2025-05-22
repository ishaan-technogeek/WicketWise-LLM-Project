from langchain.prompts import ChatPromptTemplate
from langchain.vectorstores import Chroma
from langchain.schema import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.chains import LLMChain
from langchain_google_genai import ChatGoogleGenerativeAI
from typing import Union, Dict, Any, List
import sqlite3
import json
from langchain.prompts import ChatPromptTemplate
from langchain.vectorstores import Chroma
from langchain.schema import Document


# from Model_train_RAG import example_query_table_extracter


def create_prompt_with_examples_tableSelection(query, table_list, retriever):
    similar_docs = retriever.get_relevant_documents(query)
    examples_text = "\n\n".join([doc.page_content for doc in similar_docs])

    full_prompt = [
    ("system",
     """
You are an expert SQL specialist.
Your goal is to identify the **relevant database tables** required to answer a user's natural language query.

Below are examples of previous queries along with the correct SQL generated:

{examples_text}

Available tables:
{table_list}

User Query:
{query}

Please follow these instructions carefully:
- Respond with ONLY a JSON array listing the relevant table names (e.g., ["players", "matches"]).
- Do NOT include any SQL code or explanations.
- Include ONLY the tables necessary to answer the query.
"""),
    ("user", "Which tables should be used for this query?")
]

    print(f"Prompt: {full_prompt}")
    return full_prompt


def RAG_select_database(query, table_list, example_query_table_extracter):
    # Prepare example documents
    docs = [
        Document(page_content=f"Q: {ex['query']}\nA: {ex['sql']}")
        for ex in example_query_table_extracter
    ]

    # Initialize vector store
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/text-embedding-004",
        google_api_key="AIzaSyCGZvV_wKpFeW2KFFnvSTi4-5HuZVeea50"
    )
    vector_store = Chroma.from_documents(documents=docs, embedding=embeddings)

    retriever = vector_store.as_retriever(search_type="similarity", k=10)

    # Build the dynamic prompt
    dynamic_prompt = create_prompt_with_examples_tableSelection(query, table_list, retriever)

    # Return LangChain-style prompt
    return ChatPromptTemplate.from_messages(dynamic_prompt)

example_query_table_extracter =[
  {"query": "Generate a summary for Virat Kohli as a batsmen", "tables": ["Ball_by_Ball", "Batsman_Scored", "Wicket_Taken", "Player_Match", "Player"]},
  {"query": "Summarise Rohit Sharma's career", "tables": ["Ball_by_Ball", "Batsman_Scored", "Wicket_Taken", "Player_Match", "Player"]},
  {"query": "Give a highlight of Sachin Tendulkars career", "tables": ["Ball_by_Ball", "Batsman_Scored", "Wicket_Taken", "Player_Match", "Player"]},
  {"query": "Tell me about Gautam Gambhir", "tables": ["Ball_by_Ball", "Batsman_Scored", "Wicket_Taken", "Player_Match", "Player"]},
  {"query": "tell me about Sourav Ganguly", "tables": ["Ball_by_Ball", "Batsman_Scored", "Wicket_Taken", "Player_Match", "Player"]},
  {"query": "What has Dinesh Karthik done in his career", "tables": ["Ball_by_Ball", "Batsman_Scored", "Wicket_Taken", "Player_Match", "Player"]},
  {"query": "Tell me about Dinesh Karthik", "tables": ["Ball_by_Ball", "Batsman_Scored", "Wicket_Taken", "Player_Match", "Player"]},
  {"query": "Summarize bowling stats for Zaheer Khan", "tables": ["Ball_by_Ball", "Wicket_Taken", "Batsman_Scored", "Player_Match", "Player"]},
  {"query": "tell me about the bowling stats of Ashish Nehra", "tables": ["Ball_by_Ball", "Wicket_Taken", "Batsman_Scored", "Player_Match", "Player"]},
  {"query": "what type of bowler was Brett Lee", "tables": ["Ball_by_Ball", "Wicket_Taken", "Batsman_Scored", "Player_Match", "Player"]},
  {"query": "Summarize bowling stats for Morne Morkel", "tables": ["Ball_by_Ball", "Wicket_Taken", "Batsman_Scored", "Player_Match", "Player"]},
  {"query": "What type of bowler was Piyush Chawla", "tables": ["Ball_by_Ball", "Wicket_Taken", "Batsman_Scored", "Player_Match", "Player"]},
  {"query": "Tell me about bowler Munaf Patel", "tables": ["Ball_by_Ball", "Wicket_Taken", "Batsman_Scored", "Player_Match", "Player"]},
  {"query": "tell me about Lasith Malinga the bowler", "tables": ["Ball_by_Ball", "Wicket_Taken", "Batsman_Scored", "Player_Match", "Player"]},
  {"query": "Bowlers who have bowled most deliveries", "tables": ["Ball_by_Ball", "Player", "Country", "Bowling_Style"]},
  {"query": "No of 5-wicket hauls by bowlers in an IPL", "tables": ["Wicket_Taken", "Ball_by_Ball", "Player", "Country", "Bowling_Style"]},
  {"query": "Highest run score by a batsman in an IPL match", "tables": ["Ball_by_Ball", "Batsman_Scored", "Player", "Country", "Batting_Style"]},
  {"query": "Number of fifties and centruies by a batsman in an IPL", "tables": ["Ball_by_Ball", "Batsman_Scored", "Player", "Country", "Batting_Style"]},
  {"query": "Best Teams in IPL", "tables": ["Match", "Team", "Season"]},
  {"query": "IPL Season's Best PLayers", "tables": ["Season", "Player"]},
  {"query": "IPL Season's Winners,Runners Up, Win Type", "tables": ["Match", "Season", "Team"]},
  {"query": "Given the following input: Chennai Super Kings  vs Mumbai Indians, first determine whether Chennai Super Kings and Mumbai Indians are teams or individual players. I want complete statistical analysis of Chennai Super Kings and Mumbai Indians for the role of team vs team if both are teams, head to head analysis.", "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Match", "Team"]},
  {"query": "Given the following input: Royal Challengers Banglore  vs Kolkata Knight Riders , first determine whether Royal Challengers Banglore  and Kolkata Knight Riders are teams or individual players. I want complete statistical analysis of Royal Challengers Banglore  and Kolkata Knight Riders  for the role of team vs team if both are teams, head to head analysis.", "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Match", "Team"]},
  {"query": "Given the following input: Kings XI Punjab  vs Rajasthan Royals, first determine whether Kings XI Punjab and Rajasthan Royals are teams or individual players. I want complete statistical analysis of Kings XI Punjab and Rajasthan Royals  for the role of team vs team if both are teams, head to head analysis.", "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Match", "Team"]},
  {"query": "Given the following input: Delhi Daredevils  vs Sunrisers Hyderabad, first determine whether Delhi Daredevils and Sunrisers Hyderabad are teams or individual players. I want complete statistical analysis of Delhi Daredevils and Sunrisers Hyderabad for the role of team vs team if both are teams, head to head analysis.", "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Match", "Team"]},
  {"query": "Given the following input: Gujarat Lions  vs Rising Pune Supergiants, first determine whether Gujarat Lions and Rising Pune Supergiants are teams or individual players. I want complete statistical analysis of Gujarat Lions and Rising Pune Supergiants for the role of team vs team if both are teams, head to head analysis.", "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Match", "Team"]},
  {"query": "Given the following input: Sourav Ganguly vs Brett Lee, first determine whether Sourav Ganguly are Brett Lee teams or individual players. I want complete statistical analysis of Sourav Ganguly and Brett Lee for the role of batsman vs bowler if both are players", "tables": ["Ball_by_Ball", "Player", "Batsman_Scored", "Wicket_Taken"]},
  {"query": "Given the following input: Rahul Dravid vs Mark Boucher, first determine whether Rahul Dravid are Mark Boucher teams or individual players. I want complete statistical analysis of Rahul Dravid and Mark Boucher for the role of batsman vs bowler if both are players", "tables": ["Ball_by_Ball", "Player", "Batsman_Scored", "Wicket_Taken"]},
  {"query": "Given the following input: Sachin Tendulkar vs Sunil Narine, first determine whether Sachin Tendulkar are Sunil Narine teams or individual players. I want complete statistical analysis of Sachin Tendulkar and Sunil Narine for the role of batsman vs bowler if both are players", "tables": ["Ball_by_Ball", "Player", "Batsman_Scored", "Wicket_Taken"]},
  {"query": "Given the following input: Virat Kohli vs Jasprit Bumrah, first determine whether Virat Kohli are Jasprit Bumrah teams or individual players. I want complete statistical analysis of Virat Kohli and Jasprit Bumrah for the role of batsman vs bowler if both are players", "tables": ["Ball_by_Ball", "Player", "Batsman_Scored", "Wicket_Taken"]},
  {"query": "Given the following input: Rohit Sharma vs Morne Morkel, first determine whether Rohit Sharma are Morne Morkel teams or individual players. I want complete statistical analysis of Rohit Sharma and Morne Morkel for the role of batsman vs bowler if both are players", "tables": ["Ball_by_Ball", "Player", "Batsman_Scored", "Wicket_Taken"]},
  {"query": "Given the following input:Jacques Kallis vs Ravichandran Ashwin, first determine whether Jacques Kallis are Ravichandran Ashwin teams or individual players. I want complete statistical analysis ofJacques Kallis and Ravichandran Ashwin for the role of batsman vs bowler if both are players", "tables": ["Ball_by_Ball", "Player", "Batsman_Scored", "Wicket_Taken"]}
]


class DatasetSelectionAgent:
    def __init__(self, api_key: str = None):
        self.api_key =  "AIzaSyCGZvV_wKpFeW2KFFnvSTi4-5HuZVeea50"
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set for DatasetSelectionAgent")

        self.examples = example_query_table_extracter
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004", 
            google_api_key=self.api_key
        )
        self.vector_store = self._build_vector_store()

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.api_key
        )

    def _build_vector_store(self):
        docs = [Document(page_content=f"Q: {ex['query']}\nA: {ex['tables']}") for ex in self.examples]
        return Chroma.from_documents(documents=docs, embedding=self.embeddings)

    def _list_all_tables(self, conn: sqlite3.Connection) -> List[str]:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
        )
        return [row[0] for row in cur.fetchall()]

    def _build_prompt(self, query: str, table_list: List[str]):
        retriever = self.vector_store.as_retriever(search_type="similarity", k=3)
        similar_docs = retriever.get_relevant_documents(query)
        examples_text = "\n\n".join([doc.page_content for doc in similar_docs])
        table_str = ", ".join(table_list)

        return ChatPromptTemplate.from_messages([
            ("system", f"""You are a highly skilled SQL expert. 
Your task is to select the **relevant tables** needed to answer a user's natural language request.

Examples:
{examples_text}

Available tables:
{table_str}

User Request:
{query}

Instructions:
-Retrieve all the tables related to role of the player and the statistics mentioned by user in the prompt (if present), user comparison type queries from vector space for retrieval.
- Return ONLY a JSON array of relevant table names (e.g., ["players", "matches"]).
- Do NOT include SQL or any explanation.
- Only include tables that are needed to answer the query.
"""),
            ("user", f"Which tables should be used for this query?")
        ])

    def select_dataset(
        self,
        query_or_plan: Union[str, Dict[str, Any]],
        connection: sqlite3.Connection = None
    ) -> Dict[str, Any]:
        from database import get_table_schema, create_connection  # Adjust if needed

        own_conn = False
        if connection is None:
            connection = create_connection("wicketwise.db")
            own_conn = True

        try:
            user_query = (
                query_or_plan if isinstance(query_or_plan, str)
                else json.dumps(query_or_plan)
            )
            print(f"User query: {user_query}")
            all_tables = self._list_all_tables(connection)
            print(f"Available tables: {all_tables}")

            # Dynamic prompt creation
            dynamic_prompt = self._build_prompt(user_query, all_tables)
            chain = LLMChain(llm=self.llm, prompt=dynamic_prompt)

            # Run LLM
            table_str = ", ".join(all_tables)
            resp = chain.run(
                query=user_query,
                tables=table_str
            ).strip()
            print(f"LLM response: {resp}")

            # Strip markdown
            if resp.startswith("```json"):
                resp = resp.removeprefix("```json").strip()
            if resp.endswith("```"):
                resp = resp.removesuffix("```").strip()

            try:
                selected = json.loads(resp)
                if not isinstance(selected, list):
                    raise ValueError("LLM did not return a JSON array")
            except Exception as e:
                raise ValueError(f"Failed to parse LLM response as JSON list: {e}\nResponse was: {resp}")

            relevant_fields: Dict[str, List[str]] = {}
            for tbl in selected:
                try:
                    cols = get_table_schema(tbl, connection)
                except Exception:
                    cols = []
                relevant_fields[tbl] = cols

            print(f"Selected tables: {selected}")
            print(f"Relevant fields: {relevant_fields}")
            return {
                "selected_tables": selected,
                "relevant_fields": relevant_fields
            }

        finally:
            if own_conn:
                connection.close()
