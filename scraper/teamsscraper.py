#teams data scraper

from bs4 import BeautifulSoup
import requests

soup = BeautifulSoup(open('teams/csk.html', encoding="utf8"), 'html.parser')

players = soup.find("ul", class_="playersList")
link = players.find("li").find('a')['href']
data = requests.get(link)
soup2 = BeautifulSoup(data.text, 'html.parser')
image_link = "https:" + soup2.find("div", class_="player-hero__photo u-hide-tablet").find("img")['src']
image = requests.get(image_link)
print(image_link)

f = open("dhoni.png", "wb")
f.write(image.content)
f.close()
# print(soup2.find("div", class_="player-hero__photo u-hide-tablet").prettify())