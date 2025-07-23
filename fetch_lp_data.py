import os
import requests
import json
from datetime import datetime, timezone

# Configuration
REGION = "euw1"  # Or na1, kr, etc.
PLATFORM_REGION = "europe"  # Use platform routing values like 'americas', 'europe', 'asia', 'sea'
SUMMONERS = [
    "Loopy#0004",
    "The Mid Game#Canoe",
    "emerrin#623HS",
    "Wiosna#Seal",
    "Owpi#idiot",
    "Big2080#EUW",
    "Yui#KEK",
    "Lil Wio#EUW",
    "Afee#0301",
    "ASSE ATER84#TASTY",
    "Lexa#LEXA3",
    "run#7 7 7",
    "MumGoBlastCone#BOOM",
    "blueqion#EUW",
    "Dominatrix#VIOLA",
    "inflict#eyes",
]

SUMMONERS_NICK = [
    "Loopy",
    "canoes",
    "Emily",
    "Wiosna",
    "Owpi",
    "Big2080",
    "Yui",
    "Wiowid",
    "Afee",
    "Mental",
    "Lexa",
    "sevan",
    "Nico(smurf)",
    "Blueqion",
    "Viola",
    "itachi",
]

SUMMONERS_NA_NICK = [
    "Feels",
    "FroneZone",
]

REGION_NA = "na1"
PLATFORM_REGION_NA = "americas"
SUMMONERS_NA = [
    "Feels#444",
    "FroneZone#9688",
]

CHALLENGER_CUTOFF = 0
GRANDMASTER_CUTOFF = 0

summoner_data_list = []

import time

