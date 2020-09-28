from flask import Flask, render_template, jsonify, request, session, redirect
import sqlite3
import database_operations as dbop
import time
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = "fantasy_league"
DATABASE_PATH = 'fantasy.db'


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


def create_tables():
    user_table = """
        CREATE TABLE IF NOT EXISTS user(
            user_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            password TEXT,
            activated INTEGER DEFAULT 0,
            points REAL DEFAULT 0.0,
            deleted INTEGER DEFAULT 0,
            current_bet_ID DEFAULT NULL 
        )
    """
    team_table = """
        CREATE TABLE IF NOT EXISTS team(
            team_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            team_name TEXT,
            team_code TEXT
        )
    """

    team_members_table = """
        CREATE TABLE IF NOT EXISTS team_member(
            member_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            member_name TEXT,
            photo_link TEXT,
            team_ID INTEGER REFERENCES team(team_ID)
        )
    """

    ipl_schedule_table = """
        CREATE TABLE IF NOT EXISTS ipl_schedule(
            schedule_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            team1_ID INTEGER REFERENCES team(team_ID),
            team2_ID INTEGER REFERENCES team(team_ID),
            scheduled_date DATETIME,
            deadline DATETIME
        )
    """

    ipl_scheduled_points_table = """
        CREATE TABLE IF NOT EXISTS ipl_scheduled_points(
            ISP_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            schedule_ID INTEGER REFERENCES ipl_schedule(schedule_ID),
            member_ID INTEGER REFERENCES team_member(member_ID),
            points REAL DEFAULT 0.0
        )
    """

    bet_table = """
        CREATE TABLE IF NOT EXISTS bet(
            bet_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            user_ID INTEGER REFERENCES user(user_ID),
            schedule_ID INTEGER REFERENCES ipl_schedule(schedule_ID),
            for_team_ID INTEGER REFERENCES team(team_ID),
            placed_at DATETIME,
            points_won REAL DEFAULT 0.0
        )
    """

    bet_on_person_table = """
        CREATE TABLE IF NOT EXISTS bet_on_person(
            bp_ID INTEGER PRIMARY KEY AUTOINCREMENT,
            bet_ID INTEGER REFERENCES bet(bet_ID),
            member_id INTEGER REFERENCES team_member(member_ID)
        )
    """
    conn = create_connection(DATABASE_PATH)
    conn.row_factory = dict_factory
    c = conn.cursor()
    c.execute(user_table)
    c.execute(team_table)
    c.execute(team_members_table)
    c.execute(ipl_schedule_table)
    c.execute(ipl_scheduled_points_table)
    c.execute(bet_table)
    c.execute(bet_on_person_table)
    conn.commit()
    conn.close()

create_tables()
@app.route('/')
def login_page():
    return render_template('index.html')


@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/home')
def home_page():
    if "user_id" not in session:
        return render_template("index.html")
    return render_template('home.html')

@app.route('/bet')
def bet_page():
    if "user_id" not in session:
        return render_template("index.html")
    return render_template('bet.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')
######AJAX CALLS#########
@app.route("/login_ajax", methods=['POST'])
def login_user():
    data = request.get_json()
    print(data['username'], data['password'])
    resp = dbop.check_login(data)
    if resp['status_code'] == 200:
        session['user_id'] = resp['user_id']
        session['username'] = resp['username']
    return jsonify(resp)

@app.route("/signup_ajax", methods=['POST'])
def signup_user():
    data = request.get_json()
    resp = dbop.signup_user(data)
    return jsonify(resp)

@app.route('/home_ajax', methods=['POST'])
def home_ajax():
    resp = dbop.get_home_data(session['user_id'])
    return jsonify(resp)

@app.route('/verify_bet_ajax', methods=['POST'])
def verify_bet_ajax():
    data = request.get_json()
    resp = dbop.verify_bet_ajax(session['user_id'], data['schedule_id'])
    return jsonify(resp)

