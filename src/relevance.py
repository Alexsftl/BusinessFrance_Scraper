from .gemini_handler import AllModelsExhausted
import requests
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


def is_relevant(offer, handler, config_dict):
    profile = config_dict["USER_PROFILE"]
    text = offer_text(offer)

    prompt = (
        "You decide if a job offer matches a candidate's profile.\n"
        "Answer with a single word: YES or NO.\n\n"
        "Candidate profile:\n" + profile + "\n\n"
        "Job offer:\n" + text + "\n\n"
        "Does this offer match the profile? Answer YES or NO."
    )

    answer = handler.generate(prompt)
    return answer.strip().upper().startswith("YES")


def filter_relevant(offers, config_dict, handler, save_func=None):
    relevant = {}
    items = list(offers.items())
    total = len(items)
    checked_since_save = 0

    for i, (offer_id, offer) in enumerate(items):
        if offer.get("relevancy_check") != "unchecked":
            continue

        try:
            match = is_relevant(offer, handler, config_dict)
        except AllModelsExhausted:
            log.error("RELEVANCE ERROR - all Gemini models exhausted; stopping run.")
            break
        except Exception as e:
            log.error(f"RELEVANCE ERROR - offer {offer_id}: {e}")
            continue

        if match:
            offer["relevancy_check"] = "relevant"
            relevant[offer_id] = offer
        else:
            offer["relevancy_check"] = "not_relevant"

        log.info(f"Checked offer {i + 1}/{total} ({offer_id}): {offer['relevancy_check']}")

        checked_since_save += 1
        if save_func is not None and checked_since_save >= SAVE_EVERY:
            save_func(offers)
            checked_since_save = 0

    if save_func is not None:
        save_func(offers)

    return relevant