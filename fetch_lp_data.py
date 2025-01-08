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
]

# Global cutoff values (will be fetched dynamically)
CHALLENGER_CUTOFF = 0
GRANDMASTER_CUTOFF = 0


def main():
    global CHALLENGER_CUTOFF, GRANDMASTER_CUTOFF

    # Get API key from environment variable
    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        print("Missing Riot API Key!")
        return

    # Fetch cutoff LP values for Challenger and Grandmaster
    CHALLENGER_CUTOFF = get_cutoff_lp("CHALLENGER", api_key)
    GRANDMASTER_CUTOFF = get_cutoff_lp("GRANDMASTER", api_key)

    print(f"Challenger Cutoff: {CHALLENGER_CUTOFF} LP")
    print(f"Grandmaster Cutoff: {GRANDMASTER_CUTOFF} LP")

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
                    # Adjust LP based on cutoffs
                    adjusted_lp = adjust_lp(solo_queue["tier"], solo_queue["rank"], solo_queue["leaguePoints"])
                    summoner_data_list.append({
                        "summonerName": summoner,
                        "tier": solo_queue["tier"],
                        "rank": solo_queue["rank"],
                        "lp": solo_queue["leaguePoints"],
                        "adjustedLP": adjusted_lp,  # Include adjusted LP for plotting
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
        except Exception as e:
            print(f"Error for {summoner}: {e}")

    # Load existing data if present
    data_filename = "lp_data.json"
    try:
        with open(data_filename, "r", encoding="utf-8") as f:
            old_data = json.load(f)
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
    url = f"https://{PLATFORM_REGION}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
    headers = {"X-Riot-Token": api_key}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        puuid = r.json().get("puuid")
        return get_summoner_id_by_puuid(puuid, api_key)
    else:
        print(f"Error {r.status_code} fetching PUUID for {name}#{tag}: {r.text}")
        return None


def get_summoner_id_by_puuid(puuid, api_key):
    url = f"https://{REGION}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    headers = {"X-Riot-Token": api_key}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json().get("id")
    else:
        print(f"Error {r.status_code} fetching Summoner ID for PUUID {puuid}: {r.text}")
        return None


def get_ranked_data(encrypted_summoner_id, api_key):
    url = f"https://{REGION}.api.riotgames.com/lol/league/v4/entries/by-summoner/{encrypted_summoner_id}"
    headers = {"X-Riot-Token": api_key}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()
    else:
        print(f"Error {r.status_code} fetching ranked data for {encrypted_summoner_id}: {r.text}")
        return None


def get_cutoff_lp(tier, api_key):
    """Fetch the LP cutoff for a given tier (Challenger or Grandmaster)."""
    url = f"https://{REGION}.api.riotgames.com/lol/league/v4/{tier.lower()}leagues/by-queue/RANKED_SOLO_5x5"
    headers = {"X-Riot-Token": api_key}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        entries = r.json().get("entries", [])
        if entries:
            # Find the lowest LP in this tier
            return min(entry["leaguePoints"] for entry in entries)
    print(f"Error fetching cutoff for {tier}: {r.text}")
    return 0


def adjust_lp(tier, rank, lp):
    """Adjust LP values based on tier and cutoffs."""
    if tier == "CHALLENGER":
        return 4800 + lp
    elif tier == "GRANDMASTER":
        return 4400 + lp
    elif tier == "MASTER":
        return 4000 + lp
    else:
        return lp


if __name__ == "__main__":
    main()
