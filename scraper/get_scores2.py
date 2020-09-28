from selenium import webdriver
import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import re

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
url = "https://www.iplt20.com/stats/2020/player-points"
# driver = webdriver.Chrome("chromedriver.exe")
# driver.get(url)
time.sleep(4)
data = requests.get(url)
# soup = BeautifulSoup(driver.page_source, "html.parser")
soup = BeautifulSoup(data.text, "html.parser")

table = soup.find("table", class_="table table--scroll-on-tablet top-players")
query = """
    UPDATE team_member SET points = ? WHERE member_name = ?
"""
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
    print(player_name, points, team)
# conn.commit()
conn.close()
# driver.close()