def main():
    global CHALLENGER_CUTOFF, GRANDMASTER_CUTOFF

    api_key = os.getenv("RIOT_API_KEY")
    api_key = "RGAPI-3e1a5954-22bc-4d7f-bb43-47740289973c"
    if not api_key:
        print("Missing Riot API Key!")
        return

    # Add delay between API calls
    DELAY = 1.2  # seconds between requests
    
    # [Rest of your existing code...]
    
    for i, summoner in enumerate(SUMMONERS):
        try:
            name, tag = summoner.split("#")
            time.sleep(DELAY)  # Add delay
            summoner_id = get_summoner_id(name, tag, api_key, PLATFORM_REGION, REGION)
            # [Rest of your loop...]
            if not summoner_id:
                continue

            ranked_info = get_ranked_data(summoner_id, api_key, REGION)
            if ranked_info:
                solo_queue = next((q for q in ranked_info if q["queueType"] == "RANKED_SOLO_5x5"), None)
                if solo_queue:
                    adjusted_lp = adjust_lp(solo_queue["tier"], solo_queue["rank"], solo_queue["leaguePoints"])
                    summoner_data_list.append({
                        "summonerName": SUMMONERS_NICK[i],  # <-- Use the same index in SUMMONERS_NICK
                        "tier": solo_queue["tier"],
                        "rank": solo_queue["rank"],
                        "lp": solo_queue["leaguePoints"],
                        "adjustedLP": adjusted_lp,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "region": "EUW"
                    })
        except Exception as e:
            print(f"Error for {summoner}: {e}")

    # --- Changed loop for NA summoners ---
    for i, summoner in enumerate(SUMMONERS_NA):
        try:
            name, tag = summoner.split("#")
            summoner_id = get_summoner_id(name, tag, api_key, PLATFORM_REGION_NA, REGION_NA)
            if not summoner_id:
                continue

            ranked_info = get_ranked_data(summoner_id, api_key, REGION_NA)
            if ranked_info:
                solo_queue = next((q for q in ranked_info if q["queueType"] == "RANKED_SOLO_5x5"), None)
                if solo_queue:
                    adjusted_lp = adjust_lp(solo_queue["tier"], solo_queue["rank"], solo_queue["leaguePoints"])
                    summoner_data_list.append({
                        "summonerName": SUMMONERS_NA_NICK[i],  # <-- Use the same index in SUMMONERS_NA_NICK
                        "tier": solo_queue["tier"],
                        "rank": solo_queue["rank"],
                        "lp": solo_queue["leaguePoints"],
                        "adjustedLP": adjusted_lp,
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "region": "NA"
                    })
        except Exception as e:
            print(f"Error for {summoner}: {e}")

    # Load existing data
    data_filename = "lp_data.json"
    try:
        with open(data_filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            old_data = data.get("summoners", {})
            cutoffs = data.get("cutoffs", {"CHALLENGER": 0, "GRANDMASTER": 0})
    except:
        old_data = {}
        cutoffs = {"CHALLENGER": 0, "GRANDMASTER": 0}

    # Append new data
    for entry in summoner_data_list:
        name = entry["summonerName"]
        if name not in old_data:
            old_data[name] = []
        old_data[name].append(entry)

    # Save updated data with cutoffs
    output_data = {
        "cutoffs": {
            "CHALLENGER": CHALLENGER_CUTOFF,
            "GRANDMASTER": GRANDMASTER_CUTOFF
        },
        "summoners": old_data
    }

    with open(data_filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2)

    print(f"Successfully updated {data_filename} with {len(summoner_data_list)} new records.")


def get_cutoff_lp(tier, api_key):
    """Fetch the cutoff LP for Grandmaster and Challenger."""
    url = f"https://{REGION}.api.riotgames.com/lol/league/v4/{tier.lower()}leagues/by-queue/RANKED_SOLO_5x5"
    headers = {"X-Riot-Token": api_key}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        entries = r.json().get("entries", [])
        if entries:
            return min(entry["leaguePoints"] for entry in entries)
    print(f"Error fetching cutoff for {tier}: {r.text}")
    return 0

def adjust_lp(tier, rank, lp):
    """Calculate LP based on rank cutoffs."""
    if tier == "CHALLENGER":
        return 4000 + lp  # Use Challenger cutoff
    elif tier == "GRANDMASTER":
        return 4000 + lp  # Use Grandmaster cutoff
    elif tier == "MASTER":
        return 4000 + lp               # Master starts at 4000 LP
    else:
        division_points = {"IV": 0, "III": 100, "II": 200, "I": 300}
        rank_base = ["IRON", "BRONZE", "SILVER", "GOLD", "PLATINUM", "EMERALD", "DIAMOND"].index(tier) * 400
        return rank_base + division_points[rank] + lp

from urllib.parse import quote

def get_summoner_id(name, tag, api_key, platform, region):
    """Fetch PUUID from Riot ID."""
    # URL-encode the name and tag to handle special characters
    encoded_name = quote(name)
    encoded_tag = quote(tag)
    
    url = f"https://{platform}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{encoded_name}/{encoded_tag}"
    headers = {"X-Riot-Token": api_key}
    
    try:
        r = requests.get(url, headers=headers)
        print(f"Debug - URL: {url}")  # Debug output
        print(f"Debug - Status: {r.status_code}")  # Debug output
        
        if r.status_code == 200:
            puuid = r.json().get("puuid")
            if puuid:
                return get_summoner_id_by_puuid(puuid, api_key, region, name)
            print("Error: PUUID not found in response")
        else:
            print(f"Error fetching PUUID for {name}/{tag}: HTTP {r.status_code} - {r.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")
    
    return None

def get_summoner_id_by_puuid(puuid, api_key, region, name):
    """Fetch Summoner ID (encryptedSummonerId) using PUUID."""
    url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    headers = {"X-Riot-Token": api_key}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        encrypted_id = r.json().get("puuid")
        return encrypted_id  # Fix: Return 'id' (encryptedSummonerId), not 'puuid'
    print(f"Error fetching Summoner ID for name:{name} PUUID {puuid}: {r.text}")
    return None

import time

def get_ranked_data(encrypted_summoner_id, api_key, region):
    time.sleep(1.2)  # 1.2s delay to stay under rate limits
    url = f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-puuid/{encrypted_summoner_id}"
    headers = {"X-Riot-Token": api_key}
    r = requests.get(url, headers=headers)
    # ... rest of your code ...
    if r.status_code == 200:
        return r.json()
    print(f"Error fetching ranked data for {encrypted_summoner_id}: {r.text}")
    return None

if __name__ == "__main__":
    main()