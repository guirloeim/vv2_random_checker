import os
import requests
import json
from datetime import datetime, timezone

# Configuration
REGION = "euw1"  # Or na1, kr, etc.
PLATFORM_REGION = "europe"  # Use platform routing values like 'americas', 'europe', 'asia', 'sea'
SUMMONERS = [
    "Nico#coati",
    "Loopy#0004",
    "The Mid Game#Canoe",
    "emerrin#623HS",
    "meow81#paw",
    "Owpi#idiot",
    "Big2080#EUW",
    "Myst#Blade",
    "Yui#KEK",
    "Lil Wio#EUW",
    "King Afee#333",
    "Lemis#33310",
    # ... add more Riot IDs (name#tag)
]

def main():
    # Get API key from environment variable
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        print("Missing Riot API Key!")
        return

    # List to store new summoner data
    summoner_data_list = []
    for summoner in SUMMONERS:
        try:
            # Extract name and tag
            name, tag = summoner.split("#")
            summoner_id = get_summoner_id(name, tag, api_key)
            if not summoner_id:
                continue

            # Get ranked data
            ranked_info = get_ranked_data(summoner_id, api_key)
            if ranked_info:
                # Process solo queue data
                solo_queue = next((q for q in ranked_info if q["queueType"] == "RANKED_SOLO_5x5"), None)
                if solo_queue:
                    summoner_data_list.append({
                        "summonerName": summoner,
                        "tier": solo_queue["tier"],
                        "rank": solo_queue["rank"],
                        "lp": solo_queue["leaguePoints"],
                        # Fixed timestamp with timezone-aware datetime
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
        except Exception as e:
            print(f"Error for {summoner}: {e}")

    # Load existing data if present
    data_filename = "lp_data.json"
    try:
        with open(data_filename, "r", encoding="utf-8") as f:
            old_data = json.load(f)
            # Flatten grouped data if it's a dictionary
            if isinstance(old_data, dict):
                old_data = [item for sublist in old_data.values() for item in sublist]
    except:
        old_data = []

    # Ensure old_data is a list
    if not isinstance(old_data, list):
        old_data = []

    # Append new data records
    old_data.extend(summoner_data_list)

    # Group data by summoner name for progression tracking
    grouped_data = {}
    for entry in old_data:
        if isinstance(entry, dict):  # Ensure entry is a dictionary
            name = entry["summonerName"]
            if name not in grouped_data:
                grouped_data[name] = []
            grouped_data[name].append(entry)

    # Save back to file
    with open(data_filename, "w", encoding="utf-8") as f:
        json.dump(grouped_data, f, indent=2)

    print(f"Successfully updated {data_filename} with {len(summoner_data_list)} new records.")


def get_summoner_id(name, tag, api_key):
    # Get PUUID from Riot ID
    url = f"https://{PLATFORM_REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
    headers = {
        "X-Riot-Token": api_key
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        puuid = r.json().get("puuid")
        return get_summoner_id_by_puuid(puuid, api_key)
    else:
        print(f"Error {r.status_code} fetching PUUID for {name}#{tag}: {r.text}")
        return None


def get_summoner_id_by_puuid(puuid, api_key):
    # Get Summoner ID by PUUID
    url = f"https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    headers = {
        "X-Riot-Token": api_key
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json().get("id")
    else:
        print(f"Error {r.status_code} fetching Summoner ID for PUUID {puuid}: {r.text}")
        return None


def get_ranked_data(encrypted_summoner_id, api_key):
    # Get ranked data
    url = f"https://{REGION}.api.riotgames.com/lol/league/v4/entries/by-summoner/{encrypted_summoner_id}"
    headers = {
        "X-Riot-Token": api_key
    }
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()
    else:
        print(f"Error {r.status_code} fetching ranked data for {encrypted_summoner_id}: {r.text}")
        return None


if __name__ == "__main__":
    main()