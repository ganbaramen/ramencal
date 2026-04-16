import requests
from bs4 import BeautifulSoup
import re
from datetime import date
import icalendar
from pathlib import Path

CALENDAR_URL = "https://oishii.love/mizutama/live/"
OUTPUT_FILE = Path("mizutama-live.ics")


def parse_date(date_str):
    match = re.match(r"(\d{4})\.(\d{2})\.(\d{2})", date_str)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    return None


def scrape_events():
    response = requests.get(CALENDAR_URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    events = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if "/live/20" in href and href != CALENDAR_URL:
            parts = [str(p).strip() for p in link.stripped_strings]
            if len(parts) >= 2:
                full_text = parts[0]
                date_match = re.match(
                    r"(\d{4}\.\d{2}\.\d{2})\([^)]+\)\s*(.+)", full_text
                )
                if date_match:
                    date_str = parse_date(date_match.group(1))
                    venue = date_match.group(2).strip()
                    title = parts[1] if len(parts) > 1 else ""
                url = href if href.startswith("http") else f"https://oishii.love{href}"
                if date_str:
                    events.append(
                        {"date": date_str, "title": title, "venue": venue, "url": url}
                    )
    return events


def generate_ics(events):
    calendar = icalendar.Calendar()
    calendar.add("prodid", "-//Mizutama Live Calendar//oishii.love//")
    calendar.add("version", "2.0")
    calendar.add("x-wr-calname", "水玉 Live")

    for i, event in enumerate(events):
        cal_event = icalendar.Event()
        cal_event.add("uid", f"{event['date']}-{i}@mizutama-cal")
        event_date = date.fromisoformat(event["date"])
        cal_event.add("dtstart", event_date)
        cal_event.add("dtend", event_date)
        cal_event.add("summary", event["title"])
        venue_line = f"{event['venue']}\n" if event.get("venue") else ""
        cal_event.add("description", f"{venue_line}{event['title']}\n{event['url']}")
        cal_event.add("transp", "TRANSPARENT")
        calendar.add_component(cal_event)

    return calendar.to_ical()


def main():
    print("Fetching events from oishii.love/mizutama/live/...")
    events = scrape_events()
    print(f"Found {len(events)} events")

    ics_content = generate_ics(events)
    OUTPUT_FILE.write_bytes(ics_content)
    print(f"Written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
