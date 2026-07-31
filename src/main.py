from .config import load_config
from .scraper import scrape_offers, cutoff_date
from .relevance import filter_relevant
from .telegram import send_offers
from .store import load_offers, save_offers, new_offers, delete_old


def run():
    config_dict = load_config()

    since = cutoff_date(config_dict["MAX_DAYS"])

    scraped = scrape_offers(
        config_dict, since=since, batch=config_dict["BATCH_SIZE"]
    )

    stored = load_offers()
    fresh = new_offers(scraped, stored)

    relevant = filter_relevant(fresh, config_dict)

    send_offers(relevant, config_dict)

    merged = {**stored, **fresh}
    merged = delete_old(merged, since=since)
    save_offers(merged)

    print(
        "Run complete: "
        + str(len(fresh))
        + " new offers, "
        + str(len(relevant))
        + " relevant, "
        + str(len(merged))
        + " stored."
    )


if __name__ == "__main__":
    run()