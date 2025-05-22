# text_to_sql.py

import os
import re
import sqlite3
from typing import List, Dict, Any

from langchain_google_genai import GoogleGenerativeAIEmbeddings, ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.vectorstores import Chroma
from langchain.schema import Document
from langchain.chains import LLMChain

# Your RAG examples: each item has a NL query, the tables used, and the correct SQL.
examples_of_tables_sql = [
    {
  "query": "Generate a summary for Virat Kohli as a batsmen",
  "tables": ["Ball_by_Ball", "Batsman_Scored", "Wicket_Taken", "Player_Match", "Player"],
  "sql": """
    WITH
    InningStats AS (
        SELECT
            bbb.Striker           AS Player_Id,
            bbb.Match_Id,
            bbb.Innings_No,
            SUM(bs.Runs_Scored)   AS Runs,
            CASE 
              WHEN MAX(wt.Player_Out) IS NULL THEN 1 
              ELSE 0 
            END                    AS NotOut
        FROM Ball_by_Ball bbb
        JOIN Batsman_Scored bs
          ON  bbb.Match_Id   = bs.Match_Id
          AND bbb.Over_Id    = bs.Over_Id
          AND bbb.Ball_Id    = bs.Ball_Id
          AND bbb.Innings_No = bs.Innings_No
        LEFT JOIN Wicket_Taken wt
          ON  bbb.Match_Id   = wt.Match_Id
          AND bbb.Over_Id    = wt.Over_Id
          AND bbb.Ball_Id    = wt.Ball_Id
          AND bbb.Innings_No = wt.Innings_No
          AND wt.Player_Out  = bbb.Striker
        GROUP BY bbb.Striker, bbb.Match_Id, bbb.Innings_No
    ),
    PerBatsmanInnings AS (
        SELECT
            Player_Id,
            COUNT(*)                                    AS Innings_Played,
            MAX(Runs)                                   AS Highest_Score,
            SUM(CASE WHEN Runs >= 100 THEN 1 ELSE 0 END) AS Centuries,
            SUM(CASE WHEN Runs BETWEEN 50 AND 99 THEN 1 ELSE 0 END) AS Half_Centuries,
            SUM(NotOut)                                 AS Not_Outs
        FROM InningStats
        GROUP BY Player_Id
    ),
    PerBatsmanBalls AS (
        SELECT
            bbb.Striker           AS Player_Id,
            COUNT(DISTINCT pm.Match_Id)                 AS Matches_Played,
            SUM(bs.Runs_Scored)                         AS Runs_Scored,
            COUNT(*)                                    AS Balls_Faced,
            SUM(CASE WHEN bs.Runs_Scored = 4 THEN 1 ELSE 0 END) AS Fours,
            SUM(CASE WHEN bs.Runs_Scored = 6 THEN 1 ELSE 0 END) AS Sixes
        FROM Ball_by_Ball bbb
        JOIN Batsman_Scored bs
          ON  bbb.Match_Id   = bs.Match_Id
          AND bbb.Over_Id    = bs.Over_Id
          AND bbb.Ball_Id    = bs.Ball_Id
          AND bbb.Innings_No = bs.Innings_No
        JOIN Player_Match pm
          ON  bbb.Striker    = pm.Player_Id
          AND bbb.Match_Id   = pm.Match_Id
        GROUP BY bbb.Striker
    )
    SELECT
        p.Player_Name               AS Player,
        pb.Matches_Played,
        pi.Innings_Played            AS Innings,
        pb.Runs_Scored,
        pi.Highest_Score,
        CASE 
          WHEN (pi.Innings_Played - pi.Not_Outs) = 0 
          THEN NULL 
          ELSE ROUND(pb.Runs_Scored * 1.0 
                     / (pi.Innings_Played - pi.Not_Outs), 2) 
        END                          AS Batting_Average,
        ROUND(100.0 * pb.Runs_Scored / pb.Balls_Faced, 2) AS Strike_Rate,
        pi.Centuries,
        pi.Half_Centuries,
        pi.Not_Outs,
        pb.Balls_Faced,
        pb.Fours,
        pb.Sixes
    FROM Player p
    JOIN PerBatsmanBalls   pb ON pb.Player_Id = p.Player_Id
    JOIN PerBatsmanInnings pi ON pi.Player_Id = p.Player_Id
    WHERE p.Player_Name = 'Virat Kohli'
    ;
  """
},
{"query": "Summarise Rohit Sharma's career",
  "tables": ["Ball_by_Ball", "Batsman_Scored", "Wicket_Taken", "Player_Match", "Player"],
  "sql": """
    WITH
    InningStats AS (
        SELECT
            bbb.Striker           AS Player_Id,
            bbb.Match_Id,
            bbb.Innings_No,
            SUM(bs.Runs_Scored)   AS Runs,
            CASE 
              WHEN MAX(wt.Player_Out) IS NULL THEN 1 
              ELSE 0 
            END                    AS NotOut
        FROM Ball_by_Ball bbb
        JOIN Batsman_Scored bs
          ON  bbb.Match_Id   = bs.Match_Id
          AND bbb.Over_Id    = bs.Over_Id
          AND bbb.Ball_Id    = bs.Ball_Id
          AND bbb.Innings_No = bs.Innings_No
        LEFT JOIN Wicket_Taken wt
          ON  bbb.Match_Id   = wt.Match_Id
          AND bbb.Over_Id    = wt.Over_Id
          AND bbb.Ball_Id    = wt.Ball_Id
          AND bbb.Innings_No = wt.Innings_No
          AND wt.Player_Out  = bbb.Striker
        GROUP BY bbb.Striker, bbb.Match_Id, bbb.Innings_No
    ),
    PerBatsmanInnings AS (
        SELECT
            Player_Id,
            COUNT(*)                                    AS Innings_Played,
            MAX(Runs)                                   AS Highest_Score,
            SUM(CASE WHEN Runs >= 100 THEN 1 ELSE 0 END) AS Centuries,
            SUM(CASE WHEN Runs BETWEEN 50 AND 99 THEN 1 ELSE 0 END) AS Half_Centuries,
            SUM(NotOut)                                 AS Not_Outs
        FROM InningStats
        GROUP BY Player_Id
    ),
    PerBatsmanBalls AS (
        SELECT
            bbb.Striker           AS Player_Id,
            COUNT(DISTINCT pm.Match_Id)                 AS Matches_Played,
            SUM(bs.Runs_Scored)                         AS Runs_Scored,
            COUNT(*)                                    AS Balls_Faced,
            SUM(CASE WHEN bs.Runs_Scored = 4 THEN 1 ELSE 0 END) AS Fours,
            SUM(CASE WHEN bs.Runs_Scored = 6 THEN 1 ELSE 0 END) AS Sixes
        FROM Ball_by_Ball bbb
        JOIN Batsman_Scored bs
          ON  bbb.Match_Id   = bs.Match_Id
          AND bbb.Over_Id    = bs.Over_Id
          AND bbb.Ball_Id    = bs.Ball_Id
          AND bbb.Innings_No = bs.Innings_No
        JOIN Player_Match pm
          ON  bbb.Striker    = pm.Player_Id
          AND bbb.Match_Id   = pm.Match_Id
        GROUP BY bbb.Striker
    )
    SELECT
        p.Player_Name               AS Player,
        pb.Matches_Played,
        pi.Innings_Played            AS Innings,
        pb.Runs_Scored,
        pi.Highest_Score,
        CASE 
          WHEN (pi.Innings_Played - pi.Not_Outs) = 0 
          THEN NULL 
          ELSE ROUND(pb.Runs_Scored * 1.0 
                     / (pi.Innings_Played - pi.Not_Outs), 2) 
        END                          AS Batting_Average,
        ROUND(100.0 * pb.Runs_Scored / pb.Balls_Faced, 2) AS Strike_Rate,
        pi.Centuries,
        pi.Half_Centuries,
        pi.Not_Outs,
        pb.Balls_Faced,
        pb.Fours,
        pb.Sixes
    FROM Player p
    JOIN PerBatsmanBalls   pb ON pb.Player_Id = p.Player_Id
    JOIN PerBatsmanInnings pi ON pi.Player_Id = p.Player_Id
    WHERE p.Player_Name = 'Rohit Sharma'
    ;
  """
},
{"query": "Give a highlight of Sachin Tendulkars career",
 "tables": ["Ball_by_Ball", "Batsman_Scored", "Wicket_Taken", "Player_Match", "Player"],
  "sql": """
    WITH
    InningStats AS (
        SELECT
            bbb.Striker           AS Player_Id,
            bbb.Match_Id,
            bbb.Innings_No,
            SUM(bs.Runs_Scored)   AS Runs,
            CASE 
              WHEN MAX(wt.Player_Out) IS NULL THEN 1 
              ELSE 0 
            END                    AS NotOut
        FROM Ball_by_Ball bbb
        JOIN Batsman_Scored bs
          ON  bbb.Match_Id   = bs.Match_Id
          AND bbb.Over_Id    = bs.Over_Id
          AND bbb.Ball_Id    = bs.Ball_Id
          AND bbb.Innings_No = bs.Innings_No
        LEFT JOIN Wicket_Taken wt
          ON  bbb.Match_Id   = wt.Match_Id
          AND bbb.Over_Id    = wt.Over_Id
          AND bbb.Ball_Id    = wt.Ball_Id
          AND bbb.Innings_No = wt.Innings_No
          AND wt.Player_Out  = bbb.Striker
        GROUP BY bbb.Striker, bbb.Match_Id, bbb.Innings_No
    ),
    PerBatsmanInnings AS (
        SELECT
            Player_Id,
            COUNT(*)                                    AS Innings_Played,
            MAX(Runs)                                   AS Highest_Score,
            SUM(CASE WHEN Runs >= 100 THEN 1 ELSE 0 END) AS Centuries,
            SUM(CASE WHEN Runs BETWEEN 50 AND 99 THEN 1 ELSE 0 END) AS Half_Centuries,
            SUM(NotOut)                                 AS Not_Outs
        FROM InningStats
        GROUP BY Player_Id
    ),
    PerBatsmanBalls AS (
        SELECT
            bbb.Striker           AS Player_Id,
            COUNT(DISTINCT pm.Match_Id)                 AS Matches_Played,
            SUM(bs.Runs_Scored)                         AS Runs_Scored,
            COUNT(*)                                    AS Balls_Faced,
            SUM(CASE WHEN bs.Runs_Scored = 4 THEN 1 ELSE 0 END) AS Fours,
            SUM(CASE WHEN bs.Runs_Scored = 6 THEN 1 ELSE 0 END) AS Sixes
        FROM Ball_by_Ball bbb
        JOIN Batsman_Scored bs
          ON  bbb.Match_Id   = bs.Match_Id
          AND bbb.Over_Id    = bs.Over_Id
          AND bbb.Ball_Id    = bs.Ball_Id
          AND bbb.Innings_No = bs.Innings_No
        JOIN Player_Match pm
          ON  bbb.Striker    = pm.Player_Id
          AND bbb.Match_Id   = pm.Match_Id
        GROUP BY bbb.Striker
    )
    SELECT
        p.Player_Name               AS Player,
        pb.Matches_Played,
        pi.Innings_Played            AS Innings,
        pb.Runs_Scored,
        pi.Highest_Score,
        CASE 
          WHEN (pi.Innings_Played - pi.Not_Outs) = 0 
          THEN NULL 
          ELSE ROUND(pb.Runs_Scored * 1.0 
                     / (pi.Innings_Played - pi.Not_Outs), 2) 
        END                          AS Batting_Average,
        ROUND(100.0 * pb.Runs_Scored / pb.Balls_Faced, 2) AS Strike_Rate,
        pi.Centuries,
        pi.Half_Centuries,
        pi.Not_Outs,
        pb.Balls_Faced,
        pb.Fours,
        pb.Sixes
    FROM Player p
    JOIN PerBatsmanBalls   pb ON pb.Player_Id = p.Player_Id
    JOIN PerBatsmanInnings pi ON pi.Player_Id = p.Player_Id
    WHERE p.Player_Name = 'Sachin Tendulkar'
    ;
  """
},
{"query": "Tell me about Gautam Gambhir",
 "tables": ["Ball_by_Ball", "Batsman_Scored", "Wicket_Taken", "Player_Match", "Player"],
  "sql": """
    WITH
    InningStats AS (
        SELECT
            bbb.Striker           AS Player_Id,
            bbb.Match_Id,
            bbb.Innings_No,
            SUM(bs.Runs_Scored)   AS Runs,
            CASE 
              WHEN MAX(wt.Player_Out) IS NULL THEN 1 
              ELSE 0 
            END                    AS NotOut
        FROM Ball_by_Ball bbb
        JOIN Batsman_Scored bs
          ON  bbb.Match_Id   = bs.Match_Id
          AND bbb.Over_Id    = bs.Over_Id
          AND bbb.Ball_Id    = bs.Ball_Id
          AND bbb.Innings_No = bs.Innings_No
        LEFT JOIN Wicket_Taken wt
          ON  bbb.Match_Id   = wt.Match_Id
          AND bbb.Over_Id    = wt.Over_Id
          AND bbb.Ball_Id    = wt.Ball_Id
          AND bbb.Innings_No = wt.Innings_No
          AND wt.Player_Out  = bbb.Striker
        GROUP BY bbb.Striker, bbb.Match_Id, bbb.Innings_No
    ),
    PerBatsmanInnings AS (
        SELECT
            Player_Id,
            COUNT(*)                                    AS Innings_Played,
            MAX(Runs)                                   AS Highest_Score,
            SUM(CASE WHEN Runs >= 100 THEN 1 ELSE 0 END) AS Centuries,
            SUM(CASE WHEN Runs BETWEEN 50 AND 99 THEN 1 ELSE 0 END) AS Half_Centuries,
            SUM(NotOut)                                 AS Not_Outs
        FROM InningStats
        GROUP BY Player_Id
    ),
    PerBatsmanBalls AS (
        SELECT
            bbb.Striker           AS Player_Id,
            COUNT(DISTINCT pm.Match_Id)                 AS Matches_Played,
            SUM(bs.Runs_Scored)                         AS Runs_Scored,
            COUNT(*)                                    AS Balls_Faced,
            SUM(CASE WHEN bs.Runs_Scored = 4 THEN 1 ELSE 0 END) AS Fours,
            SUM(CASE WHEN bs.Runs_Scored = 6 THEN 1 ELSE 0 END) AS Sixes
        FROM Ball_by_Ball bbb
        JOIN Batsman_Scored bs
          ON  bbb.Match_Id   = bs.Match_Id
          AND bbb.Over_Id    = bs.Over_Id
          AND bbb.Ball_Id    = bs.Ball_Id
          AND bbb.Innings_No = bs.Innings_No
        JOIN Player_Match pm
          ON  bbb.Striker    = pm.Player_Id
          AND bbb.Match_Id   = pm.Match_Id
        GROUP BY bbb.Striker
    )
    SELECT
        p.Player_Name               AS Player,
        pb.Matches_Played,
        pi.Innings_Played            AS Innings,
        pb.Runs_Scored,
        pi.Highest_Score,
        CASE 
          WHEN (pi.Innings_Played - pi.Not_Outs) = 0 
          THEN NULL 
          ELSE ROUND(pb.Runs_Scored * 1.0 
                     / (pi.Innings_Played - pi.Not_Outs), 2) 
        END                          AS Batting_Average,
        ROUND(100.0 * pb.Runs_Scored / pb.Balls_Faced, 2) AS Strike_Rate,
        pi.Centuries,
        pi.Half_Centuries,
        pi.Not_Outs,
        pb.Balls_Faced,
        pb.Fours,
        pb.Sixes
    FROM Player p
    JOIN PerBatsmanBalls   pb ON pb.Player_Id = p.Player_Id
    JOIN PerBatsmanInnings pi ON pi.Player_Id = p.Player_Id
    WHERE p.Player_Name = 'Gautam Gambhir'
    ;
  """
},
{"query": "Give a highlight of Sachin Tendulkars career",
 "tables": ["Ball_by_Ball", "Batsman_Scored", "Wicket_Taken", "Player_Match", "Player"],
  "sql": """
    WITH
    InningStats AS (
        SELECT
            bbb.Striker           AS Player_Id,
            bbb.Match_Id,
            bbb.Innings_No,
            SUM(bs.Runs_Scored)   AS Runs,
            CASE 
              WHEN MAX(wt.Player_Out) IS NULL THEN 1 
              ELSE 0 
            END                    AS NotOut
        FROM Ball_by_Ball bbb
        JOIN Batsman_Scored bs
          ON  bbb.Match_Id   = bs.Match_Id
          AND bbb.Over_Id    = bs.Over_Id
          AND bbb.Ball_Id    = bs.Ball_Id
          AND bbb.Innings_No = bs.Innings_No
        LEFT JOIN Wicket_Taken wt
          ON  bbb.Match_Id   = wt.Match_Id
          AND bbb.Over_Id    = wt.Over_Id
          AND bbb.Ball_Id    = wt.Ball_Id
          AND bbb.Innings_No = wt.Innings_No
          AND wt.Player_Out  = bbb.Striker
        GROUP BY bbb.Striker, bbb.Match_Id, bbb.Innings_No
    ),
    PerBatsmanInnings AS (
        SELECT
            Player_Id,
            COUNT(*)                                    AS Innings_Played,
            MAX(Runs)                                   AS Highest_Score,
            SUM(CASE WHEN Runs >= 100 THEN 1 ELSE 0 END) AS Centuries,
            SUM(CASE WHEN Runs BETWEEN 50 AND 99 THEN 1 ELSE 0 END) AS Half_Centuries,
            SUM(NotOut)                                 AS Not_Outs
        FROM InningStats
        GROUP BY Player_Id
    ),
    PerBatsmanBalls AS (
        SELECT
            bbb.Striker           AS Player_Id,
            COUNT(DISTINCT pm.Match_Id)                 AS Matches_Played,
            SUM(bs.Runs_Scored)                         AS Runs_Scored,
            COUNT(*)                                    AS Balls_Faced,
            SUM(CASE WHEN bs.Runs_Scored = 4 THEN 1 ELSE 0 END) AS Fours,
            SUM(CASE WHEN bs.Runs_Scored = 6 THEN 1 ELSE 0 END) AS Sixes
        FROM Ball_by_Ball bbb
        JOIN Batsman_Scored bs
          ON  bbb.Match_Id   = bs.Match_Id
          AND bbb.Over_Id    = bs.Over_Id
          AND bbb.Ball_Id    = bs.Ball_Id
          AND bbb.Innings_No = bs.Innings_No
        JOIN Player_Match pm
          ON  bbb.Striker    = pm.Player_Id
          AND bbb.Match_Id   = pm.Match_Id
        GROUP BY bbb.Striker
    )
    SELECT
        p.Player_Name               AS Player,
        pb.Matches_Played,
        pi.Innings_Played            AS Innings,
        pb.Runs_Scored,
        pi.Highest_Score,
        CASE 
          WHEN (pi.Innings_Played - pi.Not_Outs) = 0 
          THEN NULL 
          ELSE ROUND(pb.Runs_Scored * 1.0 
                     / (pi.Innings_Played - pi.Not_Outs), 2) 
        END                          AS Batting_Average,
        ROUND(100.0 * pb.Runs_Scored / pb.Balls_Faced, 2) AS Strike_Rate,
        pi.Centuries,
        pi.Half_Centuries,
        pi.Not_Outs,
        pb.Balls_Faced,
        pb.Fours,
        pb.Sixes
    FROM Player p
    JOIN PerBatsmanBalls   pb ON pb.Player_Id = p.Player_Id
    JOIN PerBatsmanInnings pi ON pi.Player_Id = p.Player_Id
    WHERE p.Player_Name = 'Sachin Tendulkar'
    ;
  """
},
{"query": "Give a highlight of Sachin Tendulkars career",
 "tables": ["Ball_by_Ball", "Batsman_Scored", "Wicket_Taken", "Player_Match", "Player"],
  "sql": """
    WITH
    InningStats AS (
        SELECT
            bbb.Striker           AS Player_Id,
            bbb.Match_Id,
            bbb.Innings_No,
            SUM(bs.Runs_Scored)   AS Runs,
            CASE 
              WHEN MAX(wt.Player_Out) IS NULL THEN 1 
              ELSE 0 
            END                    AS NotOut
        FROM Ball_by_Ball bbb
        JOIN Batsman_Scored bs
          ON  bbb.Match_Id   = bs.Match_Id
          AND bbb.Over_Id    = bs.Over_Id
          AND bbb.Ball_Id    = bs.Ball_Id
          AND bbb.Innings_No = bs.Innings_No
        LEFT JOIN Wicket_Taken wt
          ON  bbb.Match_Id   = wt.Match_Id
          AND bbb.Over_Id    = wt.Over_Id
          AND bbb.Ball_Id    = wt.Ball_Id
          AND bbb.Innings_No = wt.Innings_No
          AND wt.Player_Out  = bbb.Striker
        GROUP BY bbb.Striker, bbb.Match_Id, bbb.Innings_No
    ),
    PerBatsmanInnings AS (
        SELECT
            Player_Id,
            COUNT(*)                                    AS Innings_Played,
            MAX(Runs)                                   AS Highest_Score,
            SUM(CASE WHEN Runs >= 100 THEN 1 ELSE 0 END) AS Centuries,
            SUM(CASE WHEN Runs BETWEEN 50 AND 99 THEN 1 ELSE 0 END) AS Half_Centuries,
            SUM(NotOut)                                 AS Not_Outs
        FROM InningStats
        GROUP BY Player_Id
    ),
    PerBatsmanBalls AS (
        SELECT
            bbb.Striker           AS Player_Id,
            COUNT(DISTINCT pm.Match_Id)                 AS Matches_Played,
            SUM(bs.Runs_Scored)                         AS Runs_Scored,
            COUNT(*)                                    AS Balls_Faced,
            SUM(CASE WHEN bs.Runs_Scored = 4 THEN 1 ELSE 0 END) AS Fours,
            SUM(CASE WHEN bs.Runs_Scored = 6 THEN 1 ELSE 0 END) AS Sixes
        FROM Ball_by_Ball bbb
        JOIN Batsman_Scored bs
          ON  bbb.Match_Id   = bs.Match_Id
          AND bbb.Over_Id    = bs.Over_Id
          AND bbb.Ball_Id    = bs.Ball_Id
          AND bbb.Innings_No = bs.Innings_No
        JOIN Player_Match pm
          ON  bbb.Striker    = pm.Player_Id
          AND bbb.Match_Id   = pm.Match_Id
        GROUP BY bbb.Striker
    )
    SELECT
        p.Player_Name               AS Player,
        pb.Matches_Played,
        pi.Innings_Played            AS Innings,
        pb.Runs_Scored,
        pi.Highest_Score,
        CASE 
          WHEN (pi.Innings_Played - pi.Not_Outs) = 0 
          THEN NULL 
          ELSE ROUND(pb.Runs_Scored * 1.0 
                     / (pi.Innings_Played - pi.Not_Outs), 2) 
        END                          AS Batting_Average,
        ROUND(100.0 * pb.Runs_Scored / pb.Balls_Faced, 2) AS Strike_Rate,
        pi.Centuries,
        pi.Half_Centuries,
        pi.Not_Outs,
        pb.Balls_Faced,
        pb.Fours,
        pb.Sixes
    FROM Player p
    JOIN PerBatsmanBalls   pb ON pb.Player_Id = p.Player_Id
    JOIN PerBatsmanInnings pi ON pi.Player_Id = p.Player_Id
    WHERE p.Player_Name = 'Sachin Tendulkar'
    ;
  """
},
{"query": "tell me about Sourav Ganguly",
 "tables": ["Ball_by_Ball", "Batsman_Scored", "Wicket_Taken", "Player_Match", "Player"],
  "sql": """
    WITH
    InningStats AS (
        SELECT
            bbb.Striker           AS Player_Id,
            bbb.Match_Id,
            bbb.Innings_No,
            SUM(bs.Runs_Scored)   AS Runs,
            CASE 
              WHEN MAX(wt.Player_Out) IS NULL THEN 1 
              ELSE 0 
            END                    AS NotOut
        FROM Ball_by_Ball bbb
        JOIN Batsman_Scored bs
          ON  bbb.Match_Id   = bs.Match_Id
          AND bbb.Over_Id    = bs.Over_Id
          AND bbb.Ball_Id    = bs.Ball_Id
          AND bbb.Innings_No = bs.Innings_No
        LEFT JOIN Wicket_Taken wt
          ON  bbb.Match_Id   = wt.Match_Id
          AND bbb.Over_Id    = wt.Over_Id
          AND bbb.Ball_Id    = wt.Ball_Id
          AND bbb.Innings_No = wt.Innings_No
          AND wt.Player_Out  = bbb.Striker
        GROUP BY bbb.Striker, bbb.Match_Id, bbb.Innings_No
    ),
    PerBatsmanInnings AS (
        SELECT
            Player_Id,
            COUNT(*)                                    AS Innings_Played,
            MAX(Runs)                                   AS Highest_Score,
            SUM(CASE WHEN Runs >= 100 THEN 1 ELSE 0 END) AS Centuries,
            SUM(CASE WHEN Runs BETWEEN 50 AND 99 THEN 1 ELSE 0 END) AS Half_Centuries,
            SUM(NotOut)                                 AS Not_Outs
        FROM InningStats
        GROUP BY Player_Id
    ),
    PerBatsmanBalls AS (
        SELECT
            bbb.Striker           AS Player_Id,
            COUNT(DISTINCT pm.Match_Id)                 AS Matches_Played,
            SUM(bs.Runs_Scored)                         AS Runs_Scored,
            COUNT(*)                                    AS Balls_Faced,
            SUM(CASE WHEN bs.Runs_Scored = 4 THEN 1 ELSE 0 END) AS Fours,
            SUM(CASE WHEN bs.Runs_Scored = 6 THEN 1 ELSE 0 END) AS Sixes
        FROM Ball_by_Ball bbb
        JOIN Batsman_Scored bs
          ON  bbb.Match_Id   = bs.Match_Id
          AND bbb.Over_Id    = bs.Over_Id
          AND bbb.Ball_Id    = bs.Ball_Id
          AND bbb.Innings_No = bs.Innings_No
        JOIN Player_Match pm
          ON  bbb.Striker    = pm.Player_Id
          AND bbb.Match_Id   = pm.Match_Id
        GROUP BY bbb.Striker
    )
    SELECT
        p.Player_Name               AS Player,
        pb.Matches_Played,
        pi.Innings_Played            AS Innings,
        pb.Runs_Scored,
        pi.Highest_Score,
        CASE 
          WHEN (pi.Innings_Played - pi.Not_Outs) = 0 
          THEN NULL 
          ELSE ROUND(pb.Runs_Scored * 1.0 
                     / (pi.Innings_Played - pi.Not_Outs), 2) 
        END                          AS Batting_Average,
        ROUND(100.0 * pb.Runs_Scored / pb.Balls_Faced, 2) AS Strike_Rate,
        pi.Centuries,
        pi.Half_Centuries,
        pi.Not_Outs,
        pb.Balls_Faced,
        pb.Fours,
        pb.Sixes
    FROM Player p
    JOIN PerBatsmanBalls   pb ON pb.Player_Id = p.Player_Id
    JOIN PerBatsmanInnings pi ON pi.Player_Id = p.Player_Id
    WHERE p.Player_Name = 'Sourav Ganguly'
    ;
  """
},
{"query": "What has Dinesh Karthik done in his career",
 "tables": ["Ball_by_Ball", "Batsman_Scored", "Wicket_Taken", "Player_Match", "Player"],
  "sql": """
    WITH
    InningStats AS (
        SELECT
            bbb.Striker           AS Player_Id,
            bbb.Match_Id,
            bbb.Innings_No,
            SUM(bs.Runs_Scored)   AS Runs,
            CASE 
              WHEN MAX(wt.Player_Out) IS NULL THEN 1 
              ELSE 0 
            END                    AS NotOut
        FROM Ball_by_Ball bbb
        JOIN Batsman_Scored bs
          ON  bbb.Match_Id   = bs.Match_Id
          AND bbb.Over_Id    = bs.Over_Id
          AND bbb.Ball_Id    = bs.Ball_Id
          AND bbb.Innings_No = bs.Innings_No
        LEFT JOIN Wicket_Taken wt
          ON  bbb.Match_Id   = wt.Match_Id
          AND bbb.Over_Id    = wt.Over_Id
          AND bbb.Ball_Id    = wt.Ball_Id
          AND bbb.Innings_No = wt.Innings_No
          AND wt.Player_Out  = bbb.Striker
        GROUP BY bbb.Striker, bbb.Match_Id, bbb.Innings_No
    ),
    PerBatsmanInnings AS (
        SELECT
            Player_Id,
            COUNT(*)                                    AS Innings_Played,
            MAX(Runs)                                   AS Highest_Score,
            SUM(CASE WHEN Runs >= 100 THEN 1 ELSE 0 END) AS Centuries,
            SUM(CASE WHEN Runs BETWEEN 50 AND 99 THEN 1 ELSE 0 END) AS Half_Centuries,
            SUM(NotOut)                                 AS Not_Outs
        FROM InningStats
        GROUP BY Player_Id
    ),
    PerBatsmanBalls AS (
        SELECT
            bbb.Striker           AS Player_Id,
            COUNT(DISTINCT pm.Match_Id)                 AS Matches_Played,
            SUM(bs.Runs_Scored)                         AS Runs_Scored,
            COUNT(*)                                    AS Balls_Faced,
            SUM(CASE WHEN bs.Runs_Scored = 4 THEN 1 ELSE 0 END) AS Fours,
            SUM(CASE WHEN bs.Runs_Scored = 6 THEN 1 ELSE 0 END) AS Sixes
        FROM Ball_by_Ball bbb
        JOIN Batsman_Scored bs
          ON  bbb.Match_Id   = bs.Match_Id
          AND bbb.Over_Id    = bs.Over_Id
          AND bbb.Ball_Id    = bs.Ball_Id
          AND bbb.Innings_No = bs.Innings_No
        JOIN Player_Match pm
          ON  bbb.Striker    = pm.Player_Id
          AND bbb.Match_Id   = pm.Match_Id
        GROUP BY bbb.Striker
    )
    SELECT
        p.Player_Name               AS Player,
        pb.Matches_Played,
        pi.Innings_Played            AS Innings,
        pb.Runs_Scored,
        pi.Highest_Score,
        CASE 
          WHEN (pi.Innings_Played - pi.Not_Outs) = 0 
          THEN NULL 
          ELSE ROUND(pb.Runs_Scored * 1.0 
                     / (pi.Innings_Played - pi.Not_Outs), 2) 
        END                          AS Batting_Average,
        ROUND(100.0 * pb.Runs_Scored / pb.Balls_Faced, 2) AS Strike_Rate,
        pi.Centuries,
        pi.Half_Centuries,
        pi.Not_Outs,
        pb.Balls_Faced,
        pb.Fours,
        pb.Sixes
    FROM Player p
    JOIN PerBatsmanBalls   pb ON pb.Player_Id = p.Player_Id
    JOIN PerBatsmanInnings pi ON pi.Player_Id = p.Player_Id
    WHERE p.Player_Name = 'Dinesh Karthik'
    ;
  """
},
{"query": "Tell me about Dinesh Karthik",
 "tables": ["Ball_by_Ball", "Batsman_Scored", "Wicket_Taken", "Player_Match", "Player"],
  "sql": """
    WITH
    InningStats AS (
        SELECT
            bbb.Striker           AS Player_Id,
            bbb.Match_Id,
            bbb.Innings_No,
            SUM(bs.Runs_Scored)   AS Runs,
            CASE 
              WHEN MAX(wt.Player_Out) IS NULL THEN 1 
              ELSE 0 
            END                    AS NotOut
        FROM Ball_by_Ball bbb
        JOIN Batsman_Scored bs
          ON  bbb.Match_Id   = bs.Match_Id
          AND bbb.Over_Id    = bs.Over_Id
          AND bbb.Ball_Id    = bs.Ball_Id
          AND bbb.Innings_No = bs.Innings_No
        LEFT JOIN Wicket_Taken wt
          ON  bbb.Match_Id   = wt.Match_Id
          AND bbb.Over_Id    = wt.Over_Id
          AND bbb.Ball_Id    = wt.Ball_Id
          AND bbb.Innings_No = wt.Innings_No
          AND wt.Player_Out  = bbb.Striker
        GROUP BY bbb.Striker, bbb.Match_Id, bbb.Innings_No
    ),
    PerBatsmanInnings AS (
        SELECT
            Player_Id,
            COUNT(*)                                    AS Innings_Played,
            MAX(Runs)                                   AS Highest_Score,
            SUM(CASE WHEN Runs >= 100 THEN 1 ELSE 0 END) AS Centuries,
            SUM(CASE WHEN Runs BETWEEN 50 AND 99 THEN 1 ELSE 0 END) AS Half_Centuries,
            SUM(NotOut)                                 AS Not_Outs
        FROM InningStats
        GROUP BY Player_Id
    ),
    PerBatsmanBalls AS (
        SELECT
            bbb.Striker           AS Player_Id,
            COUNT(DISTINCT pm.Match_Id)                 AS Matches_Played,
            SUM(bs.Runs_Scored)                         AS Runs_Scored,
            COUNT(*)                                    AS Balls_Faced,
            SUM(CASE WHEN bs.Runs_Scored = 4 THEN 1 ELSE 0 END) AS Fours,
            SUM(CASE WHEN bs.Runs_Scored = 6 THEN 1 ELSE 0 END) AS Sixes
        FROM Ball_by_Ball bbb
        JOIN Batsman_Scored bs
          ON  bbb.Match_Id   = bs.Match_Id
          AND bbb.Over_Id    = bs.Over_Id
          AND bbb.Ball_Id    = bs.Ball_Id
          AND bbb.Innings_No = bs.Innings_No
        JOIN Player_Match pm
          ON  bbb.Striker    = pm.Player_Id
          AND bbb.Match_Id   = pm.Match_Id
        GROUP BY bbb.Striker
    )
    SELECT
        p.Player_Name               AS Player,
        pb.Matches_Played,
        pi.Innings_Played            AS Innings,
        pb.Runs_Scored,
        pi.Highest_Score,
        CASE 
          WHEN (pi.Innings_Played - pi.Not_Outs) = 0 
          THEN NULL 
          ELSE ROUND(pb.Runs_Scored * 1.0 
                     / (pi.Innings_Played - pi.Not_Outs), 2) 
        END                          AS Batting_Average,
        ROUND(100.0 * pb.Runs_Scored / pb.Balls_Faced, 2) AS Strike_Rate,
        pi.Centuries,
        pi.Half_Centuries,
        pi.Not_Outs,
        pb.Balls_Faced,
        pb.Fours,
        pb.Sixes
    FROM Player p
    JOIN PerBatsmanBalls   pb ON pb.Player_Id = p.Player_Id
    JOIN PerBatsmanInnings pi ON pi.Player_Id = p.Player_Id
    WHERE p.Player_Name = 'Dinesh Karthik'
    ;
  """
},
{
  "query": "Summarize bowling stats for Zaheer Khan",
  "tables": ["Ball_by_Ball", "Wicket_Taken", "Batsman_Scored", "Player_Match", "Player"],
  "sql": """
    WITH
    InningStats AS (
      SELECT
        bbb.Bowler           AS Player_Id,
        bbb.Match_Id,
        bbb.Innings_No,
        COUNT(wt.Player_Out) AS Wickets,
        SUM(COALESCE(bs.Runs_Scored,0)) AS Runs_Conceded
      FROM Ball_by_Ball bbb
      LEFT JOIN Wicket_Taken wt
        ON  wt.Match_Id   = bbb.Match_Id
        AND wt.Over_Id    = bbb.Over_Id
        AND wt.Ball_Id    = bbb.Ball_Id
        AND wt.Innings_No = bbb.Innings_No
      LEFT JOIN Batsman_Scored bs
        ON  bs.Match_Id   = bbb.Match_Id
        AND bs.Over_Id    = bbb.Over_Id
        AND bs.Ball_Id    = bbb.Ball_Id
        AND bs.Innings_No = bbb.Innings_No
      GROUP BY
        bbb.Bowler,
        bbb.Match_Id,
        bbb.Innings_No
    ),
    PerBowlerInnings AS (
      SELECT
        Player_Id,
        COUNT(*)                                     AS Innings_Bowled,
        MAX(Wickets)                                 AS Best_Bowling_Innings,
        SUM(CASE WHEN Wickets >= 5 THEN 1 ELSE 0 END) AS Five_Wicket_Hauls
      FROM InningStats
      GROUP BY Player_Id
    ),
    PerBowlerBalls AS (
      SELECT
        bbb.Bowler                   AS Player_Id,
        COUNT(DISTINCT pm.Match_Id)  AS Matches_Played,
        COUNT(*)                     AS Balls_Bowled,
        SUM(COALESCE(bs.Runs_Scored,0)) AS Runs_Conceded,
        COUNT(wt.Player_Out)         AS Wickets_Taken
      FROM Ball_by_Ball bbb
      LEFT JOIN Batsman_Scored bs
        ON  bs.Match_Id   = bbb.Match_Id
        AND bs.Over_Id    = bbb.Over_Id
        AND bs.Ball_Id    = bbb.Ball_Id
        AND bs.Innings_No = bbb.Innings_No
      LEFT JOIN Wicket_Taken wt
        ON  wt.Match_Id   = bbb.Match_Id
        AND wt.Over_Id    = bbb.Over_Id
        AND wt.Ball_Id    = bbb.Ball_Id
        AND wt.Innings_No = bbb.Innings_No
      JOIN Player_Match pm
        ON  pm.Player_Id  = bbb.Bowler
        AND pm.Match_Id   = bbb.Match_Id
      GROUP BY bbb.Bowler
    )
    SELECT
      p.Player_Name                   AS Player,
      pb.Matches_Played,
      pi.Innings_Bowled,
      pb.Balls_Bowled,
      pb.Runs_Conceded,
      pb.Wickets_Taken,
      pi.Best_Bowling_Innings,
      CASE 
        WHEN pb.Wickets_Taken = 0 THEN NULL
        ELSE ROUND(pb.Runs_Conceded * 1.0 / pb.Wickets_Taken, 2)
      END                             AS Bowling_Average,
      CASE 
        WHEN pb.Balls_Bowled = 0 THEN NULL
        ELSE ROUND(pb.Runs_Conceded * 6.0 / pb.Balls_Bowled, 2)
      END                             AS Economy_Rate,
      CASE 
        WHEN pb.Wickets_Taken = 0 THEN NULL
        ELSE ROUND(pb.Balls_Bowled * 1.0 / pb.Wickets_Taken, 2)
      END                             AS Bowling_Strike_Rate,
      pi.Five_Wicket_Hauls
    FROM Player p
    JOIN PerBowlerBalls   pb ON pb.Player_Id   = p.Player_Id
    JOIN PerBowlerInnings pi ON pi.Player_Id   = p.Player_Id
    WHERE p.Player_Name = 'Zaheer Khan';
  """
},
{
  "query": "tell me about the bowling stats of Ashish Nehra",
  "tables": ["Ball_by_Ball", "Wicket_Taken", "Batsman_Scored", "Player_Match", "Player"],
  "sql": """
    WITH
    InningStats AS (
      SELECT
        bbb.Bowler           AS Player_Id,
        bbb.Match_Id,
        bbb.Innings_No,
        COUNT(wt.Player_Out) AS Wickets,
        SUM(COALESCE(bs.Runs_Scored,0)) AS Runs_Conceded
      FROM Ball_by_Ball bbb
      LEFT JOIN Wicket_Taken wt
        ON  wt.Match_Id   = bbb.Match_Id
        AND wt.Over_Id    = bbb.Over_Id
        AND wt.Ball_Id    = bbb.Ball_Id
        AND wt.Innings_No = bbb.Innings_No
      LEFT JOIN Batsman_Scored bs
        ON  bs.Match_Id   = bbb.Match_Id
        AND bs.Over_Id    = bbb.Over_Id
        AND bs.Ball_Id    = bbb.Ball_Id
        AND bs.Innings_No = bbb.Innings_No
      GROUP BY
        bbb.Bowler,
        bbb.Match_Id,
        bbb.Innings_No
    ),
    PerBowlerInnings AS (
      SELECT
        Player_Id,
        COUNT(*)                                     AS Innings_Bowled,
        MAX(Wickets)                                 AS Best_Bowling_Innings,
        SUM(CASE WHEN Wickets >= 5 THEN 1 ELSE 0 END) AS Five_Wicket_Hauls
      FROM InningStats
      GROUP BY Player_Id
    ),
    PerBowlerBalls AS (
      SELECT
        bbb.Bowler                   AS Player_Id,
        COUNT(DISTINCT pm.Match_Id)  AS Matches_Played,
        COUNT(*)                     AS Balls_Bowled,
        SUM(COALESCE(bs.Runs_Scored,0)) AS Runs_Conceded,
        COUNT(wt.Player_Out)         AS Wickets_Taken
      FROM Ball_by_Ball bbb
      LEFT JOIN Batsman_Scored bs
        ON  bs.Match_Id   = bbb.Match_Id
        AND bs.Over_Id    = bbb.Over_Id
        AND bs.Ball_Id    = bbb.Ball_Id
        AND bs.Innings_No = bbb.Innings_No
      LEFT JOIN Wicket_Taken wt
        ON  wt.Match_Id   = bbb.Match_Id
        AND wt.Over_Id    = bbb.Over_Id
        AND wt.Ball_Id    = bbb.Ball_Id
        AND wt.Innings_No = bbb.Innings_No
      JOIN Player_Match pm
        ON  pm.Player_Id  = bbb.Bowler
        AND pm.Match_Id   = bbb.Match_Id
      GROUP BY bbb.Bowler
    )
    SELECT
      p.Player_Name                   AS Player,
      pb.Matches_Played,
      pi.Innings_Bowled,
      pb.Balls_Bowled,
      pb.Runs_Conceded,
      pb.Wickets_Taken,
      pi.Best_Bowling_Innings,
      CASE 
        WHEN pb.Wickets_Taken = 0 THEN NULL
        ELSE ROUND(pb.Runs_Conceded * 1.0 / pb.Wickets_Taken, 2)
      END                             AS Bowling_Average,
      CASE 
        WHEN pb.Balls_Bowled = 0 THEN NULL
        ELSE ROUND(pb.Runs_Conceded * 6.0 / pb.Balls_Bowled, 2)
      END                             AS Economy_Rate,
      CASE 
        WHEN pb.Wickets_Taken = 0 THEN NULL
        ELSE ROUND(pb.Balls_Bowled * 1.0 / pb.Wickets_Taken, 2)
      END                             AS Bowling_Strike_Rate,
      pi.Five_Wicket_Hauls
    FROM Player p
    JOIN PerBowlerBalls   pb ON pb.Player_Id   = p.Player_Id
    JOIN PerBowlerInnings pi ON pi.Player_Id   = p.Player_Id
    WHERE p.Player_Name = 'Ashish Nehra';
  """
},
{
  "query": "what type of bowler was Brett Lee",
  "tables": ["Ball_by_Ball", "Wicket_Taken", "Batsman_Scored", "Player_Match", "Player"],
  "sql": """
    WITH
    InningStats AS (
      SELECT
        bbb.Bowler           AS Player_Id,
        bbb.Match_Id,
        bbb.Innings_No,
        COUNT(wt.Player_Out) AS Wickets,
        SUM(COALESCE(bs.Runs_Scored,0)) AS Runs_Conceded
      FROM Ball_by_Ball bbb
      LEFT JOIN Wicket_Taken wt
        ON  wt.Match_Id   = bbb.Match_Id
        AND wt.Over_Id    = bbb.Over_Id
        AND wt.Ball_Id    = bbb.Ball_Id
        AND wt.Innings_No = bbb.Innings_No
      LEFT JOIN Batsman_Scored bs
        ON  bs.Match_Id   = bbb.Match_Id
        AND bs.Over_Id    = bbb.Over_Id
        AND bs.Ball_Id    = bbb.Ball_Id
        AND bs.Innings_No = bbb.Innings_No
      GROUP BY
        bbb.Bowler,
        bbb.Match_Id,
        bbb.Innings_No
    ),
    PerBowlerInnings AS (
      SELECT
        Player_Id,
        COUNT(*)                                     AS Innings_Bowled,
        MAX(Wickets)                                 AS Best_Bowling_Innings,
        SUM(CASE WHEN Wickets >= 5 THEN 1 ELSE 0 END) AS Five_Wicket_Hauls
      FROM InningStats
      GROUP BY Player_Id
    ),
    PerBowlerBalls AS (
      SELECT
        bbb.Bowler                   AS Player_Id,
        COUNT(DISTINCT pm.Match_Id)  AS Matches_Played,
        COUNT(*)                     AS Balls_Bowled,
        SUM(COALESCE(bs.Runs_Scored,0)) AS Runs_Conceded,
        COUNT(wt.Player_Out)         AS Wickets_Taken
      FROM Ball_by_Ball bbb
      LEFT JOIN Batsman_Scored bs
        ON  bs.Match_Id   = bbb.Match_Id
        AND bs.Over_Id    = bbb.Over_Id
        AND bs.Ball_Id    = bbb.Ball_Id
        AND bs.Innings_No = bbb.Innings_No
      LEFT JOIN Wicket_Taken wt
        ON  wt.Match_Id   = bbb.Match_Id
        AND wt.Over_Id    = bbb.Over_Id
        AND wt.Ball_Id    = bbb.Ball_Id
        AND wt.Innings_No = bbb.Innings_No
      JOIN Player_Match pm
        ON  pm.Player_Id  = bbb.Bowler
        AND pm.Match_Id   = bbb.Match_Id
      GROUP BY bbb.Bowler
    )
    SELECT
      p.Player_Name                   AS Player,
      pb.Matches_Played,
      pi.Innings_Bowled,
      pb.Balls_Bowled,
      pb.Runs_Conceded,
      pb.Wickets_Taken,
      pi.Best_Bowling_Innings,
      CASE 
        WHEN pb.Wickets_Taken = 0 THEN NULL
        ELSE ROUND(pb.Runs_Conceded * 1.0 / pb.Wickets_Taken, 2)
      END                             AS Bowling_Average,
      CASE 
        WHEN pb.Balls_Bowled = 0 THEN NULL
        ELSE ROUND(pb.Runs_Conceded * 6.0 / pb.Balls_Bowled, 2)
      END                             AS Economy_Rate,
      CASE 
        WHEN pb.Wickets_Taken = 0 THEN NULL
        ELSE ROUND(pb.Balls_Bowled * 1.0 / pb.Wickets_Taken, 2)
      END                             AS Bowling_Strike_Rate,
      pi.Five_Wicket_Hauls
    FROM Player p
    JOIN PerBowlerBalls   pb ON pb.Player_Id   = p.Player_Id
    JOIN PerBowlerInnings pi ON pi.Player_Id   = p.Player_Id
    WHERE p.Player_Name = 'Brett Lee';
  """
},
{
  "query": "Summarize bowling stats for Morne Morkel",
  "tables": ["Ball_by_Ball", "Wicket_Taken", "Batsman_Scored", "Player_Match", "Player"],
  "sql": """
    WITH
    InningStats AS (
      SELECT
        bbb.Bowler           AS Player_Id,
        bbb.Match_Id,
        bbb.Innings_No,
        COUNT(wt.Player_Out) AS Wickets,
        SUM(COALESCE(bs.Runs_Scored,0)) AS Runs_Conceded
      FROM Ball_by_Ball bbb
      LEFT JOIN Wicket_Taken wt
        ON  wt.Match_Id   = bbb.Match_Id
        AND wt.Over_Id    = bbb.Over_Id
        AND wt.Ball_Id    = bbb.Ball_Id
        AND wt.Innings_No = bbb.Innings_No
      LEFT JOIN Batsman_Scored bs
        ON  bs.Match_Id   = bbb.Match_Id
        AND bs.Over_Id    = bbb.Over_Id
        AND bs.Ball_Id    = bbb.Ball_Id
        AND bs.Innings_No = bbb.Innings_No
      GROUP BY
        bbb.Bowler,
        bbb.Match_Id,
        bbb.Innings_No
    ),
    PerBowlerInnings AS (
      SELECT
        Player_Id,
        COUNT(*)                                     AS Innings_Bowled,
        MAX(Wickets)                                 AS Best_Bowling_Innings,
        SUM(CASE WHEN Wickets >= 5 THEN 1 ELSE 0 END) AS Five_Wicket_Hauls
      FROM InningStats
      GROUP BY Player_Id
    ),
    PerBowlerBalls AS (
      SELECT
        bbb.Bowler                   AS Player_Id,
        COUNT(DISTINCT pm.Match_Id)  AS Matches_Played,
        COUNT(*)                     AS Balls_Bowled,
        SUM(COALESCE(bs.Runs_Scored,0)) AS Runs_Conceded,
        COUNT(wt.Player_Out)         AS Wickets_Taken
      FROM Ball_by_Ball bbb
      LEFT JOIN Batsman_Scored bs
        ON  bs.Match_Id   = bbb.Match_Id
        AND bs.Over_Id    = bbb.Over_Id
        AND bs.Ball_Id    = bbb.Ball_Id
        AND bs.Innings_No = bbb.Innings_No
      LEFT JOIN Wicket_Taken wt
        ON  wt.Match_Id   = bbb.Match_Id
        AND wt.Over_Id    = bbb.Over_Id
        AND wt.Ball_Id    = bbb.Ball_Id
        AND wt.Innings_No = bbb.Innings_No
      JOIN Player_Match pm
        ON  pm.Player_Id  = bbb.Bowler
        AND pm.Match_Id   = bbb.Match_Id
      GROUP BY bbb.Bowler
    )
    SELECT
      p.Player_Name                   AS Player,
      pb.Matches_Played,
      pi.Innings_Bowled,
      pb.Balls_Bowled,
      pb.Runs_Conceded,
      pb.Wickets_Taken,
      pi.Best_Bowling_Innings,
      CASE 
        WHEN pb.Wickets_Taken = 0 THEN NULL
        ELSE ROUND(pb.Runs_Conceded * 1.0 / pb.Wickets_Taken, 2)
      END                             AS Bowling_Average,
      CASE 
        WHEN pb.Balls_Bowled = 0 THEN NULL
        ELSE ROUND(pb.Runs_Conceded * 6.0 / pb.Balls_Bowled, 2)
      END                             AS Economy_Rate,
      CASE 
        WHEN pb.Wickets_Taken = 0 THEN NULL
        ELSE ROUND(pb.Balls_Bowled * 1.0 / pb.Wickets_Taken, 2)
      END                             AS Bowling_Strike_Rate,
      pi.Five_Wicket_Hauls
    FROM Player p
    JOIN PerBowlerBalls   pb ON pb.Player_Id   = p.Player_Id
    JOIN PerBowlerInnings pi ON pi.Player_Id   = p.Player_Id
    WHERE p.Player_Name = 'Morne Morkel';
  """
},
{
  "query": "What type of bowler was Piyush Chawla",
  "tables": ["Ball_by_Ball", "Wicket_Taken", "Batsman_Scored", "Player_Match", "Player"],
  "sql": """
    WITH
    InningStats AS (
      SELECT
        bbb.Bowler           AS Player_Id,
        bbb.Match_Id,
        bbb.Innings_No,
        COUNT(wt.Player_Out) AS Wickets,
        SUM(COALESCE(bs.Runs_Scored,0)) AS Runs_Conceded
      FROM Ball_by_Ball bbb
      LEFT JOIN Wicket_Taken wt
        ON  wt.Match_Id   = bbb.Match_Id
        AND wt.Over_Id    = bbb.Over_Id
        AND wt.Ball_Id    = bbb.Ball_Id
        AND wt.Innings_No = bbb.Innings_No
      LEFT JOIN Batsman_Scored bs
        ON  bs.Match_Id   = bbb.Match_Id
        AND bs.Over_Id    = bbb.Over_Id
        AND bs.Ball_Id    = bbb.Ball_Id
        AND bs.Innings_No = bbb.Innings_No
      GROUP BY
        bbb.Bowler,
        bbb.Match_Id,
        bbb.Innings_No
    ),
    PerBowlerInnings AS (
      SELECT
        Player_Id,
        COUNT(*)                                     AS Innings_Bowled,
        MAX(Wickets)                                 AS Best_Bowling_Innings,
        SUM(CASE WHEN Wickets >= 5 THEN 1 ELSE 0 END) AS Five_Wicket_Hauls
      FROM InningStats
      GROUP BY Player_Id
    ),
    PerBowlerBalls AS (
      SELECT
        bbb.Bowler                   AS Player_Id,
        COUNT(DISTINCT pm.Match_Id)  AS Matches_Played,
        COUNT(*)                     AS Balls_Bowled,
        SUM(COALESCE(bs.Runs_Scored,0)) AS Runs_Conceded,
        COUNT(wt.Player_Out)         AS Wickets_Taken
      FROM Ball_by_Ball bbb
      LEFT JOIN Batsman_Scored bs
        ON  bs.Match_Id   = bbb.Match_Id
        AND bs.Over_Id    = bbb.Over_Id
        AND bs.Ball_Id    = bbb.Ball_Id
        AND bs.Innings_No = bbb.Innings_No
      LEFT JOIN Wicket_Taken wt
        ON  wt.Match_Id   = bbb.Match_Id
        AND wt.Over_Id    = bbb.Over_Id
        AND wt.Ball_Id    = bbb.Ball_Id
        AND wt.Innings_No = bbb.Innings_No
      JOIN Player_Match pm
        ON  pm.Player_Id  = bbb.Bowler
        AND pm.Match_Id   = bbb.Match_Id
      GROUP BY bbb.Bowler
    )
    SELECT
      p.Player_Name                   AS Player,
      pb.Matches_Played,
      pi.Innings_Bowled,
      pb.Balls_Bowled,
      pb.Runs_Conceded,
      pb.Wickets_Taken,
      pi.Best_Bowling_Innings,
      CASE 
        WHEN pb.Wickets_Taken = 0 THEN NULL
        ELSE ROUND(pb.Runs_Conceded * 1.0 / pb.Wickets_Taken, 2)
      END                             AS Bowling_Average,
      CASE 
        WHEN pb.Balls_Bowled = 0 THEN NULL
        ELSE ROUND(pb.Runs_Conceded * 6.0 / pb.Balls_Bowled, 2)
      END                             AS Economy_Rate,
      CASE 
        WHEN pb.Wickets_Taken = 0 THEN NULL
        ELSE ROUND(pb.Balls_Bowled * 1.0 / pb.Wickets_Taken, 2)
      END                             AS Bowling_Strike_Rate,
      pi.Five_Wicket_Hauls
    FROM Player p
    JOIN PerBowlerBalls   pb ON pb.Player_Id   = p.Player_Id
    JOIN PerBowlerInnings pi ON pi.Player_Id   = p.Player_Id
    WHERE p.Player_Name = 'Piyush Chawla';
  """
},
{
  "query": "Tell me about bowler Munaf Patel",
  "tables": ["Ball_by_Ball", "Wicket_Taken", "Batsman_Scored", "Player_Match", "Player"],
  "sql": """
    WITH
    InningStats AS (
      SELECT
        bbb.Bowler           AS Player_Id,
        bbb.Match_Id,
        bbb.Innings_No,
        COUNT(wt.Player_Out) AS Wickets,
        SUM(COALESCE(bs.Runs_Scored,0)) AS Runs_Conceded
      FROM Ball_by_Ball bbb
      LEFT JOIN Wicket_Taken wt
        ON  wt.Match_Id   = bbb.Match_Id
        AND wt.Over_Id    = bbb.Over_Id
        AND wt.Ball_Id    = bbb.Ball_Id
        AND wt.Innings_No = bbb.Innings_No
      LEFT JOIN Batsman_Scored bs
        ON  bs.Match_Id   = bbb.Match_Id
        AND bs.Over_Id    = bbb.Over_Id
        AND bs.Ball_Id    = bbb.Ball_Id
        AND bs.Innings_No = bbb.Innings_No
      GROUP BY
        bbb.Bowler,
        bbb.Match_Id,
        bbb.Innings_No
    ),
    PerBowlerInnings AS (
      SELECT
        Player_Id,
        COUNT(*)                                     AS Innings_Bowled,
        MAX(Wickets)                                 AS Best_Bowling_Innings,
        SUM(CASE WHEN Wickets >= 5 THEN 1 ELSE 0 END) AS Five_Wicket_Hauls
      FROM InningStats
      GROUP BY Player_Id
    ),
    PerBowlerBalls AS (
      SELECT
        bbb.Bowler                   AS Player_Id,
        COUNT(DISTINCT pm.Match_Id)  AS Matches_Played,
        COUNT(*)                     AS Balls_Bowled,
        SUM(COALESCE(bs.Runs_Scored,0)) AS Runs_Conceded,
        COUNT(wt.Player_Out)         AS Wickets_Taken
      FROM Ball_by_Ball bbb
      LEFT JOIN Batsman_Scored bs
        ON  bs.Match_Id   = bbb.Match_Id
        AND bs.Over_Id    = bbb.Over_Id
        AND bs.Ball_Id    = bbb.Ball_Id
        AND bs.Innings_No = bbb.Innings_No
      LEFT JOIN Wicket_Taken wt
        ON  wt.Match_Id   = bbb.Match_Id
        AND wt.Over_Id    = bbb.Over_Id
        AND wt.Ball_Id    = bbb.Ball_Id
        AND wt.Innings_No = bbb.Innings_No
      JOIN Player_Match pm
        ON  pm.Player_Id  = bbb.Bowler
        AND pm.Match_Id   = bbb.Match_Id
      GROUP BY bbb.Bowler
    )
    SELECT
      p.Player_Name                   AS Player,
      pb.Matches_Played,
      pi.Innings_Bowled,
      pb.Balls_Bowled,
      pb.Runs_Conceded,
      pb.Wickets_Taken,
      pi.Best_Bowling_Innings,
      CASE 
        WHEN pb.Wickets_Taken = 0 THEN NULL
        ELSE ROUND(pb.Runs_Conceded * 1.0 / pb.Wickets_Taken, 2)
      END                             AS Bowling_Average,
      CASE 
        WHEN pb.Balls_Bowled = 0 THEN NULL
        ELSE ROUND(pb.Runs_Conceded * 6.0 / pb.Balls_Bowled, 2)
      END                             AS Economy_Rate,
      CASE 
        WHEN pb.Wickets_Taken = 0 THEN NULL
        ELSE ROUND(pb.Balls_Bowled * 1.0 / pb.Wickets_Taken, 2)
      END                             AS Bowling_Strike_Rate,
      pi.Five_Wicket_Hauls
    FROM Player p
    JOIN PerBowlerBalls   pb ON pb.Player_Id   = p.Player_Id
    JOIN PerBowlerInnings pi ON pi.Player_Id   = p.Player_Id
    WHERE p.Player_Name = 'Munaf Patel';
  """
},
{
  "query": "tell me about Lasith Malinga the bowler",
  "tables": ["Ball_by_Ball", "Wicket_Taken", "Batsman_Scored", "Player_Match", "Player"],
  "sql": """
    WITH
    InningStats AS (
      SELECT
        bbb.Bowler           AS Player_Id,
        bbb.Match_Id,
        bbb.Innings_No,
        COUNT(wt.Player_Out) AS Wickets,
        SUM(COALESCE(bs.Runs_Scored,0)) AS Runs_Conceded
      FROM Ball_by_Ball bbb
      LEFT JOIN Wicket_Taken wt
        ON  wt.Match_Id   = bbb.Match_Id
        AND wt.Over_Id    = bbb.Over_Id
        AND wt.Ball_Id    = bbb.Ball_Id
        AND wt.Innings_No = bbb.Innings_No
      LEFT JOIN Batsman_Scored bs
        ON  bs.Match_Id   = bbb.Match_Id
        AND bs.Over_Id    = bbb.Over_Id
        AND bs.Ball_Id    = bbb.Ball_Id
        AND bs.Innings_No = bbb.Innings_No
      GROUP BY
        bbb.Bowler,
        bbb.Match_Id,
        bbb.Innings_No
    ),
    PerBowlerInnings AS (
      SELECT
        Player_Id,
        COUNT(*)                                     AS Innings_Bowled,
        MAX(Wickets)                                 AS Best_Bowling_Innings,
        SUM(CASE WHEN Wickets >= 5 THEN 1 ELSE 0 END) AS Five_Wicket_Hauls
      FROM InningStats
      GROUP BY Player_Id
    ),
    PerBowlerBalls AS (
      SELECT
        bbb.Bowler                   AS Player_Id,
        COUNT(DISTINCT pm.Match_Id)  AS Matches_Played,
        COUNT(*)                     AS Balls_Bowled,
        SUM(COALESCE(bs.Runs_Scored,0)) AS Runs_Conceded,
        COUNT(wt.Player_Out)         AS Wickets_Taken
      FROM Ball_by_Ball bbb
      LEFT JOIN Batsman_Scored bs
        ON  bs.Match_Id   = bbb.Match_Id
        AND bs.Over_Id    = bbb.Over_Id
        AND bs.Ball_Id    = bbb.Ball_Id
        AND bs.Innings_No = bbb.Innings_No
      LEFT JOIN Wicket_Taken wt
        ON  wt.Match_Id   = bbb.Match_Id
        AND wt.Over_Id    = bbb.Over_Id
        AND wt.Ball_Id    = bbb.Ball_Id
        AND wt.Innings_No = bbb.Innings_No
      JOIN Player_Match pm
        ON  pm.Player_Id  = bbb.Bowler
        AND pm.Match_Id   = bbb.Match_Id
      GROUP BY bbb.Bowler
    )
    SELECT
      p.Player_Name                   AS Player,
      pb.Matches_Played,
      pi.Innings_Bowled,
      pb.Balls_Bowled,
      pb.Runs_Conceded,
      pb.Wickets_Taken,
      pi.Best_Bowling_Innings,
      CASE 
        WHEN pb.Wickets_Taken = 0 THEN NULL
        ELSE ROUND(pb.Runs_Conceded * 1.0 / pb.Wickets_Taken, 2)
      END                             AS Bowling_Average,
      CASE 
        WHEN pb.Balls_Bowled = 0 THEN NULL
        ELSE ROUND(pb.Runs_Conceded * 6.0 / pb.Balls_Bowled, 2)
      END                             AS Economy_Rate,
      CASE 
        WHEN pb.Wickets_Taken = 0 THEN NULL
        ELSE ROUND(pb.Balls_Bowled * 1.0 / pb.Wickets_Taken, 2)
      END                             AS Bowling_Strike_Rate,
      pi.Five_Wicket_Hauls
    FROM Player p
    JOIN PerBowlerBalls   pb ON pb.Player_Id   = p.Player_Id
    JOIN PerBowlerInnings pi ON pi.Player_Id   = p.Player_Id
    WHERE p.Player_Name = 'Lasith Malinga';
  """
},

{
      "query":"Bowlers who have bowled most deliveries",
      "tables": ["Ball_by_Ball", "Player", "Country", "Bowling_Style"],
      "sql": """SELECT Player_Name,c.Country_Name,d.Bowling_skill,count(*) as Deliveries
       FROM Ball_by_Ball a
       join Player b
       on a.Bowler==b.Player_Id
       join Country c
       on b.Country_Name==c.Country_Id
       join Bowling_Style d
       on b.Bowling_skill==d.Bowling_Id
       group by Bowler
       order by Deliveries desc;"""
    },
    { "query":"No of 5-wicket hauls by bowlers in an IPL ",
      "tables": ["Wicket_Taken", "Ball_by_Ball", "Player", "Country", "Bowling_Style"],
      "sql": """select Player_Name,Country_Name,Bowling_skill,
        count(*) as hauls
        from (select Player_Id,Player_Name,Country_Name,Bowling_skill,
              count(Kind_Out) as Wickets
              from Wicket_Taken a
              join Ball_by_Ball b
              on a.Match_Id=b.Match_Id 
              and a.Innings_No=b.Innings_No
              and a.Over_Id=b.Over_Id 
              and a.Ball_Id=b.Ball_Id
              join (select Player_Id,Player_Name,b.Country_Name, c.Bowling_skill
                    from Player a
                    join Country b
                    on a.Country_Name=b.Country_Id
                    join Bowling_Style c
                    on a.Bowling_skill=c.Bowling_Id) c
             on b.Bowler=c.Player_Id
             where Kind_Out in (1,2,4,6,7,8)
             group by c.Player_Id,a.Match_Id
             having Wickets >=5)
             group by Player_Id
             order by hauls desc; """
    },
    
     {"query":"Highest run score by a batsman in an IPL match",
      "tables": ["Ball_by_Ball", "Batsman_Scored", "Player", "Country", "Batting_Style"],
      "sql": """
                select Player_Name,Country_Name,runs as highest_score,balls,
        dots,fours,sixes
        from(select Striker,sum(Runs_Scored) as runs, count(Runs_Scored) as balls,
             sum(case when Runs_Scored==0 then 1 else 0 end) as dots,
             sum(case when Runs_Scored==4 then 1 else 0 end) as fours,
             sum(case when Runs_Scored==6 then 1 else 0 end) as sixes
             from Ball_by_Ball a
             join Batsman_Scored b
             on a.Match_Id=b.Match_Id 
             and a.Innings_No=b.Innings_No
             and a.Over_Id=b.Over_Id 
             and a.Ball_Id=b.Ball_Id
             group by Striker,a.Match_Id) a
        join (select Player_Id,Player_Name,b.Country_Name, c.Batting_hand
             from Player a
             join Country b
             on a.Country_Name=b.Country_Id
             join Batting_Style c
             on a.Batting_hand=c.Batting_Id) b
        on a.Striker=b.Player_Id
        order by highest_score desc; """
    },
     {"query":"Number of fifties and centruies by a batsman in an IPL",
      "tables": ["Ball_by_Ball", "Batsman_Scored", "Player", "Country", "Batting_Style"],
      "sql": """
                select Player_Name,Country_Name,
        sum(case when runs>=50 and runs<100 then 1 else 0 end) as fifties,
        sum(case when runs>=100 then 1 else 0 end) as centuries,
        max(runs) as highest_score
        from(select Striker,sum(Runs_Scored) as runs
             from Ball_by_Ball a
             join Batsman_Scored b
             on a.Match_Id=b.Match_Id 
             and a.Innings_No=b.Innings_No
             and a.Over_Id=b.Over_Id 
             and a.Ball_Id=b.Ball_Id
             group by Striker,a.Match_Id
             having runs>=50) a
        join (select Player_Id,Player_Name,b.Country_Name, c.Batting_hand
             from Player a
             join Country b
             on a.Country_Name=b.Country_Id
             join Batting_Style c
             on a.Batting_hand=c.Batting_Id) b
        on a.Striker=b.Player_Id
        group by Player_Id
        order by fifties+centuries desc; """
    },
     {"query":"Best Teams in IPL",
      "tables": ["Match", "Team", "Season"],
      "sql": """select Team_Name as Team,
        a.matches+b.matches as Matches,c.Wins,
        round(round(Wins,2)/round(a.matches+b.matches,2),2) as Win_perc,
        Defending_perc,Chasing_perc
        from( select Team_1,
              count(*) as matches
              from Match
              group by Team_1) a
        join( select Team_2,
              count(*) as matches
              from Match
              group by Team_2) b
        on a.Team_1=b.Team_2
        join (select Match_Winner,
              count(*) as Wins
              from Match
              where Match_Winner is not null
              group by Match_Winner) c
        on a.Team_1=c.Match_Winner
        join( select 
              case when Toss_Winner=Team_1 and Toss_Decide=2 then Team_1
                   when Toss_Winner=Team_1 and Toss_Decide=1 then Team_2
                   when Toss_Winner=Team_2 and Toss_Decide=2 then Team_2
                   else Team_1 end as franchise,
              round(round(sum(case when Win_Type==1 then 1 else 0 end),2)/round(count(Match_Id),2),2) as Defending_perc
              from Match 
              where Outcome_type=1 
              group by franchise) d
        on a.Team_1=d.franchise
        join( select 
              case when Toss_Winner=Team_1 and Toss_Decide=2 then Team_2
                   when Toss_Winner=Team_1 and Toss_Decide=1 then Team_1
                   when Toss_Winner=Team_2 and Toss_Decide=2 then Team_1
                   else Team_2 end as franchise,
              round(round(sum(case when Win_Type==2 then 1 else 0 end),2)/round(count(Match_Id),2),2) as Chasing_perc
              from Match 
              where Outcome_type=1
              group by franchise) e
        on a.Team_1=e.franchise
        join Team f
        on a.Team_1=f.Team_Id
        order by Win_perc desc,Chasing_perc desc,Defending_perc desc; """

    },
     {"query":"IPL Season's Best PLayers",
      "tables": ["Season", "Player"],
      "sql": """
               select Season_Year,
        b.Player_Name as Man_of_Season,
        c.Player_Name as Top_Scorer,
        d.Player_Name as Top_Wicket_Tacker
        from Season a
        join Player b
        on a.Man_of_the_Series=b.Player_Id
        join Player c
        on a.Orange_Cap=c.Player_Id
        join Player d
        on a.Purple_Cap=d.Player_Id; """
    },

    {"query":" IPL Season's Winners,Runners Up, Win Type",
         "tables": ["Match", "Season", "Team"],
        "sql": """
               select Season_Year,c.Team_Name as Winner,d.Team_Name as Runner_Up
        from( select Season_Id,
              case when Team_1=Match_Winner then Team_1 
              else Team_2 end as first,
              case when Team_1!=Match_Winner then Team_1 
              else Team_2 end as second
              from (select Season_Id,Team_1,Team_2,Match_Winner
                    from Match
                    group by Season_Id
                    having Match_Id=max(Match_Id))) a
        join Season b
        on a.Season_Id=b.Season_Id
        join Team c
        on a.first=c.Team_Id
        join Team d
        on a.second=d.Team_Id;"""
    },
    {"query":"""Given the following input: Chennai Super Kings  vs Mumbai Indians, first determine whether Chennai Super Kings and Mumbai Indians are teams or individual players."
                f" I want complete statistical analysis of Chennai Super Kings and Mumbai Indians for the role of team vs team if both are teams, head to head analysis.""",
      "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Match", "Team"],
      "sql": """
               WITH InningScores AS (
  -- Compute total runs scored by each team in each match
  SELECT
    b.Match_Id,
    b.Team_Batting AS Team_Id,
    SUM(bs.Runs_Scored) + COALESCE(SUM(er.Extra_Runs), 0) AS Total_Runs
  FROM Ball_by_Ball b
  LEFT JOIN Batsman_Scored bs
    ON bs.Match_Id = b.Match_Id
    AND bs.Over_Id = b.Over_Id
    AND bs.Ball_Id = b.Ball_Id
    AND bs.Innings_No = b.Innings_No
  LEFT JOIN Extra_Runs er
    ON er.Match_Id = b.Match_Id
    AND er.Over_Id = b.Over_Id
    AND er.Ball_Id = b.Ball_Id
    AND er.Innings_No = b.Innings_No
  GROUP BY b.Match_Id, b.Team_Batting
)

SELECT
  mi.Team_Name AS Team_A,
  csk.Team_Name AS Team_B,
  COUNT(*) AS Matches_Played,
  -- Head-to-head wins
  SUM(CASE WHEN m.Match_Winner = mi.Team_Id THEN 1 ELSE 0 END) AS Team_A_Wins,
  SUM(CASE WHEN m.Match_Winner = csk.Team_Id THEN 1 ELSE 0 END) AS Team_B_Wins,
  -- Head-to-head average scores
  ROUND(AVG(s_a.Total_Runs), 1) AS Team_A_Avg_Score,
  ROUND(AVG(s_b.Total_Runs), 1) AS Team_B_Avg_Score
FROM Match m
  -- Load the two teams once each by name
  JOIN Team mi ON mi.Team_Name = 'Mumbai Indians'
  JOIN Team csk ON csk.Team_Name = 'Chennai Super Kings'

  -- Link in the per-match totals
  LEFT JOIN InningScores s_a
    ON s_a.Match_Id = m.Match_Id
    AND s_a.Team_Id = mi.Team_Id
  LEFT JOIN InningScores s_b
    ON s_b.Match_Id = m.Match_Id
    AND s_b.Team_Id = csk.Team_Id

WHERE 
  -- Only matches between the two teams, in either order
  (m.Team_1 = mi.Team_Id AND m.Team_2 = csk.Team_Id)
  OR
  (m.Team_1 = csk.Team_Id AND m.Team_2 = mi.Team_Id)
"""
    },
    {"query":""" Given the following input: Royal Challengers Banglore  vs Kolkata Knight Riders , first determine whether Royal Challengers Banglore  and Kolkata Knight Riders are teams or individual players."
                f" I want complete statistical analysis of Royal Challengers Banglore  and Kolkata Knight Riders  for the role of team vs team if both are teams, head to head analysis.""",
      "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Match", "Team"],
      "sql": """
               WITH InningScores AS (
  -- Compute total runs scored by each team in each match
  SELECT
    b.Match_Id,
    b.Team_Batting AS Team_Id,
    SUM(bs.Runs_Scored) + COALESCE(SUM(er.Extra_Runs), 0) AS Total_Runs
  FROM Ball_by_Ball b
  LEFT JOIN Batsman_Scored bs
    ON bs.Match_Id = b.Match_Id
    AND bs.Over_Id = b.Over_Id
    AND bs.Ball_Id = b.Ball_Id
    AND bs.Innings_No = b.Innings_No
  LEFT JOIN Extra_Runs er
    ON er.Match_Id = b.Match_Id
    AND er.Over_Id = b.Over_Id
    AND er.Ball_Id = b.Ball_Id
    AND er.Innings_No = b.Innings_No
  GROUP BY b.Match_Id, b.Team_Batting
)

SELECT
  mi.Team_Name AS Team_A,
  csk.Team_Name AS Team_B,
  COUNT(*) AS Matches_Played,
  -- Head-to-head wins
  SUM(CASE WHEN m.Match_Winner = mi.Team_Id THEN 1 ELSE 0 END) AS Team_A_Wins,
  SUM(CASE WHEN m.Match_Winner = csk.Team_Id THEN 1 ELSE 0 END) AS Team_B_Wins,
  -- Head-to-head average scores
  ROUND(AVG(s_a.Total_Runs), 1) AS Team_A_Avg_Score,
  ROUND(AVG(s_b.Total_Runs), 1) AS Team_B_Avg_Score
FROM Match m
  -- Load the two teams once each by name
  JOIN Team mi ON mi.Team_Name = 'Kolkata Knight Riders'
  JOIN Team csk ON csk.Team_Name = 'Royal Challengers Bangalore'

  -- Link in the per-match totals
  LEFT JOIN InningScores s_a
    ON s_a.Match_Id = m.Match_Id
    AND s_a.Team_Id = mi.Team_Id
  LEFT JOIN InningScores s_b
    ON s_b.Match_Id = m.Match_Id
    AND s_b.Team_Id = csk.Team_Id

WHERE 
  -- Only matches between the two teams, in either order
  (m.Team_1 = mi.Team_Id AND m.Team_2 = csk.Team_Id)
  OR
  (m.Team_1 = csk.Team_Id AND m.Team_2 = mi.Team_Id)
"""
    },
    {"query":""" Given the following input: Kings XI Punjab  vs Rajasthan Royals, first determine whether Kings XI Punjab and Rajasthan Royals are teams or individual players."
                f" I want complete statistical analysis of Kings XI Punjab and Rajasthan Royals  for the role of team vs team if both are teams, head to head analysis.""",
      "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Match", "Team"],
      "sql": """
               WITH InningScores AS (
  -- Compute total runs scored by each team in each match
  SELECT
    b.Match_Id,
    b.Team_Batting AS Team_Id,
    SUM(bs.Runs_Scored) + COALESCE(SUM(er.Extra_Runs), 0) AS Total_Runs
  FROM Ball_by_Ball b
  LEFT JOIN Batsman_Scored bs
    ON bs.Match_Id = b.Match_Id
    AND bs.Over_Id = b.Over_Id
    AND bs.Ball_Id = b.Ball_Id
    AND bs.Innings_No = b.Innings_No
  LEFT JOIN Extra_Runs er
    ON er.Match_Id = b.Match_Id
    AND er.Over_Id = b.Over_Id
    AND er.Ball_Id = b.Ball_Id
    AND er.Innings_No = b.Innings_No
  GROUP BY b.Match_Id, b.Team_Batting
)

SELECT
  mi.Team_Name AS Team_A,
  csk.Team_Name AS Team_B,
  COUNT(*) AS Matches_Played,
  -- Head-to-head wins
  SUM(CASE WHEN m.Match_Winner = mi.Team_Id THEN 1 ELSE 0 END) AS Team_A_Wins,
  SUM(CASE WHEN m.Match_Winner = csk.Team_Id THEN 1 ELSE 0 END) AS Team_B_Wins,
  -- Head-to-head average scores
  ROUND(AVG(s_a.Total_Runs), 1) AS Team_A_Avg_Score,
  ROUND(AVG(s_b.Total_Runs), 1) AS Team_B_Avg_Score
FROM Match m
  -- Load the two teams once each by name
  JOIN Team mi ON mi.Team_Name = 'Kings XI Punjab'
  JOIN Team csk ON csk.Team_Name = 'Rajasthan Royals'

  -- Link in the per-match totals
  LEFT JOIN InningScores s_a
    ON s_a.Match_Id = m.Match_Id
    AND s_a.Team_Id = mi.Team_Id
  LEFT JOIN InningScores s_b
    ON s_b.Match_Id = m.Match_Id
    AND s_b.Team_Id = csk.Team_Id

WHERE 
  -- Only matches between the two teams, in either order
  (m.Team_1 = mi.Team_Id AND m.Team_2 = csk.Team_Id)
  OR
  (m.Team_1 = csk.Team_Id AND m.Team_2 = mi.Team_Id)
"""
    },
       {"query":"Given the following input: Delhi Daredevils  vs Sunrisers Hyderabad, first determine whether Delhi Daredevils and Sunrisers Hyderabad are teams or individual players."
                f" I want complete statistical analysis of Delhi Daredevils and Sunrisers Hyderabad for the role of team vs team if both are teams, head to head analysis.""",
      "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Match", "Team"],
      "sql": """
               WITH InningScores AS (
  -- Compute total runs scored by each team in each match
  SELECT
    b.Match_Id,
    b.Team_Batting AS Team_Id,
    SUM(bs.Runs_Scored) + COALESCE(SUM(er.Extra_Runs), 0) AS Total_Runs
  FROM Ball_by_Ball b
  LEFT JOIN Batsman_Scored bs
    ON bs.Match_Id = b.Match_Id
    AND bs.Over_Id = b.Over_Id
    AND bs.Ball_Id = b.Ball_Id
    AND bs.Innings_No = b.Innings_No
  LEFT JOIN Extra_Runs er
    ON er.Match_Id = b.Match_Id
    AND er.Over_Id = b.Over_Id
    AND er.Ball_Id = b.Ball_Id
    AND er.Innings_No = b.Innings_No
  GROUP BY b.Match_Id, b.Team_Batting
)

SELECT
  mi.Team_Name AS Team_A,
  csk.Team_Name AS Team_B,
  COUNT(*) AS Matches_Played,
  -- Head-to-head wins
  SUM(CASE WHEN m.Match_Winner = mi.Team_Id THEN 1 ELSE 0 END) AS Team_A_Wins,
  SUM(CASE WHEN m.Match_Winner = csk.Team_Id THEN 1 ELSE 0 END) AS Team_B_Wins,
  -- Head-to-head average scores
  ROUND(AVG(s_a.Total_Runs), 1) AS Team_A_Avg_Score,
  ROUND(AVG(s_b.Total_Runs), 1) AS Team_B_Avg_Score
FROM Match m
  -- Load the two teams once each by name
  JOIN Team mi ON mi.Team_Name = 'Delhi Daredevils'
  JOIN Team csk ON csk.Team_Name = 'Sunrisers Hyderabad'

  -- Link in the per-match totals
  LEFT JOIN InningScores s_a
    ON s_a.Match_Id = m.Match_Id
    AND s_a.Team_Id = mi.Team_Id
  LEFT JOIN InningScores s_b
    ON s_b.Match_Id = m.Match_Id
    AND s_b.Team_Id = csk.Team_Id

WHERE 
  -- Only matches between the two teams, in either order
  (m.Team_1 = mi.Team_Id AND m.Team_2 = csk.Team_Id)
  OR
  (m.Team_1 = csk.Team_Id AND m.Team_2 = mi.Team_Id)
"""
    },
       {"query":" Given the following input: Gujarat Lions  vs Rising Pune Supergiants, first determine whether Gujarat Lions and Rising Pune Supergiants are teams or individual players."
                f" I want complete statistical analysis of Gujarat Lions and Rising Pune Supergiants for the role of team vs team if both are teams, head to head analysis.""",
      "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Match", "Team"],
      "sql": """
               WITH InningScores AS (
  -- Compute total runs scored by each team in each match
  SELECT
    b.Match_Id,
    b.Team_Batting AS Team_Id,
    SUM(bs.Runs_Scored) + COALESCE(SUM(er.Extra_Runs), 0) AS Total_Runs
  FROM Ball_by_Ball b
  LEFT JOIN Batsman_Scored bs
    ON bs.Match_Id = b.Match_Id
    AND bs.Over_Id = b.Over_Id
    AND bs.Ball_Id = b.Ball_Id
    AND bs.Innings_No = b.Innings_No
  LEFT JOIN Extra_Runs er
    ON er.Match_Id = b.Match_Id
    AND er.Over_Id = b.Over_Id
    AND er.Ball_Id = b.Ball_Id
    AND er.Innings_No = b.Innings_No
  GROUP BY b.Match_Id, b.Team_Batting
)

SELECT
  mi.Team_Name AS Team_A,
  csk.Team_Name AS Team_B,
  COUNT(*) AS Matches_Played,
  -- Head-to-head wins
  SUM(CASE WHEN m.Match_Winner = mi.Team_Id THEN 1 ELSE 0 END) AS Team_A_Wins,
  SUM(CASE WHEN m.Match_Winner = csk.Team_Id THEN 1 ELSE 0 END) AS Team_B_Wins,
  -- Head-to-head average scores
  ROUND(AVG(s_a.Total_Runs), 1) AS Team_A_Avg_Score,
  ROUND(AVG(s_b.Total_Runs), 1) AS Team_B_Avg_Score
FROM Match m
  -- Load the two teams once each by name
  JOIN Team mi ON mi.Team_Name = 'Gujarat Lions'
  JOIN Team csk ON csk.Team_Name = 'Rising Pune Supergiants'

  -- Link in the per-match totals
  LEFT JOIN InningScores s_a
    ON s_a.Match_Id = m.Match_Id
    AND s_a.Team_Id = mi.Team_Id
  LEFT JOIN InningScores s_b
    ON s_b.Match_Id = m.Match_Id
    AND s_b.Team_Id = csk.Team_Id

WHERE 
  -- Only matches between the two teams, in either order
  (m.Team_1 = mi.Team_Id AND m.Team_2 = csk.Team_Id)
  OR
  (m.Team_1 = csk.Team_Id AND m.Team_2 = mi.Team_Id)
"""
},
{"query":"Given the following input: Sourav Ganguly vs Brett Lee, first determine whether Sourav Ganguly are Brett Lee teams or individual players."
                f" I want complete statistical analysis of Sourav Ganguly and Brett Lee for the role of batsman vs bowler if both are players",
      "tables": ["Ball_by_Ball", "Player", "Batsman_Scored", "Wicket_Taken"],
      "sql": """
              SELECT
    batsman.Player_Name AS Batsman,
    bowler.Player_Name AS Bowler,
    COUNT(*) AS Balls_Faced,
    COALESCE(SUM(bs.Runs_Scored), 0) AS Runs_Scored,
    COUNT(DISTINCT wt.Match_Id || '-' || wt.Over_Id || '-' || wt.Ball_Id) AS Times_Out
FROM Ball_by_Ball b
JOIN Player batsman ON b.Striker = batsman.Player_Id
JOIN Player bowler ON b.Bowler = bowler.Player_Id
LEFT JOIN Batsman_Scored bs ON 
    bs.Match_Id = b.Match_Id AND 
    bs.Over_Id = b.Over_Id AND 
    bs.Ball_Id = b.Ball_Id AND
    bs.Innings_No = b.Innings_No
LEFT JOIN Wicket_Taken wt ON 
    wt.Match_Id = b.Match_Id AND 
    wt.Over_Id = b.Over_Id AND 
    wt.Ball_Id = b.Ball_Id AND
    wt.Player_Out = b.Striker AND 
    wt.Kind_Out != 'run out'
WHERE
    batsman.Player_Name = 'Sourav Ganguly' AND
    bowler.Player_Name = 'Brett Lee'
GROUP BY batsman.Player_Name, bowler.Player_Name;"""

   },
{"query":"Given the following input: Rahul Dravid vs Mark Boucher, first determine whether Rahul Dravid are Mark Boucher teams or individual players."
               """ f" I want complete statistical analysis of Rahul Dravid and Mark Boucher for the role of batsman vs bowler if both are players""",
      "tables": ["Ball_by_Ball", "Player", "Batsman_Scored", "Wicket_Taken"],
      "sql": """
              SELECT
    batsman.Player_Name AS Batsman,
    bowler.Player_Name AS Bowler,
    COUNT(*) AS Balls_Faced,
    COALESCE(SUM(bs.Runs_Scored), 0) AS Runs_Scored,
    COUNT(DISTINCT wt.Match_Id || '-' || wt.Over_Id || '-' || wt.Ball_Id) AS Times_Out
FROM Ball_by_Ball b
JOIN Player batsman ON b.Striker = batsman.Player_Id
JOIN Player bowler ON b.Bowler = bowler.Player_Id
LEFT JOIN Batsman_Scored bs ON 
    bs.Match_Id = b.Match_Id AND 
    bs.Over_Id = b.Over_Id AND 
    bs.Ball_Id = b.Ball_Id AND
    bs.Innings_No = b.Innings_No
LEFT JOIN Wicket_Taken wt ON 
    wt.Match_Id = b.Match_Id AND 
    wt.Over_Id = b.Over_Id AND 
    wt.Ball_Id = b.Ball_Id AND
    wt.Player_Out = b.Striker AND 
    wt.Kind_Out != 'run out'
WHERE
    batsman.Player_Name = 'Rahul Dravid' AND
    bowler.Player_Name = 'Mark Boucher'
GROUP BY batsman.Player_Name, bowler.Player_Name;"""

    },

