import requests, json
import time
import logging

log = logging.getLogger(__name__)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GEMINI_MAX_RETRIES = 5
GEMINI_WAIT = 4
SAVE_EVERY = 10

def offer_text(offer):
    parts = [
        offer.get("missionTitle"),
        offer.get("missionDescription"),
        offer.get("missionProfile"),
        offer.get("organizationName"),
    ]
    return "\n".join(p for p in parts if p)



def is_relevant_llm(offer, config_dict):
    profile = config_dict["USER_PROFILE"]
    text = offer_text(offer)

    prompt = (
        "You decide if a job offer matches a candidate's profile.\n"
        "Answer with a single word: YES or NO.\n\n"
        "Candidate profile:\n" + profile + "\n\n"
        "Job offer:\n" + text + "\n\n"
        "Does this offer match the profile? Answer YES or NO."
    )

    url = GEMINI_URL.format(model="gemini-3.1-flash-lite")

    r = requests.post(
        url,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": config_dict["GEMINI_API_KEY"],
        },
        json={"contents": [{"parts": [{"text": prompt}]}]},
        timeout=30,
    )

    r.raise_for_status()

    data = r.json()
    answer = data["candidates"][0]["content"]["parts"][0]["text"]

    return answer.strip().upper().startswith("YES")



def filter_relevant(offers, config_dict, save_func=None):
    relevant = {}
    items = list(offers.items())
    total = len(items)
    checked_since_save = 0

    for i, (offer_id, offer) in enumerate(items):
        
        if offer.get("relevancy_check") != "unchecked":
            continue

        match = None

        for attempt in range(GEMINI_MAX_RETRIES):
            try:
                match = is_relevant_llm(offer, config_dict)
                break
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    match = None
                    log.warning(f"RELEVANCE WARNING - Gemini rate limit hit, waiting {GEMINI_WAIT}s (retry {attempt + 1}/{GEMINI_MAX_RETRIES})...")
                    time.sleep(GEMINI_WAIT)
                    continue
            except Exception as e:
                match = None
                log.error(f"RELEVANCE ERROR - failed to send offer {offer_id}: {e}")
                time.sleep(GEMINI_WAIT)
                continue

        if match is None:
            log.error(f"RELEVANCE ERROR - failed to send offer {offer_id}: {e}")
            continue
        elif match:
            offer["relevancy_check"] = "relevant"
            relevant[offer_id] = offer
        else:
            offer["relevancy_check"] = "not_relevant"

        log.info(f"Checked offer {i + 1}/{total} ({offer_id}): {offer['relevancy_check']}")

        checked_since_save += 1
        if save_func is not None and checked_since_save >= SAVE_EVERY:
            save_func(offers)
            checked_since_save = 0

        if i < total - 1:
            time.sleep(GEMINI_WAIT)

    if save_func is not None:
        save_func(offers)

    return relevant