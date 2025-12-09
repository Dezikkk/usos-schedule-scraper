import re
import json
import argparse
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

TYPES = {"W": "Wykład", "K": "Konwersatorium", "LB": "Laboratorium",
         "A": "Audytorium", "C": "Ćwiczenia", "S": "Seminarium", "P": "Projekt",
         "WYK": "Wykład", "CWA": "Ćwiczenia audytoryjne", "CW": "Ćwiczenia"}


def get_week_date(offset: int = 0) -> str:
    today = datetime.now()
    monday = today - timedelta(days=today.weekday())
    target = monday + timedelta(weeks=offset)
    return target.strftime("%Y-%m-%d")


def login(session: requests.Session, usos_base: str, username: str, password: str) -> bool:
    r = session.get(f"{usos_base}/kontroler.php?_action=logowaniecas/index")

    soup = BeautifulSoup(r.text, "html.parser")
    form = soup.find("form", id="fm1") or soup.find("form")
    if not form:
        return False

    action = form.get("action", "")
    if not action.startswith("http"):
        from urllib.parse import urljoin
        action = urljoin(r.url, action)

    data = {"username": username, "password": password}
    for inp in form.find_all("input", type="hidden"):
        if name := inp.get("name"):
            data[name] = inp.get("value", "")

    r = session.post(action, data=data, allow_redirects=True)
    return not ("cas" in r.url and "login" in r.url)


def get_schedule(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    week = soup.find("div", class_="selected_week")
    cas = soup.find("cas-bar")

    schedule = {
        "meta": {
            "user": cas.get("logged-user", "") if cas else "",
            "week": week.find("b").text.strip() if week else "",
            "exported": datetime.now().isoformat()
        },
        "days": {}
    }

    timetable = soup.find("usos-timetable")
    if not timetable:
        return {}

    for day_div in timetable.find_all("div", recursive=False):
        h4 = day_div.find("h4")
        if not h4:
            continue
        
        day_name = h4.text.strip()
        schedule["days"][day_name] = []

        for entry in day_div.find_all("timetable-entry"):
            name = entry.get("name", "")
            
            # Czas start
            time_span = entry.find("span", slot="time")
            time_start = time_span.text.strip() if time_span else ""
            
            # Czas end z dialog-event (format: "9:45 — 11:30")
            dialog_event = entry.find("span", slot="dialog-event")
            time_end = ""
            if dialog_event:
                match = re.search(r"[—–-]\s*(\d+:\d+)", dialog_event.text)
                if match:
                    time_end = match.group(1)
            
            # Typ i info
            info_div = entry.find("div", slot="info")
            info = info_div.text.strip() if info_div else ""
            
            type_match = re.match(r"(\w+),", info)
            course_type = type_match.group(1) if type_match else ""
            
            # Sala i budynek
            loc_match = re.search(r"\((.+?),\s*bud\.\s*(\w+)\)", info)
            room, building = (loc_match.group(1), loc_match.group(2)) if loc_match else ("", "")

            schedule["days"][day_name].append({
                "time_start": time_start,
                "time_end": time_end,
                "type": TYPES.get(course_type, course_type),
                "name": name,
                "room": room,
                "building": building
            })

        schedule["days"][day_name].sort(key=lambda x: x["time_start"])

    return schedule


def print_schedule(s: dict):
    print(f"\n  {s['meta']['user']} | {s['meta']['week']}\n")
    for day, entries in s["days"].items():
        if not entries:
            continue
        print(f"  {day.upper()}")
        for e in entries:
            loc = f" ({e['room']}, {e['building']})" if e['room'] else ""
            print(f"    {e['time_start']}-{e['time_end']} {e['name']}{loc} [{e['type']}]")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="Downloads the class schedule from USOS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Przykłady:
  %(prog)s -u login -p haslo -b https://usosweb.uni.pl
  %(prog)s -u login -p haslo -b https://usosweb.uni.pl -w 1
  %(prog)s -u login -p haslo -b https://usosweb.uni.pl -d 2025-12-15 -o json
        """
    )

    parser.add_argument("-u", "--user", required=True, help="USOS login")
    parser.add_argument("-p", "--password", required=True, help="USOS password")
    parser.add_argument("-b", "--base", required=True, help="USOS base url")

    parser.add_argument("-w", "--week", type=int, default=0,
                        help="Week offset: 0=current, 1=next, -1=previous")
    parser.add_argument("-d", "--date", type=str, default=None,
                        help="Specific date YYYY-MM-DD (overwrites --week)")

    parser.add_argument("-o", "--output", choices=["json", "print"], default="print",
                        help="Output format (default: print)")
    parser.add_argument("-f", "--file", type=str, default="schedule.json",
                        help="JSON file name")

    parser.add_argument("-v", "--verbose", action="store_true",
                        help="Show status messages")

    args = parser.parse_args()

    week_date = args.date if args.date else get_week_date(args.week)
    usos_base = args.base.rstrip("/")
    session = requests.Session()

    if args.verbose:
        print(f"[*] Logging to {usos_base}...")

    if not login(session, usos_base, args.user, args.password):
        return print("[!] Login error")

    if args.verbose:
        print(f"[*] Downloading schedule ({week_date})...")

    r = session.get(
        f"{usos_base}/kontroler.php?_action=home/plan&plan_format=new-ui&plan_week_sel_week={week_date}"
    )

    schedule = get_schedule(r.text)
    if not schedule:
        return print("[!] No schedule")

    if args.output == "json":
        with open(args.file, "w", encoding="utf-8") as f:
            json.dump(schedule, f, ensure_ascii=False, indent=2)
        if args.verbose:
            print(f"[+] Saved in: {args.file}")
    else:
        print_schedule(schedule)


if __name__ == "__main__":
    main()