@app.route('/get_players_ajax', methods=['POST'])
def get_players_ajax():
    data = request.get_json()
    resp = dbop.get_players(session['user_id'], data['team_code'])
    return jsonify(resp)

@app.route('/place_bet_ajax', methods=['POST'])
def place_bet_ajax():
    print(session)
    data = request.get_json()
    resp = dbop.place_bet(session['user_id'], data)
    return jsonify(resp)

@app.route('/get_leaderboard_ajax', methods=['POST'])
def leaderboard_ajax():
    data = request.get_json()
    resp = dbop.leaderboard(data)
    return jsonify(resp)

@app.route('/verify_can_bet_ajax', methods=['POST'])
def verify_can_bet():
    data = request.get_json()
    resp = dbop.verify_can_bet(session['user_id'], data)
    return jsonify(resp)

@app.route('/activate_user', methods=['GET'])
def activate_user():
    password = request.args.get('password', None)
    username = request.args.get('username', None)
    if username is None:
        return jsonify({"status_code": 600, "status_message": "BAD REQUEST"})
    if password is None or password != "anirudhamey":
        return jsonify({"status_code": 404, "status_message": "PASSWORD INCORRECT"})
    conn = create_connection(DATABASE_PATH)
    conn.row_factory = dict_factory
    c = conn.cursor()
    query = """
        UPDATE user SET activated = 1 WHERE username = ?
    """
    c.execute(query, (username, ))
    conn.commit()
    conn.close()
    return jsonify({"status_code": 200, "status_message": "USER ACTIVATED"})

@app.route('/get_data_from_ipl_website', methods=['GET'])
def get_ipl_data():
    data = request.args.get('data')
    conn = create_connection(DATABASE_PATH)
    conn.row_factory = dict_factory
    c = conn.cursor()
    url = "https://www.iplt20.com/stats/2020/player-points"
    data = requests.get(url)
    soup = BeautifulSoup(data.text, "html.parser")
    table = soup.find("table", class_="table table--scroll-on-tablet top-players")
    query = """
        SELECT schedule_ID,  t1.team_code AS team1, t2.team_code AS team2 FROM ipl_schedule ip, team t1, team t2 WHERE active = 1 AND t1.team_ID = ip.team1_ID AND t2.team_ID = ip.team2_ID
    """
    schedule_ids = c.execute(query).fetchall()
    player_points_arr = []
    for each_row in table.findAll("tr", class_="js-row"):
        player_name = each_row.find('div', class_="top-players__player-name").text.strip()
        player_name = re.sub("\n+", " ", player_name)
        player_name = re.sub(" +", " ", player_name)
        points = each_row.find("td", class_="top-players__pts").text.strip()
        # team = each_row['class'][1].strip()
        team = each_row.find("div", class_="top-players__team").find("span")['class']
        team = [i for i in team if "logo" not in i.lower()][0]
        # print(each_row['class'])
        # break
        # c.execute(query, (points, player_name))
        player_points_arr.append((player_name, points, team))
    query2 = """
        UPDATE ipl_scheduled_points SET points = ? WHERE ISP_ID = ?
    """
    query3 = """
        SELECT t.points AS points, ip.ISP_ID FROM team_member t, ipl_scheduled_points ip WHERE member_name = ? AND ip.member_ID = t.member_ID AND schedule_ID = ?
    """
    for each_schedule in schedule_ids:
        schedule_id = each_schedule['schedule_ID']
        teams = [each_schedule['team1'], each_schedule['team2']]
        for player_name, points, team in player_points_arr:
            if team not in teams:
                continue
            print(player_name, points)
            data = c.execute(query3, (player_name, schedule_id)).fetchone()
            print(data)
            updated_points = float(points) - float(data['points'])
            c.execute(query2, (updated_points, data['ISP_ID']))
    conn.commit()  
    return jsonify({"response": "SUCCESSFUL"})

