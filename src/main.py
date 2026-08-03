from .config import load_config
from .scraper import scrape_offers, cutoff_date
from .relevance import filter_relevant
from .telegram import send_offers
from .store import load_offers, save_offers, new_offers, delete_old


def run():
    # 0 - Initialization
    config_dict = load_config()

    since = cutoff_date(config_dict["MAX_DAYS"])

    stored = load_offers()

    # 1 - Scraping 
    scraped = scrape_offers(
        config_dict, since=since, stored=stored, batch=config_dict["BATCH_SIZE"]
    )

    fresh = new_offers(scraped, stored)

    merged = {**stored, **fresh}

    # 2 - Relevance
    relevant = filter_relevant(merged, config_dict)


    # 3 - Telegram part
    send_offers(relevant, config_dict)
    
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