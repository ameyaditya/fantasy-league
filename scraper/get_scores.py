from selenium import webdriver
import requests
from bs4 import BeautifulSoup
import sqlite3
import time

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

url = "https://www.iplt20.com/stats/2020/player-points"
team_id_maps = {"Mumbai Indians": 7, "Chennai Super Kings": 1, "Delhi Capitals": 3, "Kings XI Punjab": 6, "Sunrisers Hyderabad": 5, "Royal Challengers Bangalore": 2, "Rajasthan Royals": 4, "Kolkata Knight Riders": 8}
driver = webdriver.Chrome("chromedriver.exe")
driver.get(url)
time.sleep(4)
driver.execute_script("window.scrollTo(0, 300);")
team_name = "Royal Challengers Bangalore"
soup = BeautifulSoup(driver.page_source, "html.parser")
x = driver.find_element_by_xpath('//*[@id="main-content"]/div[2]/div/div/div[2]/div[2]/div[1]').click()
abc = soup.find("div", class_="stats-table__filter drop-down js-drop-down js-teams").find("ul", class_="drop-down__dropdown-list js-drop-down-options").findAll("li")
indx = None
for i in range(len(abc)):
    if team_name == abc[i].text.strip():
        indx = i
        break
time.sleep(2)
driver.find_element_by_xpath(f'//*[@id="main-content"]/div[2]/div/div/div[2]/div[2]/ul/li[{indx + 1}]').click()
time.sleep(4)
soup2 = BeautifulSoup(driver.page_source, "html.parser")
a = soup2.findAll("div", class_="top-players__player-name")
for i in a:
    print(i.text)

# //*[@id="main-content"]/div[2]/div/div/div[2]/div[2]/ul/li[2]