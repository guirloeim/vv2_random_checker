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
    "meow81#paw",
    "Owpi#idiot",
    "Big2080#EUW",
    "Yui#KEK",
    "Lil Wio#EUW",
    "Afee#0301",
    "FOOTQUEEN69#QU33N",
    "MENTALB00MXDD#EUW",
    "run#7 7 7",
    "dingo#gday",
    "blueqion#EUW",
    "Dominatrix#VIOLA",
    "VeigarV2SmurfAcc#123",
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
    "Mental(smurf)",
    "sevan",
    "Nico(smurf)",
    "Blueqion",
    "Viola",
    "veigarv2",
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

def main():
    global CHALLENGER_CUTOFF, GRANDMASTER_CUTOFF

    api_key = os.getenv("RIOT_API_KEY")
    if not api_key:
        print("Missing Riot API Key!")
        return

    # Fetch cutoff LP values dynamically
    CHALLENGER_CUTOFF = get_cutoff_lp("CHALLENGER", api_key)
    GRANDMASTER_CUTOFF = get_cutoff_lp("GRANDMASTER", api_key)

    print(f"Challenger Cutoff: {CHALLENGER_CUTOFF} LP")
    print(f"Grandmaster Cutoff: {GRANDMASTER_CUTOFF} LP")

    # Collect summoner data
    summoner_data_list = []

    # --- Changed loop for EUW summoners ---
    for i, summoner in enumerate(SUMMONERS):
        try:
            name, tag = summoner.split("#")
            summoner_id = get_summoner_id(name, tag, api_key, PLATFORM_REGION, REGION)
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

def get_summoner_id(name, tag, api_key, platform, region):
    """Fetch PUUID from Riot ID."""
    url = f"https://{platform}.api.riotgames.com/riot/account/v1/accounts/by-riot-id/{name}/{tag}"
    headers = {"X-Riot-Token": api_key}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        puuid = r.json().get("puuid")
        return get_summoner_id_by_puuid(puuid, api_key, region, name)
    print(f"Error fetching PUUID for {name}#{tag}: {r.text}")
    return None

def get_summoner_id_by_puuid(puuid, api_key, region, name):
    """Fetch Summoner ID using PUUID."""
    url = f"https://{region}.api.riotgames.com/lol/summoner/v4/summoners/by-puuid/{puuid}"
    headers = {"X-Riot-Token": api_key}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json().get("id")
    print(f"Error fetching Summoner ID for name:{name} PUUID {puuid}: {r.text}")
    return None

def get_ranked_data(encrypted_summoner_id, api_key, region):
    """Fetch ranked data for a given Summoner ID."""
    url = f"https://{region}.api.riotgames.com/lol/league/v4/entries/by-summoner/{encrypted_summoner_id}"
    headers = {"X-Riot-Token": api_key}
    r = requests.get(url, headers=headers)
    if r.status_code == 200:
        return r.json()
    print(f"Error fetching ranked data for {encrypted_summoner_id}: {r.text}")
    return None

if __name__ == "__main__":
    main()