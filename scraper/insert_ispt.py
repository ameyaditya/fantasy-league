import sqlite3
from pprint import PrettyPrinter

p = PrettyPrinter()

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
conn = create_connection(DATABASE_PATH)
conn.row_factory = dict_factory
c = conn.cursor()
query = """
    SELECT schedule_ID, member_ID, member_name, i.team1_ID FROM ipl_schedule i, team_member t1 WHERE i.team1_ID = t1.team_ID UNION SELECT schedule_ID, member_ID, member_name, i.team1_ID FROM ipl_schedule i, team_member t1 WHERE i.team2_ID = t1.team_ID
"""
query2 = """
    INSERT INTO ipl_scheduled_points(schedule_ID, member_ID) VALUES(?, ?)
"""
res = c.execute(query).fetchall()
for row in res:
    c.execute(query2, (row['schedule_ID'], row['member_ID']))
p.pprint(res)

conn.commit()
conn.close()