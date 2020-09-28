import requests
from selenium import webdriver
import time
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import sqlite3

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


url = "https://www.cricbuzz.com/cricket-series/3130/indian-premier-league-2020/matches"
# data = requests.get(url)
team_id_maps = {"Mumbai Indians": 7, "Chennai Super Kings": 1, "Delhi Capitals": 3, "Kings XI Punjab": 6, "Sunrisers Hyderabad": 5, "Royal Challengers Bangalore": 2, "Rajasthan Royals": 4, "Kolkata Knight Riders": 8}

driver = webdriver.Chrome("chromedriver.exe")
driver.get(url)
time.sleep(4)
soup = BeautifulSoup(driver.page_source, "html.parser")
table = soup.find("div", class_="cb-bg-white cb-col-100 cb-col cb-hm-rght cb-series-filters")
# print(table.prettify())
date = None
i = 1
conn = create_connection(DATABASE_PATH)
c = conn.cursor()
for each_row in table.find("div", class_="cb-ranking-list").findAll("div", class_="cb-series-matches", recursive=False):
    # print(each_row.prettify())
    # break
    prev_date = date
    date = each_row.find("div", class_="schedule-date").find("span")
    if date is None:
        date = prev_date
    else:
        date = date.text
    match = each_row.find("a", class_="text-hvr-underline").text
    team1, team2 = match.split(",")[0].split(" vs ")

    time = each_row.find("span", class_="schedule-date").text
    processed_datetime = date.split(",")[0] + " 2020 " + time
    obj = datetime.strptime(processed_datetime, "%b %d %Y %I:%M %p")
    deadline = obj - timedelta(minutes=30)
    tuple_to_push = (i, team_id_maps[team1], team_id_maps[team2], obj.strftime("%B %d, %Y %I:%M%p"), deadline.strftime("%B %d, %Y %I:%M%p"))

    query = """
        INSERT INTO ipl_schedule VALUES(?, ?, ?, ?, ?)
    """
    c.execute(query, tuple_to_push)
    print(tuple_to_push)
    i += 1
conn.commit()
