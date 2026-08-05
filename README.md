# Business France Scraper

Automatically scrapes [Business France VIE](https://mon-vie-via.businessfrance.fr/)
offers, filters them against **your** profile using Google Gemini, and sends
you a Telegram message for each relevant one — running by itself on GitHub
Actions, with a live metrics dashboard.

**No server**, **no code** to write. You fork the repo, add a few settings, and it
runs on a schedule in the cloud.

---

## What it does

Every run, the watcher:

1. **Scrapes** the latest VIE offers from Business France (the last 14 days).
2. **Filters** any offers it hasn't seen before, asking Gemini whether each
   one matches the profile you describe (e.g. *"data scientist: Python, SQL,
   statistics, machine learning"*).
3. **Notifies** you on Telegram about the offers judged relevant — with the
   title, company, location, and a direct link.
4. **Remembers** every offer it has already checked, so you're never notified
   twice, and only genuinely new offers are ever sent.

It runs on weekdays, several times (depends on Github's traffic) between 08:00 and 20:00 Paris time, and
publishes a dashboard tracking how many offers it scraped, how many were
relevant, and whether anything went wrong.

---

## Setup

Everything below is done in your browser and the GitHub settings screens —
there is no code to edit.

### 1. Fork this repository

Click **Fork** (top right of the repo page) to create your own copy. All the
steps below happen in **your** fork.

### 2. Reset the data files

This repo commits its own running data back into itself, so your fresh fork
inherits my offers and run history. Reset both files so
your watcher starts clean and judges offers against *your* profile.

- **`data/offers.json`** — replace the entire contents with exactly:
  ```
  {}
  ```
  (Two characters, not blank)

- **`docs/metrics.jsonl`** — delete all its contents, leaving the file
  completely empty.

You can edit both directly on GitHub (open the file → pencil icon → edit →
commit). This matters because inherited offers already carry a
"checked" verdict and would be skipped; resetting forces every offer to be
re-judged against your own profile.

### 3. Get your API keys and IDs

You need three secret values and one preference:

**Gemini API key** — a free key from
[Google AI Studio](https://aistudio.google.com/apikey). Sign in, create a
key, copy it.

**Telegram bot token** — message [@BotFather](https://t.me/BotFather) on
Telegram, send `/newbot`, follow the prompts, and copy the token it gives you
(looks like `123456:ABC-DEF...`).

**Telegram chat ID** — send any message to your new bot first, then open this
URL in a browser (replacing `<TOKEN>` with your bot token):
```
https://api.telegram.org/bot<TOKEN>/getUpdates
```
Find the `"chat":{"id": ...}` value in the response — that number is your
chat ID. (The bot can't message you until you've messaged it at least once.)

**Your profile** — a description of your profile to match the offers appropriately.
Feel free to make it as detailed as needed based on the relevance of the offers you receive on Telegram.
For example, mine includes:
- degree or educational background
- description of the types of positions I'm looking for
- technical skills
- languages

### 4. Add secrets and your profile to GitHub

In your fork: **Settings → Secrets and variables → Actions**.

Under the **Secrets** tab, add three (**New repository secret**):

| Name                  | Value                        |
|-----------------------|------------------------------|
| `GEMINI_API_KEY`      | your Gemini key              |
| `TELEGRAM_BOT_TOKEN`  | your bot token               |
| `TELEGRAM_CHAT_ID`    | your chat ID                 |

Under the **Variables** tab, add one (**New repository variable**):

| Name               | Value             |
|--------------------|-------------------|
| `USER_DESCRIPTION` | your profile |

### 5. Enable Actions and run the watcher

1. Go to the **Actions** tab. If prompted, click to enable workflows for your
   fork.
2. Select **VIE Watcher** in the left sidebar.
3. Click **Run workflow** to start it manually the first time.

The first run does a full backfill of the last 14 days — it checks several
hundred offers and can take a while (Gemini's free tier is rate-limited, so
the watcher paces itself and may spread the backfill across a couple of runs).
You'll receive Telegram messages for any relevant offers it finds.

After this, it runs on its own — weekdays, roughly hourly, 08:00–20:00 Paris
time — and each later run only checks the handful of new offers since the last
one.

### 6. Enable the dashboard (optional)

To see the metrics dashboard:

1. **Settings → Pages**.
2. Source: **Deploy from a branch**, Branch: `main`, folder: `/docs`, then
   **Save**.
3. After a minute, the page URL appears at the top — something like
   `https://<your-username>.github.io/<repo-name>/`.

---

## Monitoring

**Telegram** — you receive a message per relevant offer, and a "run failed"
alert if a run breaks, so you always know the watcher is alive.

**Dashboard** — the Pages URL shows, per run: new offers scraped, relevant
offers, offers left unchecked, errors, and run time, plus a table of every
run. Open or refresh it any time; it reflects the latest committed data.

**Logs** — for detail on any run, go to the **Actions** tab, click a run, and
expand the steps to see the full log (which offers were checked, any errors,
etc.).

---

## Stopping or pausing the watcher

**Found a job? Pause it:** go to the **Actions** tab → **VIE Watcher** in the
sidebar → the **⋯** menu (or "Disable workflow" button) → **Disable
workflow**. This stops all scheduled runs immediately — no more messages. It's
fully reversible: an **Enable workflow** button appears in the same place if
you want it back later.

**Stop it permanently:** disabling as above is usually enough, but you can
also delete the repository entirely (**Settings → Delete this repository**).

Note: GitHub automatically disables scheduled workflows in public repos after
60 days of no activity, so a forgotten watcher eventually stops on its own.

---

## How it works (for the curious)

- **`src/scraper.py`** — pulls offers from the Business France API, stopping
  once it reaches offers it already knows about.
- **`src/relevance.py`** + **`src/gemini_handler.py`** — ask Gemini to judge
  each new offer, with automatic retries and rotation between Gemini models
  when rate limits are hit.
- **`src/telegram.py`** — formats and sends the notifications.
- **`src/store.py`** — remembers every offer (in `data/offers.json`) so
  nothing is checked or sent twice, and drops offers older than 14 days.
- **`src/metrics.py`** — records one line per run to `docs/metrics.jsonl`,
  which the dashboard reads.
- **`src/main.py`** — ties it together and enforces the weekday/daytime
  schedule.
- **`.github/workflows/watch.yml`** — runs it all on GitHub's servers on a
  schedule and commits the updated data back.

---

## Notes and limitations

- **Gemini free tier** caps daily requests (around 500–1000/day across the
  models used). The one-time backfill can approach this; normal hourly runs
  use very little. If a run hits the limit, it stops cleanly and resumes on
  the next run — no offers are lost.
- **GitHub's scheduler is best-effort.** Scheduled runs can be delayed or
  occasionally skipped under load, so "hourly" is approximate (often closer to 2-3 hours between runs). For catching
  VIE offers this is enough.
- **The Business France API key** in the config is the public one embedded in
  their website — it's the same for everyone and not a secret.
