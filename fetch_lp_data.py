import os
import requests
import json
from datetime import datetime, timezone

REGION = "euw1"  # Or euw1, kr, etc.
SUMMONERS = [
    "Nico#coati",
    "Loopy#0004",
    # ... up to 20 or more
]

def main():
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        print("Missing Riot API Key!")
        return

    summoner_data_list = []
    for summ_name in SUMMONERS:
        try:
            puuid = get_puuid(summ_name, api_key)
            if not puuid:
                continue
            ranked_info = get_ranked_data(puuid, api_key)
            if ranked_info:
                # Find solo queue data
                solo_queue = next((q for q in ranked_info if q["queueType"] == "RANKED_SOLO_5x5"), None)
                if solo_queue:
                    summoner_data_list.append({
                        "summonerName": summ_name,
                        "tier": solo_queue["tier"],
                        "rank": solo_queue["rank"],
                        "lp": solo_queue["leaguePoints"],
                        "timestamp": datetime.now(timezone.utc).isoformat()  # Fixed timestamp
                    })
        except Exception as e:
            print(f"Error for {summ_name}: {e}")

    # Load existing data if present
    data_filename = "lp_data.json"
    try:
        with open(data_filename, "r", encoding="utf-8") as f:
            old_data = json.load(f)
    except:
        old_data = []

    # Ensure old_data is a list
    if not isinstance(old_data, list):
        old_data = []

    # Append new data records
    old_data.extend(summoner_data_list)

    # Save back to file
    with open(data_filename, "w", encoding="utf-8") as f:
        json.dump(old_data, f, indent=2)

    print(f"Successfully updated {data_filename} with {len(summoner_data_list)} records.")


def get_puuid(summoner_name, api_key):
    url = f"https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/by-name/{summoner_name}"
    headers = {
        "X-Riot-Token": api_key
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json().get("puuid")
    else:
        print(f"Error {r.status_code} fetching PUUID for {summoner_name}: {r.text}")
        return None

def get_ranked_data(puuid, api_key):
    url = f"https://{REGION}.api.riotgames.com/lol/league/v4/entries/by-summoner/{puuid}"
    headers = {
        "X-Riot-Token": api_key
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()
    else:
        print(f"Error {r.status_code} fetching ranked data: {r.text}")
        return None


if __name__ == "__main__":
    main()
