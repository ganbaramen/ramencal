import requests
from bs4 import BeautifulSoup
import re
import time
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


def scrape_event_details(url):
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    content = soup.find("div", class_="the-content")
    if content:
        html = str(content)
        html = re.sub(r"<br\s*/?>\s*", "\n", html)
        text_soup = BeautifulSoup(html, "html.parser")
        lines = []
        for elem in text_soup.find_all(["p", "h3", "h4"]):
            text = elem.get_text(strip=True)
            if text and not text.startswith("美味しい水玉 OFFICIAL"):
                lines.append(text.strip())
        return "\n\n".join(lines)
    return ""


def scrape_events():
    response = requests.get(CALENDAR_URL)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    events = []
    for link in soup.find_all("a", href=True):
        href = link["href"]
        if re.match(r"https://oishii\.love/mizutama/live/\d{4}/\d{2}/\d+/?$", href):
            title = link.get("title", "") or str(link.get_text(strip=True))
            if "<br" in title:
                parts = re.split(r"<br\s*/?>", title)
            else:
                parts = [title]

            if parts:
                full_text = BeautifulSoup(parts[0], "html.parser").get_text(strip=True)
                date_match = re.match(
                    r"(\d{4})\.(\d{2})\.(\d{2})\([^)]+\)\s*(.+)", full_text
                )
                if date_match:
                    date_str = f"{date_match.group(1)}-{date_match.group(2)}-{date_match.group(3)}"
                    venue = date_match.group(4).strip()
                    title_text = parts[1].strip() if len(parts) > 1 else ""
                    if date_str:
                        events.append(
                            {
                                "date": date_str,
                                "title": title_text,
                                "venue": venue,
                                "url": href,
                            }
                        )
    return events


def generate_ics(events):
    calendar = icalendar.Calendar()
    calendar.add("prodid", "-//Mizutama Live Calendar//ramencal//")
    calendar.add("version", "2.0")
    calendar.add("x-wr-calname", "美味しい水玉非公式カレンダー")

    for i, event in enumerate(events):
        cal_event = icalendar.Event()
        cal_event.add("uid", f"{event['date']}-{i}@mizutama-cal")
        event_date = date.fromisoformat(event["date"])
        cal_event.add("dtstart", event_date)
        cal_event.add("dtend", event_date)
        cal_event.add("summary", event["title"])
        venue_line = f"{event['venue']}\n" if event.get("venue") else ""
        description = f"{venue_line}{event['title']}\n{event['url']}"
        if event.get("details"):
            description += f"\n\n{event['details']}"
        cal_event.add("description", description)
        cal_event.add("transp", "TRANSPARENT")
        calendar.add_component(cal_event)

    return calendar.to_ical()


def main():
    print("Fetching events from oishii.love/mizutama/live/...")
    events = scrape_events()
    print(f"Found {len(events)} events")

    for event in events:
        time.sleep(2)
        print(f"Fetching details for {event['title']}...")
        event["details"] = scrape_event_details(event["url"])

    ics_content = generate_ics(events)
    OUTPUT_FILE.write_bytes(ics_content)
    print(f"Written to {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
