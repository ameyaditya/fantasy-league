import sqlite3
from datetime import datetime, timedelta
import os
import random
from sqlite3 import Error

DATABASE_PATH = '/home/nngfantasy/mysite/fantasy.db'

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

def check_login(data):
    conn = create_connection(DATABASE_PATH)
    conn.row_factory = dict_factory
    c = conn.cursor()
    query = """
        SELECT *FROM user WHERE username = ? AND password = ?
    """
    res = c.execute(query, (data['username'], data['password'])).fetchone()
    conn.close()
    if res is not None:
        if res['activated'] == 0:
            return {"status_code": 404, "status_message": "Unsuccessful", "error": "Username not activated"}
        return {"status_code": 200, "status_message": "Successful", "user_id": res['user_ID'], "username": res['username']}
    return {"status_code": 404, "status_message": "Unsuccessful", "error": "Username or Password Incorrect"}

def signup_user(data):
    random_icon_ID = random.randint(1, 62)
    conn = create_connection(DATABASE_PATH)
    c = conn.cursor()
    query = """
        INSERT INTO user(username, password, icon_ID) VALUES(?, ?, ?)
    """
    query2 = """
        SELECT *FROM user WHERE username = ?
    """
    res = c.execute(query2, (data['username'], )).fetchall()
    if len(res) > 0:
        return {"status_code": 404, "status_message": "unsuccessful", "error": "Username already exists"}
    try:
        c.execute(query, (data['username'], data['password'], random_icon_ID))
        conn.commit()
        return {"status_code": 200, "status_message": "Successful"}
    except Exception as e:
        return {"status_code": 404, "status_message": "unsuccessful", "error": str(e)}

def get_home_data(user_id):
    conn = create_connection(DATABASE_PATH)
    conn.row_factory = dict_factory
    c = conn.cursor()
    time_now = datetime.now() + timedelta(hours=5, minutes =30)
    string_now = (time_now - timedelta(hours=4)).strftime("%B %d, %Y") + "%"
    string_now_with_time = (time_now - timedelta(hours=4)).strftime("%B %d, %Y %I:%M%p")
    query = """
        SELECT i.schedule_ID AS schedule_ID, t1.team_name AS team1_name, t1.team_code AS team1_code, t2.team_name AS team2_name, t2.team_code AS team2_code, i.deadline FROM ipl_schedule i, team t1, team t2 WHERE scheduled_date LIKE ? AND t1.team_ID = i.team1_ID AND t2.team_ID = i.team2_ID
    """
    query2 = """
        SELECT  t.team_code, m.member_name FROM bet b, team t, team_member m, bet_on_person bp WHERE b.schedule_ID = ? AND b.user_ID = ? AND t.team_ID = b.for_team_ID AND b.bet_ID = bp.bet_ID AND bp.member_ID = m.member_ID
    """
    res = c.execute(query, (string_now,)).fetchall()
    for i in range(len(res)):
        deadline_time = datetime.strptime(res[i]['deadline'], "%B %d, %Y %I:%M%p")
        if deadline_time < time_now:
            res[i]['finished'] = True
        else:
            res[i]['finished'] = False
        res2 = c.execute(query2, (res[i]['schedule_ID'], user_id)).fetchall()
        if len(res2)>0:
            res[i] = {"data": res2}
            res[i]['placed'] = True
        else:
            res[i]['placed'] = False
    print(res)
    conn.close()
    return {"status_code": 200, "status_message": "Successful", "data": res}

def verify_bet_ajax(user_id, schedule_id):
    conn = create_connection(DATABASE_PATH)
    conn.row_factory = dict_factory
    c = conn.cursor()
    time_now = datetime.now() + timedelta(hours=5, minutes =30)
    string_now_with_time = time_now.strftime("%B %d, %Y %I:%M%p")
    query = """SELECT i.schedule_ID AS schedule_id, t1.team_name AS team1_name, t1.team_code AS team1_code, t2.team_name AS team2_name, t2.team_code AS team2_code, i.deadline FROM ipl_schedule i, team t1, team t2 WHERE t1.team_ID = i.team1_ID AND t2.team_ID = i.team2_ID AND i.schedule_ID = ?
    """
    res = c.execute(query, (schedule_id, )).fetchone()
    if res is None or datetime.strptime(res['deadline'], "%B %d, %Y %I:%M%p") < time_now:
        return {"status_code": 500, "status_message": "unsuccessful", "error": "deadline passed or invalid schedule ID"}
    return {"status_code": 200, "status_message": "successful", "data": res}

def get_players(user_id, team_code):
    return_data = []
    team_code = team_code.upper()
    for each_name in os.listdir(f"static/images/teams/{team_code}"):
        return_data.append([f"/static/images/teams/{team_code}/{each_name}", each_name.split(".")[0]])
    return {"status_code": 200, "status_message": "successful", "data": return_data}

def place_bet(user_id, data):
    print(user_id)
    conn = create_connection(DATABASE_PATH)
    conn.row_factory = dict_factory
    c = conn.cursor()
    query = """
        SELECT *FROM bet WHERE user_ID = ? AND schedule_ID = ?
    """
    res = c.execute(query, (user_id, data['schedule_id'])).fetchone()
    if res:
        return {"status_code": 500, "status_message": "unsuccessful", "error": "Already placed"}
    time_now = datetime.now() + timedelta(hours=5, minutes =30)
    string_now_with_time = time_now.strftime("%B %d, %Y %I:%M%p")
    query = """
        SELECT *FROM ipl_schedule WHERE schedule_ID = ? AND deadline > ?
    """
    res = c.execute(query, (data['schedule_id'], string_now_with_time)).fetchone()
    if res is None:
        return {"status_code": 500, "status_message": "unsuccessful", "error": "Deadline is crossed"}
    query = """
        SELECT team_ID FROM team WHERE team_code = ?
    """
    team_id = c.execute(query, (data['team'], )).fetchone()['team_ID']
    query = """
        INSERT INTO bet(user_ID, schedule_ID, for_team_ID, placed_at) VALUES(?, ?, ?, ?)
    """
    c.execute(query, (user_id, data['schedule_id'], team_id, string_now_with_time))
    conn.commit()
    bet_id = c.lastrowid
    query = """
        SELECT member_ID from team_member WHERE member_name = ?
    """
    query2 = """
        INSERT INTO bet_on_person(bet_ID, member_ID) VALUES(?, ?)
    """
    for names in data['players']:
        member_id = c.execute(query, (names, )).fetchone()['member_ID']
        c.execute(query2, (bet_id, member_id))
    conn.commit()
    return {"status_code": 200, "status_message": "successful"}

def leaderboard(data):
    conn = create_connection(DATABASE_PATH)
    conn.row_factory = dict_factory
    c = conn.cursor()
    query = """
        SELECT *FROM user ORDER BY points DESC
    """
    res = c.execute(query).fetchall()
    conn.close()
    return {"status_code": 200, "status_message": "successful", "data": res}

def verify_can_bet(user_id, data):
    conn = create_connection(DATABASE_PATH)
    conn.row_factory = dict_factory
    c = conn.cursor()
    query = """
        SELECT *FROM bet WHERE user_ID = ? AND schedule_ID = ?
    """
    res = c.execute(query, (user_id, data['schedule_id'])).fetchone()
    if res:
        return {"status_code": 400, "status_message": "unsuccessful"}
    conn.close()
    return {"status_code": 200, "status_message": "successful"}