{"query":"Given the following input: Sachin Tendulkar vs Sunil Narine, first determine whether Sachin Tendulkar are Sunil Narine teams or individual players."
                f" I want complete statistical analysis of Sachin Tendulkar and Sunil Narine for the role of batsman vs bowler if both are players""",
      "tables": ["Ball_by_Ball", "Player", "Batsman_Scored", "Wicket_Taken"],
      "sql": """
                    SELECT
    batsman.Player_Name AS Batsman,
    bowler.Player_Name AS Bowler,
    COUNT(*) AS Balls_Faced,
    COALESCE(SUM(bs.Runs_Scored), 0) AS Runs_Scored,
    COUNT(DISTINCT wt.Match_Id || '-' || wt.Over_Id || '-' || wt.Ball_Id) AS Times_Out
FROM Ball_by_Ball b
JOIN Player batsman ON b.Striker = batsman.Player_Id
JOIN Player bowler ON b.Bowler = bowler.Player_Id
LEFT JOIN Batsman_Scored bs ON 
    bs.Match_Id = b.Match_Id AND 
    bs.Over_Id = b.Over_Id AND 
    bs.Ball_Id = b.Ball_Id AND
    bs.Innings_No = b.Innings_No
LEFT JOIN Wicket_Taken wt ON 
    wt.Match_Id = b.Match_Id AND 
    wt.Over_Id = b.Over_Id AND 
    wt.Ball_Id = b.Ball_Id AND
    wt.Player_Out = b.Striker AND 
    wt.Kind_Out != 'run out'
WHERE
    batsman.Player_Name = 'Sachin Tendulkar' AND
    bowler.Player_Name = 'Sunil Narine'
GROUP BY batsman.Player_Name, bowler.Player_Name;"""

    },
{"query":"Given the following input: Virat Kohli vs Jasprit Bumrah, first determine whether Virat Kohli are Jasprit Bumrah teams or individual players."
                f" I want complete statistical analysis of Virat Kohli and Jasprit Bumrah for the role of batsman vs bowler if both are players""",
      "tables": ["Ball_by_Ball", "Player", "Batsman_Scored", "Wicket_Taken"],
      "sql": """
              SELECT
    batsman.Player_Name AS Batsman,
    bowler.Player_Name AS Bowler,
    COUNT(*) AS Balls_Faced,
    COALESCE(SUM(bs.Runs_Scored), 0) AS Runs_Scored,
    COUNT(DISTINCT wt.Match_Id || '-' || wt.Over_Id || '-' || wt.Ball_Id) AS Times_Out
FROM Ball_by_Ball b
JOIN Player batsman ON b.Striker = batsman.Player_Id
JOIN Player bowler ON b.Bowler = bowler.Player_Id
LEFT JOIN Batsman_Scored bs ON 
    bs.Match_Id = b.Match_Id AND 
    bs.Over_Id = b.Over_Id AND 
    bs.Ball_Id = b.Ball_Id AND
    bs.Innings_No = b.Innings_No
LEFT JOIN Wicket_Taken wt ON 
    wt.Match_Id = b.Match_Id AND 
    wt.Over_Id = b.Over_Id AND 
    wt.Ball_Id = b.Ball_Id AND
    wt.Player_Out = b.Striker AND 
    wt.Kind_Out != 'run out'
WHERE
    batsman.Player_Name = 'Virat Kohli' AND
    bowler.Player_Name = 'Jasprit Bumrah'
GROUP BY batsman.Player_Name, bowler.Player_Name;"""

    },
{"query":"Given the following input: Rohit Sharma vs Morne Morkel, first determine whether Rohit Sharma are Morne Morkelteams or individual players."
                f" I want complete statistical analysis of Rohit Sharma and Morne Morkel for the role of batsman vs bowler if both are players""",
      "tables": ["Ball_by_Ball", "Player", "Batsman_Scored", "Wicket_Taken"],
      "sql": """
                           SELECT
    batsman.Player_Name AS Batsman,
    bowler.Player_Name AS Bowler,
    COUNT(*) AS Balls_Faced,
    COALESCE(SUM(bs.Runs_Scored), 0) AS Runs_Scored,
    COUNT(DISTINCT wt.Match_Id || '-' || wt.Over_Id || '-' || wt.Ball_Id) AS Times_Out
FROM Ball_by_Ball b
JOIN Player batsman ON b.Striker = batsman.Player_Id
JOIN Player bowler ON b.Bowler = bowler.Player_Id
LEFT JOIN Batsman_Scored bs ON 
    bs.Match_Id = b.Match_Id AND 
    bs.Over_Id = b.Over_Id AND 
    bs.Ball_Id = b.Ball_Id AND
    bs.Innings_No = b.Innings_No
LEFT JOIN Wicket_Taken wt ON 
    wt.Match_Id = b.Match_Id AND 
    wt.Over_Id = b.Over_Id AND 
    wt.Ball_Id = b.Ball_Id AND
    wt.Player_Out = b.Striker AND 
    wt.Kind_Out != 'run out'
WHERE
    batsman.Player_Name = 'Rohit Sharma' AND
    bowler.Player_Name = 'Morne Morkel'
GROUP BY batsman.Player_Name, bowler.Player_Name;"""

    },
{"query":"Given the following input:Jacques Kallis vs Ravichandran Ashwin, first determine whether Jacques Kallis are Ravichandran Ashwin teams or individual players."
                f" I want complete statistical analysis ofJacques Kallis and Ravichandran Ashwin for the role of batsman vs bowler if both are players""",
      "tables": ["Ball_by_Ball", "Player", "Batsman_Scored", "Wicket_Taken"],
      "sql": """
          
              SELECT
    batsman.Player_Name AS Batsman,
    bowler.Player_Name AS Bowler,
    COUNT(*) AS Balls_Faced,
    COALESCE(SUM(bs.Runs_Scored), 0) AS Runs_Scored,
    COUNT(DISTINCT wt.Match_Id || '-' || wt.Over_Id || '-' || wt.Ball_Id) AS Times_Out
FROM Ball_by_Ball b
JOIN Player batsman ON b.Striker = batsman.Player_Id
JOIN Player bowler ON b.Bowler = bowler.Player_Id
LEFT JOIN Batsman_Scored bs ON 
    bs.Match_Id = b.Match_Id AND 
    bs.Over_Id = b.Over_Id AND 
    bs.Ball_Id = b.Ball_Id AND
    bs.Innings_No = b.Innings_No
LEFT JOIN Wicket_Taken wt ON 
    wt.Match_Id = b.Match_Id AND 
    wt.Over_Id = b.Over_Id AND 
    wt.Ball_Id = b.Ball_Id AND
    wt.Player_Out = b.Striker AND 
    wt.Kind_Out != 'run out'
WHERE
    batsman.Player_Name = 'Jacques Kallis' AND
    bowler.Player_Name = 'Ravichandran Ashwin'
GROUP BY batsman.Player_Name, bowler.Player_Name;"""

    }
]


