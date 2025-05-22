from langchain.utilities import SQLDatabase
from langchain.llms import OpenAI
from langchain.agents import create_sql_agent
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from langchain.agents.agent_types import AgentType
import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate,PromptTemplate
from langchain.schema import Document
from langchain.llms import OpenAI
from langchain.chains import LLMChain
from langchain.agents import create_sql_agent, AgentType
from langchain.vectorstores import Chroma



api_key = 'AIzaSyCGZvV_wKpFeW2KFFnvSTi4-5HuZVeea50'
if not api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set. Please set it in your .env file or environment.")

llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=api_key)

examples = [
    {
      "query": "#Bowlers who have bowled most deliveries",
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
    {
        "query": "Highest Wicket takers in IPL (Runout, Retired hurt and Obstructing field are not counted as bowlers wicket)",
        "sql": """ select Player_Name,count(Kind_Out) as Wickets,
        sum(case when Kind_Out==1 then 1 else 0 end) as caught,
        sum(case when Kind_Out==2 then 1 else 0 end) as bowled,
        sum(case when Kind_Out==4 then 1 else 0 end) as lbw,
        sum(case when Kind_Out==6 then 1 else 0 end) as stumped
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
        group by c.Player_Id
        order by Wickets desc; """
    },
    {
      "query": "Highest wicket taken by a bowler in an IPL match",
      "sql": """select Player_Name,Country_Name,Bowling_skill,
        Wickets||"-"||runs as Best
        from( select a.Bowler,a.Match_Id,count(Kind_Out) as Wickets
              from Ball_by_Ball a
              join Wicket_Taken b
              on a.Match_Id=b.Match_Id 
              and a.Innings_No=b.Innings_No
              and a.Over_Id=b.Over_Id 
              and a.Ball_Id=b.Ball_Id
              where Kind_Out in (1,2,4,6,7,8)
              group by a.Bowler,a.Match_Id) a
        join( select a.Bowler,a.Match_Id,
              sum(coalesce(Runs_Scored,0)+coalesce(Extra_Runs,0)) as runs
              from Ball_by_Ball a
              left join Batsman_Scored b 
              on a.Match_Id=b.Match_Id 
              and a.Innings_No=b.Innings_No
              and a.Over_Id=b.Over_Id 
              and a.Ball_Id=b.Ball_Id
              left join Extra_Runs c
              on a.Match_Id=c.Match_Id 
              and a.Innings_No=c.Innings_No
              and a.Over_Id=c.Over_Id 
              and a.Ball_Id=c.Ball_Id
              group by a.Bowler,a.Match_Id) b
              on a.Bowler=b.Bowler
              and a.Match_Id=b.Match_Id
        join( select Player_Id,Player_Name,b.Country_Name, c.Bowling_skill
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Bowling_Style c
              on a.Bowling_skill=c.Bowling_Id) c
        on a.Bowler=c.Player_Id
        order by Wickets desc; """
    },
    {
      "query": "No of 5-wicket hauls by bowlers in an IPL ",
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
    {
      "query": "Most Runs Conceded by a Bowler in an IPL Match",
      "sql": """ select Player_Name,Country_Name,Bowling_skill,runs
        from( select a.Bowler,
              sum(coalesce(Runs_Scored,0)+coalesce(Extra_Runs,0)) as runs
              from Ball_by_Ball a
              left join Batsman_Scored b 
              on a.Match_Id=b.Match_Id 
              and a.Innings_No=b.Innings_No
              and a.Over_Id=b.Over_Id 
              and a.Ball_Id=b.Ball_Id
              left join Extra_Runs c
              on a.Match_Id=c.Match_Id 
              and a.Innings_No=c.Innings_No
              and a.Over_Id=c.Over_Id 
              and a.Ball_Id=c.Ball_Id
              group by a.Bowler,a.Match_Id) a
        join( select Player_Id,Player_Name,b.Country_Name, c.Bowling_skill
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Bowling_Style c
              on a.Bowling_skill=c.Bowling_Id) b
        on a.Bowler=b.Player_Id
        order by runs desc; """
    },
    {
      "query": "Highest Runs Concede in an IPL over by a bowler",
      "sql": """select Player_Name as Bowler,
        max(runs+extra) as Runs,Fours,Sixes,
        Extra,wides,noballs,legbyes
        from(select Match_Id,Innings_No,Over_Id,sum(Runs_Scored) as runs,
             sum(case when Runs_Scored==4 then 1 else 0 end) as Fours,
             sum(case when Runs_Scored==6 then 1 else 0 end) as Sixes
             from Batsman_Scored
             group by Match_Id, Innings_No,Over_Id) a
        join(select Match_Id,Innings_No,Over_Id,sum(Extra_Runs) as Extra,
             sum(case when Extra_Type_Id==1 then 1 else 0 end) as legbyes,
             sum(case when Extra_Type_Id==2 then 1 else 0 end) as wides,
             sum(case when Extra_Type_Id==4 then 1 else 0 end) as noballs
             from Extra_Runs
             group by Match_Id,Innings_No,Over_Id) b
        on a.Match_Id=b.Match_Id 
        and a.Innings_No=b.Innings_No
        and a.Over_Id=b.Over_Id
        join (select Match_Id,Innings_No,Over_Id,Player_Name,
              c.Bowling_skill,d.Country_Name
              from Ball_by_Ball a
              join Player b
              on a.Bowler=b.Player_Id
              join Bowling_Style c
              on b.Bowling_skill=c.Bowling_Id
              join Country d
              on b.Country_Name=d.Country_Id
              group by Match_Id,Innings_No,Over_id) c
         on a.Match_Id=c.Match_Id 
         and a.Innings_No=c.Innings_No
         and a.Over_Id=c.Over_Id
         group by a.Match_Id,a.Innings_No,a.Over_Id
         order by Runs desc; """
    },
    {
      "query": " best economy bowler's in IPL",
      "sql": """select Player_Name,Country_Name,
        overs,runs,extras,economy
        from(select Bowler,sum(coalesce(Extra_Runs,0)+Runs_Scored) as runs,
             sum(coalesce(Extra_Runs,0)) as extras,
             count(*)/6 as overs,
             round(round(sum(coalesce(Extra_Runs,0)+Runs_Scored),2)/round(count(*)/6,2),2) as economy
             from Batsman_Scored a
             join Ball_by_Ball b
             on a.Match_Id=b.Match_Id
             and a.Innings_No=b.Innings_No
             and a.Over_Id=b.Over_Id
             and a.Ball_Id=b.Ball_Id
             left join Extra_Runs c
             on a.Match_Id=c.Match_Id
             and a.Innings_No=c.Innings_No
             and a.Over_Id=c.Over_Id
             and a.Ball_Id=c.Ball_Id
             group by Bowler
             having overs>=50) a
        join (select Player_Id,Player_Name,b.Bowling_skill,c.Country_Name
              from Player a
              join Bowling_Style b
              on a.Bowling_skill=b.Bowling_Id
              join Country c
              on a.Country_Name=c.Country_Id) b
        on a.Bowler=b.Player_Id 
        order by economy asc; """
    },
    {
      "query": "Best Death overs Bowler's in Indian Premier League (Wickets_rate= average no of wickets ball in an over)",
      "sql": """"select Player_Name,Country_Name,
       Overs,Runs,Wickets,Economy,
       round(round(Wickets,2)/round(Overs,2),2) as Wicket_rate
       from( select Bowler,count(*) as Overs,sum(runs) as Runs,
             round(round(sum(runs),2)/round(count(*),2),2) as Economy
             from (select a.Bowler,a.Match_Id,
                   sum(coalesce(Runs_Scored,0)+coalesce(Extra_Runs,0)) as runs
                   from Ball_by_Ball a
                   left join Batsman_Scored b 
                   on a.Match_Id=b.Match_Id 
                   and a.Innings_No=b.Innings_No
                   and a.Over_Id=b.Over_Id 
                   and a.Ball_Id=b.Ball_Id
                   left join Extra_Runs c
                   on a.Match_Id=c.Match_Id 
                   and a.Innings_No=c.Innings_No
                   and a.Over_Id=c.Over_Id 
                   and a.Ball_Id=c.Ball_Id
                   where a.Over_Id in (16,17,18,19,20)
                   group by a.Bowler,a.Match_Id,a.Over_Id)
              group by Bowler) a 
        join( select Bowler,sum(Kind_Out) as Wickets
              from Ball_by_Ball a
              join Wicket_Taken b
              on a.Match_Id=b.Match_Id 
              and a.Innings_No=b.Innings_No
              and a.Over_Id=b.Over_Id 
              and a.Ball_Id=b.Ball_Id
              where a.Over_Id in (16,17,18,19,20) and
              Kind_Out in (1,2,4,6,7,8)
              group by a.Bowler) b
        on a.Bowler=b.Bowler
        join( select Player_Id,Player_Name,b.Country_Name, c.Bowling_skill
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Bowling_Style c
              on a.Bowling_skill=c.Bowling_Id) c
      on a.Bowler=c.Player_Id
      where Overs>=50
      order by Economy,Wicket_rate desc; """
    },
    {
      "query": "Best powerplay overs Bowler's in Indian Premier League(Wickets_rate= average no of wickets ball in an over)",
      "sql": """select Player_Name,Country_Name,
       Overs,Runs,Wickets,Economy,
       round(round(Wickets,2)/round(Overs,2),2) as Wicket_rate
       from( select Bowler,count(*) as Overs,sum(runs) as Runs,
             round(round(sum(runs),2)/round(count(*),2),2) as Economy
             from (select a.Bowler,a.Match_Id,
                   sum(coalesce(Runs_Scored,0)+coalesce(Extra_Runs,0)) as runs
                   from Ball_by_Ball a
                   left join Batsman_Scored b 
                   on a.Match_Id=b.Match_Id 
                   and a.Innings_No=b.Innings_No
                   and a.Over_Id=b.Over_Id 
                   and a.Ball_Id=b.Ball_Id
                   left join Extra_Runs c
                   on a.Match_Id=c.Match_Id 
                   and a.Innings_No=c.Innings_No
                   and a.Over_Id=c.Over_Id 
                   and a.Ball_Id=c.Ball_Id
                   where a.Over_Id in (1,2,3,4,5,6)
                   group by a.Bowler,a.Match_Id,a.Over_Id)
              group by Bowler) a 
        join( select Bowler,sum(Kind_Out) as Wickets
              from Ball_by_Ball a
              join Wicket_Taken b
              on a.Match_Id=b.Match_Id 
              and a.Innings_No=b.Innings_No
              and a.Over_Id=b.Over_Id 
              and a.Ball_Id=b.Ball_Id
              where a.Over_Id in (1,2,3,4,5,6) and
              Kind_Out in (1,2,4,6,7,8)
              group by a.Bowler) b
        on a.Bowler=b.Bowler
        join( select Player_Id,Player_Name,b.Country_Name, c.Bowling_skill
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Bowling_Style c
              on a.Bowling_skill=c.Bowling_Id) c
      on a.Bowler=c.Player_Id
      where Overs>=50
      order by Economy,Wicket_rate desc; """
    },
    {
      "query": "#Best Middle overs Bowler's in Indian Premier League(Wickets_rate= average no of wickets ball in an over)",
      "sql": """select Player_Name,Country_Name,
       Overs,Runs,Wickets,Economy,
       round(round(Wickets,2)/round(Overs,2),2) as Wicket_rate
       from( select Bowler,count(*) as Overs,sum(runs) as Runs,
             round(round(sum(runs),2)/round(count(*),2),2) as Economy
             from (select a.Bowler,a.Match_Id,
                   sum(coalesce(Runs_Scored,0)+coalesce(Extra_Runs,0)) as runs
                   from Ball_by_Ball a
                   left join Batsman_Scored b 
                   on a.Match_Id=b.Match_Id 
                   and a.Innings_No=b.Innings_No
                   and a.Over_Id=b.Over_Id 
                   and a.Ball_Id=b.Ball_Id
                   left join Extra_Runs c
                   on a.Match_Id=c.Match_Id 
                   and a.Innings_No=c.Innings_No
                   and a.Over_Id=c.Over_Id 
                   and a.Ball_Id=c.Ball_Id
                   where a.Over_Id in (7,8,9,10,11,12,13,14,15)
                   group by a.Bowler,a.Match_Id,a.Over_Id)
              group by Bowler) a 
        join( select Bowler,sum(Kind_Out) as Wickets
              from Ball_by_Ball a
              join Wicket_Taken b
              on a.Match_Id=b.Match_Id 
              and a.Innings_No=b.Innings_No
              and a.Over_Id=b.Over_Id 
              and a.Ball_Id=b.Ball_Id
              where a.Over_Id in (1,2,3,4,5,6) and
              Kind_Out in (1,2,4,6,7,8)
              group by a.Bowler) b
        on a.Bowler=b.Bowler
        join( select Player_Id,Player_Name,b.Country_Name, c.Bowling_skill
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Bowling_Style c
              on a.Bowling_skill=c.Bowling_Id) c
      on a.Bowler=c.Player_Id
      where Overs>=50
      order by Economy,Wicket_rate desc; """
    },
    {
      "query": "Best Bowlers in IPL",
      "sql": """ select Player_Name,Country_Name,
        Matches,Runs,Wickets,Economy,Best
        from(select Bowler,sum(coalesce(Extra_Runs,0)+Runs_Scored) as Runs,
             count(*)/6 as overs,
             round(round(sum(coalesce(Extra_Runs,0)+Runs_Scored),2)/round(count(*)/6,2),2) as Economy
             from Ball_by_Ball a
             left join Batsman_Scored b
             on a.Match_Id=b.Match_Id
             and a.Innings_No=b.Innings_No
             and a.Over_Id=b.Over_Id
             and a.Ball_Id=b.Ball_Id
             left join Extra_Runs c
             on a.Match_Id=c.Match_Id
             and a.Innings_No=c.Innings_No
             and a.Over_Id=c.Over_Id
             and a.Ball_Id=c.Ball_Id
             group by Bowler
             having overs>=50) a 
        join( select Bowler,count(Kind_Out) as Wickets
              from Ball_by_Ball a
              join Wicket_Taken b
              on a.Match_Id=b.Match_Id 
              and a.Innings_No=b.Innings_No
              and a.Over_Id=b.Over_Id 
              and a.Ball_Id=b.Ball_Id
              where Kind_Out in (1,2,4,6,7,8)
              group by Bowler) b
        on a.Bowler=b.Bowler
        join( select a.Bowler,max(Wickets)||"-"||runs as Best
              from( select a.Bowler,a.Match_Id,count(Kind_Out) as Wickets
                    from Ball_by_Ball a
                    join Wicket_Taken b
                    on a.Match_Id=b.Match_Id 
                    and a.Innings_No=b.Innings_No
                    and a.Over_Id=b.Over_Id 
                    and a.Ball_Id=b.Ball_Id
                    where Kind_Out in (1,2,4,6,7,8)
                    group by a.Bowler,a.Match_Id) a
              join( select a.Bowler,a.Match_Id,
                    sum(coalesce(Runs_Scored,0)+coalesce(Extra_Runs,0)) as runs
                    from Ball_by_Ball a
                    left join Batsman_Scored b 
                    on a.Match_Id=b.Match_Id 
                    and a.Innings_No=b.Innings_No
                    and a.Over_Id=b.Over_Id 
                    and a.Ball_Id=b.Ball_Id
                    left join Extra_Runs c
                    on a.Match_Id=c.Match_Id 
                    and a.Innings_No=c.Innings_No
                    and a.Over_Id=c.Over_Id 
                    and a.Ball_Id=c.Ball_Id
                    group by a.Bowler,a.Match_Id) b
              on a.Bowler=b.Bowler
              group by a.Bowler) c
        on a.Bowler=c.Bowler
        join( select Bowler,count (distinct Match_Id)as Matches
              from Ball_by_Ball
              group by Bowler) d
        on a.Bowler=d.Bowler
        join (select Player_Id,Player_Name,b.Bowling_skill,c.Country_Name
              from Player a
              join Bowling_Style b
              on a.Bowling_skill=b.Bowling_Id
              join Country c
              on a.Country_Name=c.Country_Id) e
        on a.Bowler=e.Player_Id
        order by Economy,Wickets; """
    },
    {
      "query": "Batsmens who have faced most deliveries",
      "sql": """
                SELECT Player_Name,c.Country_Name,d.Batting_hand,count(*) as Deliveries
       FROM Ball_by_Ball a
       join Player b
       on a.Striker==b.Player_Id
       join Country c
       on b.Country_Name==c.Country_Id
       join Batting_Style d
       on b.Batting_hand==d.Batting_Id
       group by Striker
       order by Deliveries desc ;"""
    },
     {
      "query": "# Highest run scored by a batsman in an IPL ",
      "sql": """select Player_Name,Country_Name,Batting_hand,sum(Runs_Scored) as Runs
        from Batsman_Scored a
        join Ball_by_Ball b
        on a.Match_Id=b.Match_Id 
        and a.Innings_No=b.Innings_No
        and a.Over_Id=b.Over_Id 
        and a.Ball_Id=b.Ball_Id
        join (select Player_Id,Player_Name,b.Country_Name, c.Batting_hand
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Batting_Style c
              on a.Batting_hand=c.Batting_Id) c
        on b.Striker=c.Player_Id
        group by c.Player_Id
        order by Runs desc; """
    },
     {
      "query": " Player who got dismissed at duck(0 score) highest no of times",
      "sql": """
               select Player_Name,Country_Name,Batting_hand,count(runs) as ducks
        from(select Striker,sum(Runs_Scored) as runs
             from (select Match_Id,Innings_No,Over_Id,Ball_Id,Striker
                   from Ball_by_Ball 
                   where Striker in (select Player_Out
                                   from Wicket_Taken))a
            join Batsman_Scored b
            on a.Match_Id=b.Match_Id 
            and a.Innings_No=b.Innings_No
            and a.Over_Id=b.Over_Id 
            and a.Ball_Id=b.Ball_Id
            group by Striker,a.Match_Id
            having runs==0) a
        join (select Player_Id,Player_Name,b.Country_Name, c.Batting_hand
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Batting_Style c
              on a.Batting_hand=c.Batting_Id) b
        on a.Striker=b.Player_Id
        group by Player_Id
        order by ducks desc; """

    },
     {
      "query": "Highest run score by a batsman in an IPL match",
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
     {
      "query": "No of fifties and centruies by a batsman in an IPL",
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
     {
      "query": "Power Hitters of IPL",
      "sql": """
                select Player_Name,Country_Name,boundaries,fours,sixes
        from(select Striker,
             sum(case when Runs_Scored==4 or Runs_Scored==6 then 1 else 0 end) as boundaries,
             sum(case when Runs_Scored==4 then 1 else 0 end) as fours,
             sum(case when Runs_Scored==6 then 1 else 0 end) as sixes
             from Ball_by_Ball a
            join Batsman_Scored b
            on a.Match_Id=b.Match_Id 
            and a.Innings_No=b.Innings_No
            and a.Over_Id=b.Over_Id 
            and a.Ball_Id=b.Ball_Id
            group by Striker) a
        join (select Player_Id,Player_Name,b.Country_Name, c.Batting_hand
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Batting_Style c
              on a.Batting_hand=c.Batting_Id) b
        on a.Striker=b.Player_Id
        order by sixes desc; """
    },
     {
      "query": "Batsman's with Highest strike rate and batting_average in IPL",
      "sql": """
                select Player_Name as Player,Country_Name
       Matches,Runs,
       round(round(Runs,2)/round(dismissals,2),2) as Batting_Avg,Strike_Rate
       from(select Striker,sum(coalesce(Runs_Scored,0)) as Runs,
             100*round(round(sum(coalesce(Runs_Scored,0)),2)/round(count(*),2),4) as Strike_Rate
             from Ball_by_Ball a
             left join Batsman_Scored b
             on a.Match_Id=b.Match_Id 
             and a.Innings_No=b.Innings_No
             and a.Over_Id=b.Over_Id 
             and a.Ball_Id=b.Ball_Id
             left join Extra_Runs c
             on a.Match_Id=c.Match_Id 
             and a.Innings_No=c.Innings_No
             and a.Over_Id=c.Over_Id 
             and a.Ball_Id=c.Ball_Id
             where Extra_Type_Id !=2 or Extra_Type_Id is null
             group by Striker) a
        join(select Player_Out,count(*) as dismissals
             from Wicket_Taken
             group by Player_Out) b
        on a.Striker=b.Player_Out
        join( select Striker,count (distinct Match_Id)as Matches
              from Ball_by_Ball
              group by Striker) c
        on a.Striker=c.Striker
        join (select Player_Id,Player_Name,b.Country_Name, c.Batting_hand
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Batting_Style c
              on a.Batting_hand=c.Batting_Id) d
        on a.Striker=d.Player_Id
        where Matches>=50
        order by Batting_Avg desc,Strike_Rate desc ; """
    },
     {
      "query": " Best Batsman's in IPL",
      "sql": """
                 select Player_Name as Player,
        Matches,Runs,Strike_Rate,
        round(round(Runs,2)/round(dismissals,2),2) as Batting_Avg,
        fifties,centuries,Best_Score
        from(select Striker,sum(coalesce(Runs_Scored,0)) as Runs,
             100*round(round(sum(coalesce(Runs_Scored,0)),2)/round(count(*),2),4) as Strike_Rate
             from Ball_by_Ball a
             left join Batsman_Scored b
             on a.Match_Id=b.Match_Id 
             and a.Innings_No=b.Innings_No
             and a.Over_Id=b.Over_Id 
             and a.Ball_Id=b.Ball_Id
             left join Extra_Runs c
             on a.Match_Id=c.Match_Id 
             and a.Innings_No=c.Innings_No
             and a.Over_Id=c.Over_Id 
             and a.Ball_Id=c.Ball_Id
             where Extra_Type_Id !=2 or Extra_Type_Id is null
             group by Striker) a
        join(select Player_Out,count(*) as dismissals
             from Wicket_Taken
             group by Player_Out) b
        on a.Striker=b.Player_Out
        join( select Striker,sum(case when runs==0 then 1 else 0 end) as Ducks,
              sum(case when runs>=50 and runs<100 then 1 else 0 end) as fifties,
              sum(case when runs>=100 then 1 else 0 end) as centuries,
              max(runs) as Best_Score
              from(select Striker,sum(Runs_Scored) as runs
                   from Ball_by_Ball a
                   join Batsman_Scored b
                   on a.Match_Id=b.Match_Id 
                   and a.Innings_No=b.Innings_No
                   and a.Over_Id=b.Over_Id 
                   and a.Ball_Id=b.Ball_Id
                   group by Striker,a.Match_Id)
               group by Striker) c
        on a.Striker=c.Striker
        join(select Striker,
             sum(case when Runs_Scored==4 then 1 else 0 end) as Fours,
             sum(case when Runs_Scored==6 then 1 else 0 end) as Sixes
             from Ball_by_Ball a
             join Batsman_Scored b
             on a.Match_Id=b.Match_Id 
             and a.Innings_No=b.Innings_No
             and a.Over_Id=b.Over_Id 
             and a.Ball_Id=b.Ball_Id
             group by Striker) d
        on a.Striker=d.Striker
        join( select Striker,count (distinct Match_Id)as Matches
              from Ball_by_Ball
              group by Striker) e
        on a.Striker=e.Striker
        join (select Player_Id,Player_Name,b.Country_Name, c.Batting_hand
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Batting_Style c
              on a.Batting_hand=c.Batting_Id) f
        on a.Striker=f.Player_Id
        where Matches>=50"""
    },
     {
      "query": "Best Fielders in IPL",
      "sql": """select Player_Name,Country_Name,dismissals,catch,run_out
        from(select Player_Name,Country_Name,count(Kind_Out) as dismissals,
             sum(case when Kind_Out==1 then 1 else 0 end) as catch,
             sum(case when Kind_Out==3 then 1 else 0 end) as run_out,
             sum(case when Kind_Out==6 then 1 else 0 end) as stumping
             from Wicket_Taken a
             join (select Player_Id,Player_Name,b.Country_Name
                   from Player a
                   join Country b
                   on a.Country_Name=b.Country_Id) b
             on a.Fielders=b.Player_Id
             where Kind_Out in (1,3,6)
             group by b.Player_Id
             having stumping=0
             order by dismissals desc) ; """
    },
     {
      "query": "Best Wicket-Keepers in IPL",
      "sql": """
                 select Player_Name,Country_Name,count(Kind_Out) as dismissals,
        sum(case when Kind_Out==1 then 1 else 0 end) as catch,
        sum(case when Kind_Out==3 then 1 else 0 end) as run_out,
        sum(case when Kind_Out==6 then 1 else 0 end) as stumping
        from Wicket_Taken a
        join (select Player_Id,Player_Name,b.Country_Name
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id) b
        on a.Fielders=b.Player_Id
        where Kind_Out in (1,3,6)
        group by b.Player_Id
        having stumping!=0
        order by dismissals desc; """
    },
     {
      "query": "Most successful captains of IPL",
      "sql": """
                select Player_Name as Captain,Country_Name,
       count(*) as Matches,
       sum(case when a.Team_Id=b.Winner then 1 else 0 end) as Wins,
       round(round(sum(case when a.Team_Id=b.Winner then 1 else 0 end),2)/round(count(*),2),2) as Win_perc,
       round(round(sum(case when a.Team_Id=b.Winner then chasing else 0 end),2)/round(sum(case when a.Team_Id!=b.Winner then defending else 0 end+case when a.Team_Id=b.Winner then chasing else 0 end),2),2) as Chasing_perc ,
       round(round(sum(case when a.Team_Id=b.Winner then defending else 0 end),2)/round(sum(case when a.Team_Id!=b.Winner then chasing else 0 end+case when a.Team_Id=b.Winner then defending else 0 end),2),2) as Defending_perc
       from (select Match_Id,Team_Id,Player_Id
             from Player_Match 
             where Role_Id in (1,4)
             group by Match_Id,Team_Id,Player_Id) a
       left join(select Match_Id, 
                 case when Win_Type==1 
                      then case when Toss_Winner=Team_1 and Toss_Decide=2 then Team_1
                                when Toss_Winner=Team_1 and Toss_Decide=1 then Team_2
                                when Toss_Winner=Team_2 and Toss_Decide=2 then Team_2
                                else Team_1 end
                      else case when Toss_Winner=Team_1 and Toss_Decide=2 then Team_2
                                when Toss_Winner=Team_1 and Toss_Decide=1 then Team_1
                                when Toss_Winner=Team_2 and Toss_Decide=2 then Team_1
                                else Team_2 end 
                      end as Winner,
                case when Win_Type==1 then 1 else 0 end as defending,
                case when Win_Type==2 then 1 else 0 end as chasing
                from Match a
                where Win_Type in (1,2)) as b
        on a.Match_Id=b.Match_Id
        join( select Player_Id,Player_Name,b.Country_Name
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id) c
        on a.Player_Id=c.Player_Id
        group by a.Player_Id
        having Matches>=30
        order by Win_perc desc, Chasing_perc desc,Defending_perc desc; """
    },
     {
      "query": "Best Teams in IPL",
      "sql": """
                select Team_Name as franchise,
        a.matches+b.matches as Matches,c.Wins,
        round(round(Wins,2)/round(a.matches+b.matches,2),2) as Win_perc
        from( select Season_Id,Team_1,
              count(*) as matches
              from Match
              group by Team_1) a
        join( select Season_Id,Team_2,
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
        join Team d
        on a.Team_1=d.Team_Id
        order by Win_perc desc; """
    },
     {
      "query": " best team in defending the score",
      "sql": """
                select 
        case when Toss_Winner=Team_1 and Toss_Decide=2 then b.Team_Name
             when Toss_Winner=Team_1 and Toss_Decide=1 then c.Team_Name
             when Toss_Winner=Team_2 and Toss_Decide=2 then c.Team_Name
             else b.Team_Name end as franchise,
        count(Match_Id) as matches,sum(case when Win_Type==1 then 1 else 0 end)as wins,
        round(round(sum(case when Win_Type==1 then 1 else 0 end),2)/round(count(Match_Id),2),2) as win_percentage
        from Match a
        join Team b
        on a.Team_1=b.Team_Id
        join Team c
        on a.Team_2=c.Team_Id
        group by franchise
        order by win_percentage desc;"""
    },
     {
      "query": "best team in chasing the score",
      "sql": """
                select 
        case when Toss_Winner=Team_1 and Toss_Decide=2 then c.Team_Name
             when Toss_Winner=Team_1 and Toss_Decide=1 then b.Team_Name
             when Toss_Winner=Team_2 and Toss_Decide=2 then b.Team_Name
             else c.Team_Name end as franchise,
        count(Match_Id) as matches,sum(case when Win_Type==2 then 1 else 0 end)as wins,
        round(round(sum(case when Win_Type==2 then 1 else 0 end),2)/round(count(Match_Id),2),2) as win_percentage
        from Match a
        join Team b
        on a.Team_1=b.Team_Id
        join Team c
        on a.Team_2=c.Team_Id
        group by franchise
        order by win_percentage desc; """
    },
     {
      "query": "Best Teams in IPL",
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
     {
      "query": "IPL Season's Best PLayers",
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
    {
      "query": "Runs scored in powerplay,middle and death overs in different seasons of IPL",
      "sql": """
                select Season_Year,Matches,
        sum(case when a.Over_Id<=6 then Runs_Scored+coalesce(Extra_Runs,0) else 0 end) as powerplay,
        sum(case when a.Over_Id>6 and a.Over_Id<=15 then Runs_Scored+coalesce(Extra_Runs,0) else 0 end) as middleovers,
        sum(case when a.Over_Id>15 then Runs_Scored+coalesce(Extra_Runs,0) else 0 end) as deathovers
        from Batsman_Scored a
        join Match b
        on a.Match_Id==b.Match_Id
        left join Extra_Runs c
        on a.Match_Id=c.Match_Id 
        and a.Innings_No=c.Innings_No
        and a.Over_Id=c.Over_Id
        and a.Ball_Id=c.Ball_Id
        join Season d
        on b.Season_Id==d.Season_Id
        join (select Season_Id,
              count(Match_Id) as Matches
              from Match 
              group by Season_Id) e
        on b.Season_Id==e.Season_Id
        group by d.Season_Year; """
    },
    {
      "query": "highest score of a Season",
      "sql": """
               select Season_Year,
        case when a.Innings_No==1 then c.Team_Name 
             else d.Team_Name end as batting_team,
        case when a.Innings_No==1 then d.Team_Name 
             else c.Team_Name end as fielding_team,
        max(runs+extra) as Score,City_Name
        from(select Season_Year,sum(Runs_Scored) as runs,
             a.Match_Id,a.Innings_No,Venue_id,
             case when Toss_Winner==Team_1 and Toss_Decide==1 then Team_2
                  when Toss_Winner==Team_1 and Toss_Decide==2 then Team_1
                  when Toss_Winner==Team_2 and Toss_Decide==1 then Team_1
                  else Team_2 end as batting,
             case when Toss_Winner==Team_1 and Toss_Decide==1 then Team_1
                  when Toss_Winner==Team_1 and Toss_Decide==2 then Team_2
                  when Toss_Winner==Team_2 and Toss_Decide==1 then Team_2
                  else Team_1 end as fielding
            from Batsman_Scored a
            join Match b
            on a.Match_Id=b.Match_Id
            join Season d
            on b.Season_Id=d.Season_Id
            group by Season_Year, a.Match_Id, a.Innings_No) a
        join (select Match_Id,Innings_No,sum(Extra_Runs) as extra
                  from Extra_Runs
                  group by Match_Id,Innings_No) b
        on a.Match_Id=b.Match_Id 
        and a.Innings_No=b.Innings_No
        join Team c
        on a.batting=c.Team_Id
        join Team d
        on a.fielding=d.Team_Id
        join (Select Venue_Id,Venue_Name,City_Name
              from Venue a
              join City b
              on a.City_Id=b.City_Id) e
        on a.Venue_Id=e.Venue_Id
        group by Season_Year; """
    },
    {
      "query": "#Lowest score of a Season",
      "sql": """
               select Season_Year,
        case when a.Innings_No==1 then c.Team_Name 
             else d.Team_Name end as batting_team,
        case when a.Innings_No==1 then d.Team_Name 
             else c.Team_Name end as fielding_team,
        min(runs+extra) as Score,City_Name
        from(select Season_Year,sum(Runs_Scored) as runs,
             a.Match_Id,a.Innings_No,Venue_id,
             case when Toss_Winner==Team_1 and Toss_Decide==1 then Team_2
                  when Toss_Winner==Team_1 and Toss_Decide==2 then Team_1
                  when Toss_Winner==Team_2 and Toss_Decide==1 then Team_1
                  else Team_2 end as batting,
             case when Toss_Winner==Team_1 and Toss_Decide==1 then Team_1
                  when Toss_Winner==Team_1 and Toss_Decide==2 then Team_2
                  when Toss_Winner==Team_2 and Toss_Decide==1 then Team_2
                  else Team_1 end as fielding
            from Batsman_Scored a
            join Match b
            on a.Match_Id=b.Match_Id
            join Season d
            on b.Season_Id=d.Season_Id
            where Win_Type not in (3,4)
            group by Season_Year, a.Match_Id, a.Innings_No) a
        join (select Match_Id,Innings_No,sum(Extra_Runs) as extra
                  from Extra_Runs
                  group by Match_Id,Innings_No) b
        on a.Match_Id=b.Match_Id 
        and a.Innings_No=b.Innings_No
        join Team c
        on a.batting=c.Team_Id
        join Team d
        on a.fielding=d.Team_Id
        join (Select Venue_Id,Venue_Name,City_Name
              from Venue a
              join City b
              on a.City_Id=b.City_Id) e
        on a.Venue_Id=e.Venue_Id
        group by Season_Year; """
    },

    {
        "query": " IPL Season's Winners,Runners Up, Win Type",
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
    }

]


examples_of_tables_sql = [
    {
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
    {
      "tables": ["Wicket_Taken", "Ball_by_Ball", "Player", "Country", "Bowling_Style"],
        "sql": """ select Player_Name,count(Kind_Out) as Wickets,
        sum(case when Kind_Out==1 then 1 else 0 end) as caught,
        sum(case when Kind_Out==2 then 1 else 0 end) as bowled,
        sum(case when Kind_Out==4 then 1 else 0 end) as lbw,
        sum(case when Kind_Out==6 then 1 else 0 end) as stumped
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
        group by c.Player_Id
        order by Wickets desc; """
    },
    {
      "tables": ["Ball_by_Ball", "Wicket_Taken", "Batsman_Scored", "Extra_Runs", "Player", "Country", "Bowling_Style"],
      "sql": """select Player_Name,Country_Name,Bowling_skill,
        Wickets||"-"||runs as Best
        from( select a.Bowler,a.Match_Id,count(Kind_Out) as Wickets
              from Ball_by_Ball a
              join Wicket_Taken b
              on a.Match_Id=b.Match_Id 
              and a.Innings_No=b.Innings_No
              and a.Over_Id=b.Over_Id 
              and a.Ball_Id=b.Ball_Id
              where Kind_Out in (1,2,4,6,7,8)
              group by a.Bowler,a.Match_Id) a
        join( select a.Bowler,a.Match_Id,
              sum(coalesce(Runs_Scored,0)+coalesce(Extra_Runs,0)) as runs
              from Ball_by_Ball a
              left join Batsman_Scored b 
              on a.Match_Id=b.Match_Id 
              and a.Innings_No=b.Innings_No
              and a.Over_Id=b.Over_Id 
              and a.Ball_Id=b.Ball_Id
              left join Extra_Runs c
              on a.Match_Id=c.Match_Id 
              and a.Innings_No=c.Innings_No
              and a.Over_Id=c.Over_Id 
              and a.Ball_Id=c.Ball_Id
              group by a.Bowler,a.Match_Id) b
              on a.Bowler=b.Bowler
              and a.Match_Id=b.Match_Id
        join( select Player_Id,Player_Name,b.Country_Name, c.Bowling_skill
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Bowling_Style c
              on a.Bowling_skill=c.Bowling_Id) c
        on a.Bowler=c.Player_Id
        order by Wickets desc; """
    },
    {
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
    {
      "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Player", "Country", "Bowling_Style"],
      "sql": """ select Player_Name,Country_Name,Bowling_skill,runs
        from( select a.Bowler,
              sum(coalesce(Runs_Scored,0)+coalesce(Extra_Runs,0)) as runs
              from Ball_by_Ball a
              left join Batsman_Scored b 
              on a.Match_Id=b.Match_Id 
              and a.Innings_No=b.Innings_No
              and a.Over_Id=b.Over_Id 
              and a.Ball_Id=b.Ball_Id
              left join Extra_Runs c
              on a.Match_Id=c.Match_Id 
              and a.Innings_No=c.Innings_No
              and a.Over_Id=c.Over_Id 
              and a.Ball_Id=c.Ball_Id
              group by a.Bowler,a.Match_Id) a
        join( select Player_Id,Player_Name,b.Country_Name, c.Bowling_skill
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Bowling_Style c
              on a.Bowling_skill=c.Bowling_Id) b
        on a.Bowler=b.Player_Id
        order by runs desc; """
    },
    {
      "tables": ["Batsman_Scored", "Extra_Runs", "Ball_by_Ball", "Player", "Bowling_Style", "Country", "Venue", "City"],
      "sql": """select Player_Name as Bowler,
        max(runs+extra) as Runs,Fours,Sixes,
        Extra,wides,noballs,legbyes
        from(select Match_Id,Innings_No,Over_Id,sum(Runs_Scored) as runs,
             sum(case when Runs_Scored==4 then 1 else 0 end) as Fours,
             sum(case when Runs_Scored==6 then 1 else 0 end) as Sixes
             from Batsman_Scored
             group by Match_Id, Innings_No,Over_Id) a
        join(select Match_Id,Innings_No,Over_Id,sum(Extra_Runs) as Extra,
             sum(case when Extra_Type_Id==1 then 1 else 0 end) as legbyes,
             sum(case when Extra_Type_Id==2 then 1 else 0 end) as wides,
             sum(case when Extra_Type_Id==4 then 1 else 0 end) as noballs
             from Extra_Runs
             group by Match_Id,Innings_No,Over_Id) b
        on a.Match_Id=b.Match_Id 
        and a.Innings_No=b.Innings_No
        and a.Over_Id=b.Over_Id
        join (select Match_Id,Innings_No,Over_Id,Player_Name,
              c.Bowling_skill,d.Country_Name
              from Ball_by_Ball a
              join Player b
              on a.Bowler=b.Player_Id
              join Bowling_Style c
              on b.Bowling_skill=c.Bowling_Id
              join Country d
              on b.Country_Name=d.Country_Id
              group by Match_Id,Innings_No,Over_id) c
         on a.Match_Id=c.Match_Id 
         and a.Innings_No=c.Innings_No
         and a.Over_Id=c.Over_Id
         group by a.Match_Id,a.Innings_No,a.Over_Id
         order by Runs desc; """
    },
    {
      "tables": ["Batsman_Scored", "Ball_by_Ball", "Extra_Runs", "Player", "Bowling_Style", "Country"],
      "sql": """select Player_Name,Country_Name,
        overs,runs,extras,economy
        from(select Bowler,sum(coalesce(Extra_Runs,0)+Runs_Scored) as runs,
             sum(coalesce(Extra_Runs,0)) as extras,
             count(*)/6 as overs,
             round(round(sum(coalesce(Extra_Runs,0)+Runs_Scored),2)/round(count(*)/6,2),2) as economy
             from Batsman_Scored a
             join Ball_by_Ball b
             on a.Match_Id=b.Match_Id
             and a.Innings_No=b.Innings_No
             and a.Over_Id=b.Over_Id
             and a.Ball_Id=b.Ball_Id
             left join Extra_Runs c
             on a.Match_Id=c.Match_Id
             and a.Innings_No=c.Innings_No
             and a.Over_Id=c.Over_Id
             and a.Ball_Id=c.Ball_Id
             group by Bowler
             having overs>=50) a
        join (select Player_Id,Player_Name,b.Bowling_skill,c.Country_Name
              from Player a
              join Bowling_Style b
              on a.Bowling_skill=b.Bowling_Id
              join Country c
              on a.Country_Name=c.Country_Id) b
        on a.Bowler=b.Player_Id 
        order by economy asc; """
    },
    {
      "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Wicket_Taken", "Player", "Country", "Bowling_Style"],
      "sql": """select Player_Name,Country_Name,
       Overs,Runs,Wickets,Economy,
       round(round(Wickets,2)/round(Overs,2),2) as Wicket_rate
       from( select Bowler,count(*) as Overs,sum(runs) as Runs,
             round(round(sum(runs),2)/round(count(*),2),2) as Economy
             from (select a.Bowler,a.Match_Id,
                   sum(coalesce(Runs_Scored,0)+coalesce(Extra_Runs,0)) as runs
                   from Ball_by_Ball a
                   left join Batsman_Scored b 
                   on a.Match_Id=b.Match_Id 
                   and a.Innings_No=b.Innings_No
                   and a.Over_Id=b.Over_Id 
                   and a.Ball_Id=b.Ball_Id
                   left join Extra_Runs c
                   on a.Match_Id=c.Match_Id 
                   and a.Innings_No=c.Innings_No
                   and a.Over_Id=c.Over_Id 
                   and a.Ball_Id=c.Ball_Id
                   where a.Over_Id in (16,17,18,19,20)
                   group by a.Bowler,a.Match_Id,a.Over_Id)
              group by Bowler) a 
        join( select Bowler,sum(Kind_Out) as Wickets
              from Ball_by_Ball a
              join Wicket_Taken b
              on a.Match_Id=b.Match_Id 
              and a.Innings_No=b.Innings_No
              and a.Over_Id=b.Over_Id 
              and a.Ball_Id=b.Ball_Id
              where a.Over_Id in (16,17,18,19,20) and
              Kind_Out in (1,2,4,6,7,8)
              group by a.Bowler) b
        on a.Bowler=b.Bowler
        join( select Player_Id,Player_Name,b.Country_Name, c.Bowling_skill
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Bowling_Style c
              on a.Bowling_skill=c.Bowling_Id) c
      on a.Bowler=c.Player_Id
      where Overs>=50
      order by Economy,Wicket_rate desc; """
    },
    {
      "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Wicket_Taken", "Player", "Country", "Bowling_Style"],
      "sql": """select Player_Name,Country_Name,
       Overs,Runs,Wickets,Economy,
       round(round(Wickets,2)/round(Overs,2),2) as Wicket_rate
       from( select Bowler,count(*) as Overs,sum(runs) as Runs,
             round(round(sum(runs),2)/round(count(*),2),2) as Economy
             from (select a.Bowler,a.Match_Id,
                   sum(coalesce(Runs_Scored,0)+coalesce(Extra_Runs,0)) as runs
                   from Ball_by_Ball a
                   left join Batsman_Scored b 
                   on a.Match_Id=b.Match_Id 
                   and a.Innings_No=b.Innings_No
                   and a.Over_Id=b.Over_Id 
                   and a.Ball_Id=b.Ball_Id
                   left join Extra_Runs c
                   on a.Match_Id=c.Match_Id 
                   and a.Innings_No=c.Innings_No
                   and a.Over_Id=c.Over_Id 
                   and a.Ball_Id=c.Ball_Id
                   where a.Over_Id in (1,2,3,4,5,6)
                   group by a.Bowler,a.Match_Id,a.Over_Id)
              group by Bowler) a 
        join( select Bowler,sum(Kind_Out) as Wickets
              from Ball_by_Ball a
              join Wicket_Taken b
              on a.Match_Id=b.Match_Id 
              and a.Innings_No=b.Innings_No
              and a.Over_Id=b.Over_Id 
              and a.Ball_Id=b.Ball_Id
              where a.Over_Id in (1,2,3,4,5,6) and
              Kind_Out in (1,2,4,6,7,8)
              group by a.Bowler) b
        on a.Bowler=b.Bowler
        join( select Player_Id,Player_Name,b.Country_Name, c.Bowling_skill
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Bowling_Style c
              on a.Bowling_skill=c.Bowling_Id) c
      on a.Bowler=c.Player_Id
      where Overs>=50
      order by Economy,Wicket_rate desc; """
    },
    {
      "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Wicket_Taken", "Player", "Country", "Bowling_Style"],
      "sql": """select Player_Name,Country_Name,
       Overs,Runs,Wickets,Economy,
       round(round(Wickets,2)/round(Overs,2),2) as Wicket_rate
       from( select Bowler,count(*) as Overs,sum(runs) as Runs,
             round(round(sum(runs),2)/round(count(*),2),2) as Economy
             from (select a.Bowler,a.Match_Id,
                   sum(coalesce(Runs_Scored,0)+coalesce(Extra_Runs,0)) as runs
                   from Ball_by_Ball a
                   left join Batsman_Scored b 
                   on a.Match_Id=b.Match_Id 
                   and a.Innings_No=b.Innings_No
                   and a.Over_Id=b.Over_Id 
                   and a.Ball_Id=b.Ball_Id
                   left join Extra_Runs c
                   on a.Match_Id=c.Match_Id 
                   and a.Innings_No=c.Innings_No
                   and a.Over_Id=c.Over_Id 
                   and a.Ball_Id=c.Ball_Id
                   where a.Over_Id in (7,8,9,10,11,12,13,14,15)
                   group by a.Bowler,a.Match_Id,a.Over_Id)
              group by Bowler) a 
        join( select Bowler,sum(Kind_Out) as Wickets
              from Ball_by_Ball a
              join Wicket_Taken b
              on a.Match_Id=b.Match_Id 
              and a.Innings_No=b.Innings_No
              and a.Over_Id=b.Over_Id 
              and a.Ball_Id=b.Ball_Id
              where a.Over_Id in (1,2,3,4,5,6) and
              Kind_Out in (1,2,4,6,7,8)
              group by a.Bowler) b
        on a.Bowler=b.Bowler
        join( select Player_Id,Player_Name,b.Country_Name, c.Bowling_skill
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Bowling_Style c
              on a.Bowling_skill=c.Bowling_Id) c
      on a.Bowler=c.Player_Id
      where Overs>=50
      order by Economy,Wicket_rate desc; """
    },
    {
      "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Wicket_Taken", "Player", "Bowling_Style", "Country"],
      "sql": """ select Player_Name,Country_Name,
        Matches,Runs,Wickets,Economy,Best
        from(select Bowler,sum(coalesce(Extra_Runs,0)+Runs_Scored) as Runs,
             count(*)/6 as overs,
             round(round(sum(coalesce(Extra_Runs,0)+Runs_Scored),2)/round(count(*)/6,2),2) as Economy
             from Ball_by_Ball a
             left join Batsman_Scored b
             on a.Match_Id=b.Match_Id
             and a.Innings_No=b.Innings_No
             and a.Over_Id=b.Over_Id
             and a.Ball_Id=b.Ball_Id
             left join Extra_Runs c
             on a.Match_Id=c.Match_Id
             and a.Innings_No=c.Innings_No
             and a.Over_Id=c.Over_Id
             and a.Ball_Id=c.Ball_Id
             group by Bowler
             having overs>=50) a 
        join( select Bowler,count(Kind_Out) as Wickets
              from Ball_by_Ball a
              join Wicket_Taken b
              on a.Match_Id=b.Match_Id 
              and a.Innings_No=b.Innings_No
              and a.Over_Id=b.Over_Id 
              and a.Ball_Id=b.Ball_Id
              where Kind_Out in (1,2,4,6,7,8)
              group by Bowler) b
        on a.Bowler=b.Bowler
        join( select a.Bowler,max(Wickets)||"-"||runs as Best
              from( select a.Bowler,a.Match_Id,count(Kind_Out) as Wickets
                    from Ball_by_Ball a
                    join Wicket_Taken b
                    on a.Match_Id=b.Match_Id 
                    and a.Innings_No=b.Innings_No
                    and a.Over_Id=b.Over_Id 
                    and a.Ball_Id=b.Ball_Id
                    where Kind_Out in (1,2,4,6,7,8)
                    group by a.Bowler,a.Match_Id) a
              join( select a.Bowler,a.Match_Id,
                    sum(coalesce(Runs_Scored,0)+coalesce(Extra_Runs,0)) as runs
                    from Ball_by_Ball a
                    left join Batsman_Scored b 
                    on a.Match_Id=b.Match_Id 
                    and a.Innings_No=b.Innings_No
                    and a.Over_Id=b.Over_Id 
                    and a.Ball_Id=b.Ball_Id
                    left join Extra_Runs c
                    on a.Match_Id=c.Match_Id 
                    and a.Innings_No=c.Innings_No
                    and a.Over_Id=c.Over_Id 
                    and a.Ball_Id=c.Ball_Id
                    group by a.Bowler,a.Match_Id) b
              on a.Bowler=b.Bowler
              group by a.Bowler) c
        on a.Bowler=c.Bowler
        join( select Bowler,count (distinct Match_Id)as Matches
              from Ball_by_Ball
              group by Bowler) d
        on a.Bowler=d.Bowler
        join (select Player_Id,Player_Name,b.Bowling_skill,c.Country_Name
              from Player a
              join Bowling_Style b
              on a.Bowling_skill=b.Bowling_Id
              join Country c
              on a.Country_Name=c.Country_Id) e
        on a.Bowler=e.Player_Id
        order by Economy,Wickets; """
    },
    {
     "tables": ["Ball_by_Ball", "Player", "Country", "Batting_Style"],
      "sql": """
                SELECT Player_Name,c.Country_Name,d.Batting_hand,count(*) as Deliveries
       FROM Ball_by_Ball a
       join Player b
       on a.Striker==b.Player_Id
       join Country c
       on b.Country_Name==c.Country_Id
       join Batting_Style d
       on b.Batting_hand==d.Batting_Id
       group by Striker
       order by Deliveries desc ;"""
    },
     {
      "tables": ["Batsman_Scored", "Ball_by_Ball", "Player", "Country", "Batting_Style"],
      "sql": """select Player_Name,Country_Name,Batting_hand,sum(Runs_Scored) as Runs
        from Batsman_Scored a
        join Ball_by_Ball b
        on a.Match_Id=b.Match_Id 
        and a.Innings_No=b.Innings_No
        and a.Over_Id=b.Over_Id 
        and a.Ball_Id=b.Ball_Id
        join (select Player_Id,Player_Name,b.Country_Name, c.Batting_hand
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Batting_Style c
              on a.Batting_hand=c.Batting_Id) c
        on b.Striker=c.Player_Id
        group by c.Player_Id
        order by Runs desc; """
    },
     {
     "tables": ["Ball_by_Ball", "Wicket_Taken", "Batsman_Scored", "Player", "Country", "Batting_Style"],
      "sql": """
               select Player_Name,Country_Name,Batting_hand,count(runs) as ducks
        from(select Striker,sum(Runs_Scored) as runs
             from (select Match_Id,Innings_No,Over_Id,Ball_Id,Striker
                   from Ball_by_Ball 
                   where Striker in (select Player_Out
                                   from Wicket_Taken))a
            join Batsman_Scored b
            on a.Match_Id=b.Match_Id 
            and a.Innings_No=b.Innings_No
            and a.Over_Id=b.Over_Id 
            and a.Ball_Id=b.Ball_Id
            group by Striker,a.Match_Id
            having runs==0) a
        join (select Player_Id,Player_Name,b.Country_Name, c.Batting_hand
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Batting_Style c
              on a.Batting_hand=c.Batting_Id) b
        on a.Striker=b.Player_Id
        group by Player_Id
        order by ducks desc; """

    },
     {
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
     {
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
     {
      "tables": ["Ball_by_Ball", "Batsman_Scored", "Player", "Country", "Batting_Style"],
      "sql": """
                select Player_Name,Country_Name,boundaries,fours,sixes
        from(select Striker,
             sum(case when Runs_Scored==4 or Runs_Scored==6 then 1 else 0 end) as boundaries,
             sum(case when Runs_Scored==4 then 1 else 0 end) as fours,
             sum(case when Runs_Scored==6 then 1 else 0 end) as sixes
             from Ball_by_Ball a
            join Batsman_Scored b
            on a.Match_Id=b.Match_Id 
            and a.Innings_No=b.Innings_No
            and a.Over_Id=b.Over_Id 
            and a.Ball_Id=b.Ball_Id
            group by Striker) a
        join (select Player_Id,Player_Name,b.Country_Name, c.Batting_hand
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Batting_Style c
              on a.Batting_hand=c.Batting_Id) b
        on a.Striker=b.Player_Id
        order by sixes desc; """
    },
     {
      "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Wicket_Taken", "Player", "Country", "Batting_Style"],
      "sql": """
                select Player_Name as Player,Country_Name
       Matches,Runs,
       round(round(Runs,2)/round(dismissals,2),2) as Batting_Avg,Strike_Rate
       from(select Striker,sum(coalesce(Runs_Scored,0)) as Runs,
             100*round(round(sum(coalesce(Runs_Scored,0)),2)/round(count(*),2),4) as Strike_Rate
             from Ball_by_Ball a
             left join Batsman_Scored b
             on a.Match_Id=b.Match_Id 
             and a.Innings_No=b.Innings_No
             and a.Over_Id=b.Over_Id 
             and a.Ball_Id=b.Ball_Id
             left join Extra_Runs c
             on a.Match_Id=c.Match_Id 
             and a.Innings_No=c.Innings_No
             and a.Over_Id=c.Over_Id 
             and a.Ball_Id=c.Ball_Id
             where Extra_Type_Id !=2 or Extra_Type_Id is null
             group by Striker) a
        join(select Player_Out,count(*) as dismissals
             from Wicket_Taken
             group by Player_Out) b
        on a.Striker=b.Player_Out
        join( select Striker,count (distinct Match_Id)as Matches
              from Ball_by_Ball
              group by Striker) c
        on a.Striker=c.Striker
        join (select Player_Id,Player_Name,b.Country_Name, c.Batting_hand
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Batting_Style c
              on a.Batting_hand=c.Batting_Id) d
        on a.Striker=d.Player_Id
        where Matches>=50
        order by Batting_Avg desc,Strike_Rate desc ; """
    },
     {
      "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Wicket_Taken", "Player", "Country", "Batting_Style"],
      "sql": """
                 select Player_Name as Player,
        Matches,Runs,Strike_Rate,
        round(round(Runs,2)/round(dismissals,2),2) as Batting_Avg,
        fifties,centuries,Best_Score
        from(select Striker,sum(coalesce(Runs_Scored,0)) as Runs,
             100*round(round(sum(coalesce(Runs_Scored,0)),2)/round(count(*),2),4) as Strike_Rate
             from Ball_by_Ball a
             left join Batsman_Scored b
             on a.Match_Id=b.Match_Id 
             and a.Innings_No=b.Innings_No
             and a.Over_Id=b.Over_Id 
             and a.Ball_Id=b.Ball_Id
             left join Extra_Runs c
             on a.Match_Id=c.Match_Id 
             and a.Innings_No=c.Innings_No
             and a.Over_Id=c.Over_Id 
             and a.Ball_Id=c.Ball_Id
             where Extra_Type_Id !=2 or Extra_Type_Id is null
             group by Striker) a
        join(select Player_Out,count(*) as dismissals
             from Wicket_Taken
             group by Player_Out) b
        on a.Striker=b.Player_Out
        join( select Striker,sum(case when runs==0 then 1 else 0 end) as Ducks,
              sum(case when runs>=50 and runs<100 then 1 else 0 end) as fifties,
              sum(case when runs>=100 then 1 else 0 end) as centuries,
              max(runs) as Best_Score
              from(select Striker,sum(Runs_Scored) as runs
                   from Ball_by_Ball a
                   join Batsman_Scored b
                   on a.Match_Id=b.Match_Id 
                   and a.Innings_No=b.Innings_No
                   and a.Over_Id=b.Over_Id 
                   and a.Ball_Id=b.Ball_Id
                   group by Striker,a.Match_Id)
               group by Striker) c
        on a.Striker=c.Striker
        join(select Striker,
             sum(case when Runs_Scored==4 then 1 else 0 end) as Fours,
             sum(case when Runs_Scored==6 then 1 else 0 end) as Sixes
             from Ball_by_Ball a
             join Batsman_Scored b
             on a.Match_Id=b.Match_Id 
             and a.Innings_No=b.Innings_No
             and a.Over_Id=b.Over_Id 
             and a.Ball_Id=b.Ball_Id
             group by Striker) d
        on a.Striker=d.Striker
        join( select Striker,count (distinct Match_Id)as Matches
              from Ball_by_Ball
              group by Striker) e
        on a.Striker=e.Striker
        join (select Player_Id,Player_Name,b.Country_Name, c.Batting_hand
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id
              join Batting_Style c
              on a.Batting_hand=c.Batting_Id) f
        on a.Striker=f.Player_Id
        where Matches>=50"""
    },
     {
      "tables": ["Wicket_Taken", "Player", "Country"],
      "sql": """select Player_Name,Country_Name,dismissals,catch,run_out
        from(select Player_Name,Country_Name,count(Kind_Out) as dismissals,
             sum(case when Kind_Out==1 then 1 else 0 end) as catch,
             sum(case when Kind_Out==3 then 1 else 0 end) as run_out,
             sum(case when Kind_Out==6 then 1 else 0 end) as stumping
             from Wicket_Taken a
             join (select Player_Id,Player_Name,b.Country_Name
                   from Player a
                   join Country b
                   on a.Country_Name=b.Country_Id) b
             on a.Fielders=b.Player_Id
             where Kind_Out in (1,3,6)
             group by b.Player_Id
             having stumping=0
             order by dismissals desc) ; """
    },
     {
      "tables": ["Wicket_Taken", "Player", "Country"],
      "sql": """
                 select Player_Name,Country_Name,count(Kind_Out) as dismissals,
        sum(case when Kind_Out==1 then 1 else 0 end) as catch,
        sum(case when Kind_Out==3 then 1 else 0 end) as run_out,
        sum(case when Kind_Out==6 then 1 else 0 end) as stumping
        from Wicket_Taken a
        join (select Player_Id,Player_Name,b.Country_Name
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id) b
        on a.Fielders=b.Player_Id
        where Kind_Out in (1,3,6)
        group by b.Player_Id
        having stumping!=0
        order by dismissals desc; """
    },
     {
      "tables": ["Player_Match", "Match", "Team", "Player", "Country"],
      "sql": """
                select Player_Name as Captain,Country_Name,
       count(*) as Matches,
       sum(case when a.Team_Id=b.Winner then 1 else 0 end) as Wins,
       round(round(sum(case when a.Team_Id=b.Winner then 1 else 0 end),2)/round(count(*),2),2) as Win_perc,
       round(round(sum(case when a.Team_Id=b.Winner then chasing else 0 end),2)/round(sum(case when a.Team_Id!=b.Winner then defending else 0 end+case when a.Team_Id=b.Winner then chasing else 0 end),2),2) as Chasing_perc ,
       round(round(sum(case when a.Team_Id=b.Winner then defending else 0 end),2)/round(sum(case when a.Team_Id!=b.Winner then chasing else 0 end+case when a.Team_Id=b.Winner then defending else 0 end),2),2) as Defending_perc
       from (select Match_Id,Team_Id,Player_Id
             from Player_Match 
             where Role_Id in (1,4)
             group by Match_Id,Team_Id,Player_Id) a
       left join(select Match_Id, 
                 case when Win_Type==1 
                      then case when Toss_Winner=Team_1 and Toss_Decide=2 then Team_1
                                when Toss_Winner=Team_1 and Toss_Decide=1 then Team_2
                                when Toss_Winner=Team_2 and Toss_Decide=2 then Team_2
                                else Team_1 end
                      else case when Toss_Winner=Team_1 and Toss_Decide=2 then Team_2
                                when Toss_Winner=Team_1 and Toss_Decide=1 then Team_1
                                when Toss_Winner=Team_2 and Toss_Decide=2 then Team_1
                                else Team_2 end 
                      end as Winner,
                case when Win_Type==1 then 1 else 0 end as defending,
                case when Win_Type==2 then 1 else 0 end as chasing
                from Match a
                where Win_Type in (1,2)) as b
        on a.Match_Id=b.Match_Id
        join( select Player_Id,Player_Name,b.Country_Name
              from Player a
              join Country b
              on a.Country_Name=b.Country_Id) c
        on a.Player_Id=c.Player_Id
        group by a.Player_Id
        having Matches>=30
        order by Win_perc desc, Chasing_perc desc,Defending_perc desc; """
    },
     {
      "tables": ["Match", "Team", "Season"],
      "sql": """
                select Team_Name as franchise,
        a.matches+b.matches as Matches,c.Wins,
        round(round(Wins,2)/round(a.matches+b.matches,2),2) as Win_perc
        from( select Season_Id,Team_1,
              count(*) as matches
              from Match
              group by Team_1) a
        join( select Season_Id,Team_2,
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
        join Team d
        on a.Team_1=d.Team_Id
        order by Win_perc desc; """
    },
     {
      "tables": ["Match", "Team"],
      "sql": """
                select 
        case when Toss_Winner=Team_1 and Toss_Decide=2 then b.Team_Name
             when Toss_Winner=Team_1 and Toss_Decide=1 then c.Team_Name
             when Toss_Winner=Team_2 and Toss_Decide=2 then c.Team_Name
             else b.Team_Name end as franchise,
        count(Match_Id) as matches,sum(case when Win_Type==1 then 1 else 0 end)as wins,
        round(round(sum(case when Win_Type==1 then 1 else 0 end),2)/round(count(Match_Id),2),2) as win_percentage
        from Match a
        join Team b
        on a.Team_1=b.Team_Id
        join Team c
        on a.Team_2=c.Team_Id
        group by franchise
        order by win_percentage desc;"""
    },
     {
      "tables": ["Match", "Team"],
      "sql": """
                select 
        case when Toss_Winner=Team_1 and Toss_Decide=2 then c.Team_Name
             when Toss_Winner=Team_1 and Toss_Decide=1 then b.Team_Name
             when Toss_Winner=Team_2 and Toss_Decide=2 then b.Team_Name
             else c.Team_Name end as franchise,
        count(Match_Id) as matches,sum(case when Win_Type==2 then 1 else 0 end)as wins,
        round(round(sum(case when Win_Type==2 then 1 else 0 end),2)/round(count(Match_Id),2),2) as win_percentage
        from Match a
        join Team b
        on a.Team_1=b.Team_Id
        join Team c
        on a.Team_2=c.Team_Id
        group by franchise
        order by win_percentage desc; """
    },
     {
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
     {
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
    {
      "tables": ["Batsman_Scored", "Match", "Extra_Runs", "Season"],
      "sql": """
                select Season_Year,Matches,
        sum(case when a.Over_Id<=6 then Runs_Scored+coalesce(Extra_Runs,0) else 0 end) as powerplay,
        sum(case when a.Over_Id>6 and a.Over_Id<=15 then Runs_Scored+coalesce(Extra_Runs,0) else 0 end) as middleovers,
        sum(case when a.Over_Id>15 then Runs_Scored+coalesce(Extra_Runs,0) else 0 end) as deathovers
        from Batsman_Scored a
        join Match b
        on a.Match_Id==b.Match_Id
        left join Extra_Runs c
        on a.Match_Id=c.Match_Id 
        and a.Innings_No=c.Innings_No
        and a.Over_Id=c.Over_Id
        and a.Ball_Id=c.Ball_Id
        join Season d
        on b.Season_Id==d.Season_Id
        join (select Season_Id,
              count(Match_Id) as Matches
              from Match 
              group by Season_Id) e
        on b.Season_Id==e.Season_Id
        group by d.Season_Year; """
    },
    {
      "tables": ["Batsman_Scored", "Match", "Extra_Runs", "Season", "Team", "Venue", "City"],
      "sql": """
               select Season_Year,
        case when a.Innings_No==1 then c.Team_Name 
             else d.Team_Name end as batting_team,
        case when a.Innings_No==1 then d.Team_Name 
             else c.Team_Name end as fielding_team,
        max(runs+extra) as Score,City_Name
        from(select Season_Year,sum(Runs_Scored) as runs,
             a.Match_Id,a.Innings_No,Venue_id,
             case when Toss_Winner==Team_1 and Toss_Decide==1 then Team_2
                  when Toss_Winner==Team_1 and Toss_Decide==2 then Team_1
                  when Toss_Winner==Team_2 and Toss_Decide==1 then Team_1
                  else Team_2 end as batting,
             case when Toss_Winner==Team_1 and Toss_Decide==1 then Team_1
                  when Toss_Winner==Team_1 and Toss_Decide==2 then Team_2
                  when Toss_Winner==Team_2 and Toss_Decide==1 then Team_2
                  else Team_1 end as fielding
            from Batsman_Scored a
            join Match b
            on a.Match_Id=b.Match_Id
            join Season d
            on b.Season_Id=d.Season_Id
            group by Season_Year, a.Match_Id, a.Innings_No) a
        join (select Match_Id,Innings_No,sum(Extra_Runs) as extra
                  from Extra_Runs
                  group by Match_Id,Innings_No) b
        on a.Match_Id=b.Match_Id 
        and a.Innings_No=b.Innings_No
        join Team c
        on a.batting=c.Team_Id
        join Team d
        on a.fielding=d.Team_Id
        join (Select Venue_Id,Venue_Name,City_Name
              from Venue a
              join City b
              on a.City_Id=b.City_Id) e
        on a.Venue_Id=e.Venue_Id
        group by Season_Year; """
    },
    {
      "tables": ["Batsman_Scored", "Match", "Extra_Runs", "Season", "Team", "Venue", "City"],
      "sql": """
               select Season_Year,
        case when a.Innings_No==1 then c.Team_Name 
             else d.Team_Name end as batting_team,
        case when a.Innings_No==1 then d.Team_Name 
             else c.Team_Name end as fielding_team,
        min(runs+extra) as Score,City_Name
        from(select Season_Year,sum(Runs_Scored) as runs,
             a.Match_Id,a.Innings_No,Venue_id,
             case when Toss_Winner==Team_1 and Toss_Decide==1 then Team_2
                  when Toss_Winner==Team_1 and Toss_Decide==2 then Team_1
                  when Toss_Winner==Team_2 and Toss_Decide==1 then Team_1
                  else Team_2 end as batting,
             case when Toss_Winner==Team_1 and Toss_Decide==1 then Team_1
                  when Toss_Winner==Team_1 and Toss_Decide==2 then Team_2
                  when Toss_Winner==Team_2 and Toss_Decide==1 then Team_2
                  else Team_1 end as fielding
            from Batsman_Scored a
            join Match b
            on a.Match_Id=b.Match_Id
            join Season d
            on b.Season_Id=d.Season_Id
            where Win_Type not in (3,4)
            group by Season_Year, a.Match_Id, a.Innings_No) a
        join (select Match_Id,Innings_No,sum(Extra_Runs) as extra
                  from Extra_Runs
                  group by Match_Id,Innings_No) b
        on a.Match_Id=b.Match_Id 
        and a.Innings_No=b.Innings_No
        join Team c
        on a.batting=c.Team_Id
        join Team d
        on a.fielding=d.Team_Id
        join (Select Venue_Id,Venue_Name,City_Name
              from Venue a
              join City b
              on a.City_Id=b.City_Id) e
        on a.Venue_Id=e.Venue_Id
        group by Season_Year; """
    },

    {
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
    }
]
# def create_prompt_with_examples_textTOSql(query, schema):
#     similar_docs = retriever.get_relevant_documents(query)
#     examples_text = "\n\n".join([doc.page_content for doc in similar_docs])

#     full_prompt =[ ("system",f"""You are a highly skilled SQL expert. Your task is to convert natural language questions into accurate SQL queries based on the provided list of tables.
#                 Ensure your generated SQL is correct and directly executable.Use the examples and the schema below to answer.

#                 Examples:
#                 {examples_text}

#                 Database Schema:
#                 {schema}

#                 Question: {query}
#                 SQL Query:

#                 Constraints:
#                 - Only use the columns provided in the schema.
#                 - Do not include any explanatory text or markdown, just the SQL query.
#                 - Assume the user wants data from the 'wicketwise.db' database.
#                 """),
#     ("user", "Generate the SQL query for the following request:\n{natural_language_request}\n\nSQL Query:")]
#     return full_prompt
    


# def train_sql_toText(query,schema):
#     docs = [Document(page_content=f"Q: {ex['query']}\nA: {ex['sql']}") for ex in examples]
#     embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key="AIzaSyAmhHkeeHTSSl-B5quRWebacPYsafYYSvM")
#     vector_store = Chroma.from_documents(documents = docs, embedding=embeddings)

#     retriever = vector_store.as_retriever(search_type="similarity", k=3)

#     dynamic_prompt=create_prompt_with_examples_textTOSql(query,schema)
#     prompt = ChatPromptTemplate.from_messages(dynamic_prompt)

#     return prompt









example_query_table_extracter=[
  {
    "query": "Bowlers who have bowled most deliveries",
    "tables": ["Ball_by_Ball", "Player", "Country", "Bowling_Style"]
  },
  {
    "query": "Highest Wicket takers in IPL (Runout, Retired hurt and Obstructing field are not counted as bowlers wicket)",
    "tables": ["Wicket_Taken", "Ball_by_Ball", "Player", "Country", "Bowling_Style"]
  },
  {
    "query": "Highest wicket taken by a bowler in an IPL match",
    "tables": ["Ball_by_Ball", "Wicket_Taken", "Batsman_Scored", "Extra_Runs", "Player", "Country", "Bowling_Style"]
  },
  {
    "query": "No of 5-wicket hauls by bowlers in an IPL",
    "tables": ["Wicket_Taken", "Ball_by_Ball", "Player", "Country", "Bowling_Style"]
  },
  {
    "query": "Most Runs Conceded by a Bowler in an IPL Match",
    "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Player", "Country", "Bowling_Style"]
  },
  {
    "query": "Highest Runs Concede in an IPL over by a bowler",
    "tables": ["Batsman_Scored", "Extra_Runs", "Ball_by_Ball", "Player", "Bowling_Style", "Country", "Venue", "City"]
  },
  {
    "query": "Best economy bowler's in IPL",
    "tables": ["Batsman_Scored", "Ball_by_Ball", "Extra_Runs", "Player", "Bowling_Style", "Country"]
  },
  {
    "query": "Best Death overs Bowler's in Indian Premier League (Wickets_rate= average no of wickets ball in an over)",
    "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Wicket_Taken", "Player", "Country", "Bowling_Style"]
  },
  {
    "query": "Best powerplay overs Bowler's in Indian Premier League(Wickets_rate= average no of wickets ball in an over)",
    "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Wicket_Taken", "Player", "Country", "Bowling_Style"]
  },
  {
    "query": "Best Middle overs Bowler's in Indian Premier League(Wickets_rate= average no of wickets ball in an over)",
    "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Wicket_Taken", "Player", "Country", "Bowling_Style"]
  },
  {
    "query": "Best Bowlers in IPL",
    "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Wicket_Taken", "Player", "Bowling_Style", "Country"]
  },
  {
    "query": "Batsmens who have faced most deliveries",
    "tables": ["Ball_by_Ball", "Player", "Country", "Batting_Style"]
  },
  {
    "query": "Highest run scored by a batsman in an IPL",
    "tables": ["Batsman_Scored", "Ball_by_Ball", "Player", "Country", "Batting_Style"]
  },
  {
    "query": "Player who got dismissed at duck(0 score) highest no of times",
    "tables": ["Ball_by_Ball", "Wicket_Taken", "Batsman_Scored", "Player", "Country", "Batting_Style"]
  },
  {
    "query": "Highest run score by a batsman in an IPL match",
    "tables": ["Ball_by_Ball", "Batsman_Scored", "Player", "Country", "Batting_Style"]
  },
  {
    "query": "No of fifties and centruies by a batsman in an IPL",
    "tables": ["Ball_by_Ball", "Batsman_Scored", "Player", "Country", "Batting_Style"]
  },
  {
    "query": "Power Hitters of IPL",
    "tables": ["Ball_by_Ball", "Batsman_Scored", "Player", "Country", "Batting_Style"]
  },
  {
    "query": "Batsman's with Highest strike rate and batting_average in IPL",
    "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Wicket_Taken", "Player", "Country", "Batting_Style"]
  },
  {
    "query": "Best Batsman's in IPL",
    "tables": ["Ball_by_Ball", "Batsman_Scored", "Extra_Runs", "Wicket_Taken", "Player", "Country", "Batting_Style"]
  },
  {
    "query": "Best Fielders in IPL",
    "tables": ["Wicket_Taken", "Player", "Country"]
  },
  {
    "query": "Best Wicket-Keepers in IPL",
    "tables": ["Wicket_Taken", "Player", "Country"]
  },
  {
    "query": "Most successful captains of IPL",
    "tables": ["Player_Match", "Match", "Team", "Player", "Country"]
  },
  {
    "query": "Best Teams in IPL",
    "tables": ["Match", "Team", "Season"]
  },
  {
    "query": "Best team in defending the score",
    "tables": ["Match", "Team"]
  },
  {
    "query": "Best team in chasing the score",
    "tables": ["Match", "Team"]
  },
  {
    "query": "IPL Season's Best Players",
    "tables": ["Season", "Player"]
  },
  {
    "query": "Runs scored in powerplay,middle and death overs in different seasons of IPL",
    "tables": ["Batsman_Scored", "Match", "Extra_Runs", "Season"]
  },
  {
    "query": "Highest score of a Season",
    "tables": ["Batsman_Scored", "Match", "Extra_Runs", "Season", "Team", "Venue", "City"]
  },
  {
    "query": "Lowest score of a Season",
    "tables": ["Batsman_Scored", "Match", "Extra_Runs", "Season", "Team", "Venue", "City"]
  },
  {
    "query": "IPL Season's Winners,Runners Up, Win Type",
    "tables": ["Match", "Season", "Team"]
  }
]


