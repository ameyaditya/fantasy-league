import os
import sqlite3

short_to_long = {"CSK": 1, "RCB": 2, "DC": 3, "RR": 4, "SRH": 5, "KXIP": 6, "MI": 7, "KKR": 8}
DATABASE_PATH = '../webapp/fantasy.db'
def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)
    return conn
i = 1

conn = create_connection(DATABASE_PATH)
c = conn.cursor()
query = """
    INSERT INTO team_member VALUES(?, ?, ?, ?)
"""
for each_team in os.listdir("teams"):
    for each_player in os.listdir("teams/"+each_team):
        member_name = each_player.split(".")[0]
        photo_link = "/static/images/teams/"+each_team+"/"+each_player
        team_id = short_to_long[each_team]
        tuple_to_insert = (i, member_name, photo_link, team_id)
        c.execute(query, tuple_to_insert)
        i += 1
conn.commit()
conn.close()