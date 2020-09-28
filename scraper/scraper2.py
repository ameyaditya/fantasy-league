from selenium import webdriver
from bs4 import BeautifulSoup
import time
import requests
import os

driver = webdriver.Chrome("chromedriver.exe")
team_urls = {"csk": "https://www.iplt20.com/teams/chennai-super-kings", "dc": "https://www.iplt20.com/teams/delhi-capitals", "kxip": "https://www.iplt20.com/teams/kings-xi-punjab", "kkr": "https://www.iplt20.com/teams/kolkata-knight-riders",
             "mi": "https://www.iplt20.com/teams/mumbai-indians", "rr": "https://www.iplt20.com/teams/rajasthan-royals", "rcb": "https://www.iplt20.com/teams/royal-challengers-bangalore", "srh": "https://www.iplt20.com/teams/sunrisers-hyderabad"}


def scrape(url, team_name):
    print(f"Starting {team_name}....")
    os.mkdir("teams/"+team_name)
    driver.get(url)
    time.sleep(10)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    for each_player in soup.find("ul", class_="playersList").find_all("li", recursive=False):
        player_name = each_player.find("p", class_="player-name").text
        player_url = "https://www.iplt20.com" + \
            each_player.find("a", class_="squadPlayerCard")['href']
        driver.get(player_url)
        time.sleep(10)
        s2 = BeautifulSoup(driver.page_source, "html.parser")
        img_src = "https:" + \
            s2.find(
                "div", class_="player-hero__photo u-hide-tablet").find('img')['src']
        img_extension = img_src.split(".")[-1]
        f = open(f"teams/{team_name}/{player_name}.{img_extension}", "wb")
        image_data = requests.get(img_src)
        f.write(image_data.content)
        f.close()
        print(f"Downloaded {player_name}'s photo",
              f"teams/{team_name}/{player_name}.{img_extension}")
    print(f"Done with {team_name}")
    print()


for each_team in team_urls:
    scrape(team_urls[each_team], each_team.upper())
