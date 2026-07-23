"""
Pokemon Center Stock Checker
-----------------------------
This is the "robot's brain."

Every time it runs, it does 4 things:
1. Visits each category page you're watching (ETB, Booster Packs, Tins)
2. Reads the list of products on that page
3. Figures out which ones are NOT sold out (i.e. actually buyable)
4. If it finds one it hasn't shouted about before, it sends a Discord alert

It remembers what it already told you about in a file called state.json,
so it won't spam you with the same "in stock" item over and over.
"""

import json
import os
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ---- The pages the robot watches ----
PAGES = {
    "Elite Trainer Box": "https://www.pokemoncenter.com/category/elite-trainer-box",
    "Booster Packs": "https://www.pokemoncenter.com/category/booster-packs",
    "Tins": "https://www.pokemoncenter.com/category/tins",
}

STATE_FILE = Path(__file__).parent / "state.json"

DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

HEADERS = {
    # Pretend to be a normal web browser, not a script
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}


def load_state():
    """Read the list of things we already alerted about."""
    if STATE_FILE.exists():
        return json.loads(STATE_FILE.read_text())
    return {}


def save_state(state):
    """Save the updated list so next run remembers."""
    STATE_FILE.write_text(json.dumps(state, indent=2))


def send_discord_alert(category, product_name, price, url):
    if not DISCORD_WEBHOOK_URL:
        print("No DISCORD_WEBHOOK_URL set, skipping alert (but printing instead):")
        print(f"IN STOCK: [{category}] {product_name} - {price} - {url}")
        return

    message = {
        "content": (
            f"🚨 **IN STOCK** 🚨\n"
            f"**{product_name}**\n"
            f"Category: {category}\n"
            f"Price: {price}\n"
            f"{url}"
        )
    }
    resp = requests.post(DISCORD_WEBHOOK_URL, json=message, timeout=15)
    resp.raise_for_status()


MAX_PAGES = 10  # safety cap so a broken pager can't loop forever


def extract_items_from_page(category, soup):
    """Pull the in-stock product tiles out of one already-fetched page."""
    in_stock_items = []

    candidates = soup.select('[data-testid*="product"], li.product, div.product-tile, article')

    if not candidates:
        candidates = soup.find_all(["li", "div"], limit=500)

    seen_names = set()

    for tile in candidates:
        text = tile.get_text(separator=" | ", strip=True)
        if not text or len(text) > 500:
            continue

        name_tag = tile.find(["h2", "h3", "h4", "a"])
        name = name_tag.get_text(strip=True) if name_tag else None

        if not name or name in seen_names or len(name) < 3:
            continue

        is_sold_out = "sold out" in text.lower() or "unavailable" in text.lower()
        is_coming_soon = "coming soon" in text.lower() or "notify me" in text.lower()

        if not is_sold_out and not is_coming_soon:
            price = ""
            for chunk in text.split(" | "):
                if "$" in chunk:
                    price = chunk
                    break

            seen_names.add(name)
            in_stock_items.append(
                {
                    "name": name,
                    "price": price,
                    "key": f"{category}::{name}",
                }
            )

    return in_stock_items


def find_next_page_url(soup, base_url, page_num):
    """
    Try to figure out the URL for the next page of results.

    First we look for an actual "next page" link in the HTML (most
    reliable). If we can't find one, we fall back to guessing a
    "?page=N" style URL, which is a common pattern for this kind of
    product listing.
    """
    next_link = soup.select_one('a[rel="next"]')
    if not next_link:
        for a in soup.find_all("a"):
            label = a.get_text(strip=True).lower()
            if label in ("next", "next page", "»", ">"):
                next_link = a
                break

    if next_link and next_link.get("href"):
        href = next_link["href"]
        if href.startswith("http"):
            return href
        if href.startswith("/"):
            return "https://www.pokemoncenter.com" + href
        return href

    separator = "&" if "?" in base_url else "?"
    return f"{base_url}{separator}page={page_num}"


def check_category(category, url):
    """
    Fetch ALL pages of a category (following pagination) and return the
    combined list of in-stock products found. Each product is a dict:
    {name, price, key}
    """
    all_items = []
    seen_keys = set()

    current_url = url
    page_num = 1

    while current_url and page_num <= MAX_PAGES:
        resp = requests.get(current_url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        page_items = extract_items_from_page(category, soup)

        new_items = [i for i in page_items if i["key"] not in seen_keys]
        if page_num > 1 and not new_items:
            break

        for item in new_items:
            seen_keys.add(item["key"])
            all_items.append(item)

        next_url = find_next_page_url(soup, url, page_num + 1)
        if next_url == current_url:
            break

        current_url = next_url
        page_num += 1

    return all_items


def main():
    state = load_state()
    new_alerts = 0

    for category, url in PAGES.items():
        try:
            items = check_category(category, url)
        except Exception as e:
            print(f"Error checking {category}: {e}", file=sys.stderr)
            continue

        for item in items:
            key = item["key"]
            if key not in state:
                # New in-stock item we haven't alerted about yet
                send_discord_alert(category, item["name"], item["price"], url)
                state[key] = True
                new_alerts += 1

        # Clean up: remove items from state that are no longer in stock,
        # so if they sell out and come back later, we alert again.
        current_keys = {item["key"] for item in items}
        keys_to_remove = [
            k for k in state
            if k.startswith(f"{category}::") and k not in current_keys
        ]
        for k in keys_to_remove:
            del state[k]

    save_state(state)
    print(f"Done. {new_alerts} new alert(s) sent.")


if __name__ == "__main__":
    main()
