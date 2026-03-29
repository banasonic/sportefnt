import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def fetch_matches():
    url = "https://www.sporteventz.com/en/"
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    matches = []
    # كل مباراة موجودة داخل عنصر class="event"
    for match in soup.select(".event"):
        teams = match.select_one(".event__teams")
        team1 = teams.select_one(".event__team--home").get_text(strip=True) if teams and teams.select_one(".event__team--home") else ""
        team2 = teams.select_one(".event__team--away").get_text(strip=True) if teams and teams.select_one(".event__team--away") else ""

        time = match.select_one(".event__time").get_text(strip=True) if match.select_one(".event__time") else ""

        channel = match.select_one(".event__channels").get_text(strip=True) if match.select_one(".event__channels") else ""

        logo_tag = match.select_one(".event__logo img")
        logo = logo_tag["src"] if logo_tag else ""

        matches.append({
            "team1": team1,
            "team2": team2,
            "time": time,
            "channel": channel,
            "logo": logo
        })

    data = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "matches": matches
    }

    with open("matches.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    fetch_matches()
