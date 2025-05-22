import sqlite3

def create_connection(db_file):
    """ 
    create a database connection to the SQLite database
    specified by db_file
    
    :param db_file: database file
    :return: Connection object or None
    """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except sqlite3.Error as e:
        print(e)

    return conn


def get_table_schema(table_name, conn):
    """ 
    Get the schema of a table 
    """
    schema = []
    try:
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        return [col[1] for col in columns]
    except sqlite3.Error as e:
        print(e)
    return []

# def get_player_stats(player_name):
#     """
#     Queries the players table for a given player's statistics.
#     """
#     conn = create_connection('wicketwise.db')
#     stats = None
#     if conn:
#         try:
#             cursor = conn.cursor()
#             cursor.execute("SELECT * FROM players WHERE name=?", (player_name,))
#             stats = cursor.fetchone()
#         except sqlite3.Error as e:
#             print(e)
#         finally:
#             conn.close()
#     return stats

# def get_match_details(match_id):
#     """
#     Queries the matches table for a given match's details.
#     """
#     conn = create_connection('wicketwise.db')
#     details = None
#     if conn:
#         try:
#             cursor = conn.cursor()
#             cursor.execute("SELECT * FROM matches WHERE match_id=?", (match_id,))
#             details = cursor.fetchone()
#         except sqlite3.Error as e:
#             print(e)
#         finally:
#             conn.close()
#     return details

# def get_team_info(team_name):
#     """
#     Placeholder function to get team information.
#     Implement database query for team info here.
#     """
#     print(f"Placeholder: Getting info for team: {team_name}")
#     return None

# def get_historical_data(query_params):
#     """
#     Placeholder function to get historical data based on parameters.
#     Implement complex database queries for historical data here.
#     """
#     print(f"Placeholder: Getting historical data with params: {query_params}")
#     return None

# def get_match_details_between_teams(team1_name, team2_name, conn):
#     """
#     Queries the matches table for details of matches played between two teams.
#     """
#     matches = []
#     try:
#         cursor = conn.cursor()
#         # Assuming 'team1' and 'team2' columns in 'matches' table store team names
#         # And we need to cover both team1 vs team2 and team2 vs team1 matches
#         cursor.execute("""
#             SELECT * FROM matches
#             WHERE (team1 = ? AND team2 = ?) OR (team1 = ? AND team2 = ?)
#         """, (team1_name, team2_name, team2_name, team1_name))
#         matches = cursor.fetchall()
#     except sqlite3.Error as e:
#         print(e)
#     return matches

# Add other database interaction functions as needed for your agents