class TextToSQLAgent:
    def __init__(
        self,
        api_key: str = "AIzaSyCGZvV_wKpFeW2KFFnvSTi4-5HuZVeea50",
        embedding_model: str = "models/text-embedding-004",
        rag_k: int = 5
    ):
        # Load API key
        self.api_key = "AIzaSyCGZvV_wKpFeW2KFFnvSTi4-5HuZVeea50"
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not set for TextToSQLAgent")

        # LLM for SQL generation
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=self.api_key
        )

        # Build the RAG vector store over your examples
        docs = [
            Document(page_content=f"Q: {ex['query']}\nSQL: {ex['sql']}")
            for ex in examples_of_tables_sql
        ]
        embeddings = GoogleGenerativeAIEmbeddings(
            model=embedding_model,
            google_api_key=self.api_key
        )
        self.vector_store = Chroma.from_documents(documents=docs, embedding=embeddings)
        self.rag_k = rag_k

        # Base template (without examples) — will be extended dynamically
        self.base_messages = [
    ("system", 
     """You are an expert SQL developer. Your role is to translate natural language questions into precise, executable SQL queries using the provided database schema.

Database Schema:
{schema_info}

Guidelines:
- Use only the columns and tables specified in the schema.
- Output only the SQL query-do not include explanations, comments, or markdown formatting.
- Assume all queries are to be run on the 'wicketwise.db' database.
- Check for batsman, bowler, allrounder(batsman + bowler) and wicketkeeper tag in user query and
    thereby retrieve the relevant query examples from the vector database.
"""),
    ("user", 
     "Please generate the SQL query for the following request:\n{natural_language_request}\n\nSQL Query:")
]


    def _strip_markdown(self, text: str) -> str:
        text = re.sub(r"```(?:sql)?", "", text, flags=re.IGNORECASE)
        return text.strip("`\n ")

    def generate_sql(self, user_query: str, schema_info: str) -> str:
        """
        1. Retrieve similar examples for user_query.
        2. Build a prompt that includes those examples + the schema + the user request.
        3. Invoke the LLM to generate SQL.
        """
        # 1) Retrieve top-k examples
        print("entered into the generate_sql function")
        retriever = self.vector_store.as_retriever(k=3)
        similar_docs = retriever.get_relevant_documents(user_query)
        examples_text = "\n\n".join(doc.page_content for doc in similar_docs)
        print(f"retrival done")
        print(examples_text)
        # 2) Build dynamic messages: first show examples as context
        dynamic_messages = [
    ("system", f"""Here are some examples of past requests and their correct SQL:\n\n{examples_text}

You are an expert SQL developer. Your role is to translate natural language questions into precise, executable SQL queries using the provided database schema.

Database Schema:
{schema_info}

Guidelines:
- Use only the columns and tables specified in the schema.
- Output only the SQL query—do not include explanations, comments, or markdown formatting.
- Assume all queries are to be run on the 'wicketwise.db' database.
- Check for batsman, bowler, allrounder (batsman + bowler), and wicketkeeper tag in user query and thereby retrieve the relevant query examples from the vector database.
"""),
    ("user", 
     "Please generate the SQL query for the following request:\n{natural_language_request}\n\nSQL Query:")
]



        # 3) Instantiate a prompt + chain
        prompt = ChatPromptTemplate.from_messages(dynamic_messages)

        chain = prompt | self.llm | StrOutputParser()
        print(f"prompt created")

        # 4) Call the chain
        try:
          raw_sql = chain.invoke({
          "schema_info": schema_info,
          "natural_language_request": user_query
       })
        except Exception as e:
          print("ERROR DURING CHAIN INVOCATION:", e)
          raise

        # 5) Strip any markdown fences
        cleaned = self._strip_markdown(raw_sql)
        print(f"Generated SQL:\n{cleaned}")
        return cleaned