@app.route('/update_bets_table', methods=['GET'])
def update_bet_table():
    conn = create_connection(DATABASE_PATH)
    conn.row_factory = dict_factory
    c = conn.cursor()
    query = """
        SELECT schedule_ID,  t1.team_code AS team1, t2.team_code AS team2, won, ip.scheduled_date FROM ipl_schedule ip, team t1, team t2 WHERE active = 1 AND t1.team_ID = ip.team1_ID AND t2.team_ID = ip.team2_ID
    """
    query2 = """
        SELECT * FROM bet WHERE schedule_ID = ?
    """
    query3 = """
        SELECT SUM(ip.points) AS points, b.bet_ID FROM ipl_scheduled_points ip, bet b, bet_on_person bp WHERE ip.schedule_ID = ? AND ip.schedule_ID = b.schedule_ID AND b.bet_ID = ? AND b.bet_ID = bp.bet_iD AND bp.member_ID = ip.member_ID GROUP BY b.bet_ID
    """
    query4 = """
        UPDATE bet SET points_won = ? WHERE bet_ID = ?
    """
    query5 = """
        UPDATE user SET points = points + ? WHERE user_ID = ?
    """
    query6 = """
        UPDATE ipl_schedule SET active = 0 WHERE schedule_ID = ?
    """
    query7 = """
        UPDATE ipl_schedule SET active = 1 WHERE scheduled_date LIKE ?
    """
    schedule_ids = c.execute(query).fetchall()
    for each_schedule in schedule_ids:
        schedule_id = each_schedule['schedule_ID']
        teams = [each_schedule['team1'], each_schedule['team2']]
        team_won = each_schedule['won']
        if team_won is None:
            continue
        res2 = c.execute(query2, (schedule_id, )).fetchall()
        # print(res2)
        for each_bet in res2:
            if each_bet['for_team_ID'] != team_won:
                continue
            res3 = c.execute(query3, (schedule_id, each_bet['bet_ID'])).fetchone()
            print(res3)
            c.execute(query4, (res3['points'], each_bet['bet_ID']))
            c.execute(query5, (res3['points'], each_bet['user_ID']))
        c.execute(query6, (schedule_id, ))
        next_date = (datetime.strptime(each_schedule['scheduled_date'], "%B %d, %Y %I:%M%p") + timedelta(days=1)).strftime("%B %d, %Y") + "%"
        c.execute(query7, (next_date, ))
    conn.commit()
    return jsonify({"response": "SUCCESSFUL"})
@app.route('/active_schedule')
def active_schedule():
    conn = create_connection(DATABASE_PATH)
    conn.row_factory = dict_factory
    c = conn.cursor()
    query = """
        SELECT i.schedule_ID, t1.team_name AS team1, t1.team_ID AS team1_ID, t2.team_name AS team2, t2.team_ID AS team2_ID FROM ipl_schedule i, team t1, team t2 WHERE i.team1_ID = t1.team_ID AND i.team2_ID = t2.team_ID AND i.active = 1
    """
    res = c.execute(query).fetchall()
    return jsonify({"data": res})

@app.route('/update_winners')
def update_winners():
    password = request.args.get('password', None)
    team_id = request.args.get('team_id', None)
    schedule_id = request.args.get('schedule_id', None)
    if password != "anirudhamey":
        return {"status_code": 600, "status_code": "Unsuccessful", "error": "RESTRICTED ACCESS"}
    if team_id is None or schedule_id is None:
        return {"status_code": 600, "status_code": "Unsuccessful", "error": "BAD REQUEST"} 
    conn = create_connection(DATABASE_PATH)
    conn.row_factory = dict_factory
    c = conn.cursor()
    query = """
        UPDATE ipl_schedule SET won = ? WHERE schedule_ID = ?
    """
    c.execute(query, (team_id, schedule_id))
    conn.commit()
    conn.close()
if __name__ == "__main__":
    app.run(debug=True)
