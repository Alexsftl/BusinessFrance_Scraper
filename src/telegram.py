import requests, json

TELEGRAM_URL = "https://api.telegram.org/bot{token}/sendMessage"

OFFER_BASE_URL = "https://mon-vie-via.businessfrance.fr/offres/{offer_id}"

def escape_html(text):
    if text is None:
        return ""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def format_offer(offer_id, offer):
    title = escape_html(offer.get("missionTitle"))
    org = escape_html(offer.get("organizationName"))
    city = escape_html(offer.get("cityName"))
    country = escape_html(offer.get("countryName"))
    date = escape_html(offer.get("startBroadcastDate"))
    url = OFFER_BASE_URL.format(offer_id=offer_id)

    location = ", ".join(p for p in [city, country] if p)

    lines = [
        "<b>" + title + "</b>",
        org,
        location,
        "Published: " + date,
        url,
    ]
    return "\n".join(line for line in lines if line)


def send_message(text, config_dict):
    url = TELEGRAM_URL.format(token=config_dict["TELEGRAM_BOT_TOKEN"])
    try:
        r = requests.post(
            url,
            json={
                "chat_id": config_dict["TELEGRAM_CHAT_ID"],
                "text": text,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=30,
        )
        r.raise_for_status()
    except Exception as e:
        raise ValueError(str(e))


def send_offer(offer_id, offer, config_dict):
    send_message(format_offer(offer_id, offer), config_dict)


def send_offers(offers, config_dict):
    for offer_id, offer in offers.items():
        send_offer(offer_id, offer, config_dict)