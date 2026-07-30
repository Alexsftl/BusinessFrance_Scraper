from datetime import date, timedelta, datetime
from zoneinfo import ZoneInfo
import requests, json
from config import config_dict


def base_payload(skip, limit=50):
    return {
        "limit": limit,
        "skip": skip,
        "sort": ["0"],
        "activitySectorId": [],
        "companiesSizes": [],
        "countriesIds": [],
        "entreprisesIds": [0],
        "geographicZones": [],
        "missionStartDate": None,
        "missionsDurations": [],
        "missionsTypesIds": [],
        "query": None,
        "specializationsIds": [],
        "studiesLevelId": [],
    }

def sort_offers_by_date(offers, reverse=True):
    return dict(
        sorted(
            offers.items(),
            key=lambda item: datetime.fromisoformat(
                item[1]["startBroadcastDate"]
            ),
            reverse=reverse,
        )
    )

def initialize_up_to_N_days(batch=200, max_days=14):
    today = datetime.now(ZoneInfo("Europe/Paris")).date()
    limit_date = today - timedelta(days=max_days)
    offers = {}


    stop = False
    skip = 0
    it=0
    while not stop:
        it+=1
        try:
            r = requests.post(
                config_dict["SEARCH_URL"],
                json=base_payload(skip=skip, limit=batch),
                headers=config_dict["HEADERS"],
                timeout=30,
            )
            data = r.json().get("result", [])
        except Exception as e:
            raise ValueError(str(e))

        if not data:
            break

        for dic in data:

            startBroadcastDate = datetime.fromisoformat(
                        dic["startBroadcastDate"].replace("Z", "+00:00")
                    ).date()

            if startBroadcastDate < limit_date:
                stop = True
                continue

            offers[str(dic["id"])] = {
                "organizationName": dic.get("organizationName"),
                "missionTitle": dic.get("missionTitle"),
                "cityName": dic.get("cityName"),
                "countryName": dic.get("countryName"),
                "missionDescription": dic.get("missionDescription"),
                "missionProfile": dic.get("missionProfile"),
                "startBroadcastDate": str(startBroadcastDate),
            }

        skip += batch

    offers = sort_offers_by_date(offers)

    return offers