# def create_prompt_with_examples_tableSelection(query,tables):
#     similar_docs = retriever.get_relevant_documents(query)
#     examples_text = "\n\n".join([doc.page_content for doc in similar_docs])

#     full_prompt =[ ("system",f"""You are a highly skilled SQL expert. prompt = PromptTemplate(
#             input_variables=["query", "tables"],
#             template=(
#                 "You are a data engineering assistant.  "
#                 "Given the user request and the list of available database tables, "
#                 "select which tables are needed to answer the request.  "
#                 "Return **only** a JSON array of table names (e.g. [\"players\",\"matches\"]).\n\n"
#                 "User request:\n{query}\n\n"
#                 "Available tables:\n{tables}"
#             )
#         )
#                 Examples:
#                 {examples_text}

#                 Database Schema:
#                 {schema}

#                 Question: {query}
#                 SQL Query:

#                 Constraints:
#                 - Only use the columns provided in the schema.
#                 - Do not include any explanatory text or markdown, just the SQL query.
#                 - Assume the user wants data from the 'wicketwise.db' database.
#                 """),
#     ("user", "Generate the SQL query for the following request:\n{natural_language_request}\n\nSQL Query:")]
#     return full_prompt


# def RAG_select_database(query,schema):
#     docs = [Document(page_content=f"Q: {ex['query']}\nA: {ex['sql']}") for ex in example_query_table_extracter]
#     embeddings = GoogleGenerativeAIEmbeddings(model="models/text-embedding-004", google_api_key="AIzaSyAmhHkeeHTSSl-B5quRWebacPYsafYYSvM")
#     vector_store = Chroma.from_documents(documents = docs, embedding=embeddings)

#     retriever = vector_store.as_retriever(search_type="similarity", k=3)

#     dynamic_prompt=create_prompt_with_examples_tableSelection(query,schema)
#     prompt = ChatPromptTemplate.from_messages(dynamic_prompt)

#     return prompt
