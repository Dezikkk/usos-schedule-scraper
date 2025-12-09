# USOS Schedule Scraper

A Python script that automatically downloads your class schedule from USOSweb and displays it in the terminal or saves it as a JSON file.

## Usage

### Basic usage (current week)

```bash
python usos_scraper.py -u your_login -p your_password -b https://usosweb.university.edu
```

### Download next week's schedule

```bash
python usos_scraper.py -u your_login -p your_password -b https://usosweb.university.edu -w 1
```

### Export to JSON

```bash
python usos_scraper.py -u your_login -p your_password -b https://usosweb.university.edu -o json -f my_schedule.json
```

## Command Line Arguments

| Argument | Short | Required | Description |
|----------|-------|----------|-------------|
| `--user` | `-u` | Yes | USOS login username |
| `--password` | `-p` | Yes | USOS password |
| `--base` | `-b` | Yes | USOS base URL (e.g., https://usosweb.uni.pl) |
| `--week` | `-w` | No | Week offset: 0=current, 1=next, -1=previous (default: 0) |
| `--date` | `-d` | No | Specific date in YYYY-MM-DD format (overrides `--week`) |
| `--output` | `-o` | No | Output format: `print` or `json` (default: print) |
| `--file` | `-f` | No | JSON output filename (default: schedule.json) |
| `--verbose` | `-v` | No | Show status messages |

## Output Examples

### Terminal Output

```
  Jan Kowalski | 9 grudnia 2025 - 15 grudnia 2025

  PONIEDZIAŁEK
    8:00-9:30 Analiza Matematyczna (sala 101, A) [Wykład]
    10:00-11:30 Programowanie Obiektowe (lab 205, B) [Laboratorium]

  WTOREK
    12:00-13:30 Bazy Danych (sala 303, C) [Ćwiczenia]
```

### JSON Output

```json
{
  "meta": {
    "user": "Jan Kowalski",
    "week": "2025-12-08 - 2025-12-14",
    "exported": "2025-12-09T13:51:31.505861"
  },
  "days": {
    "Poniedziałek": [
      {
        "time_start": "8:00",
        "time_end": "9:30",
        "type": "Wykład",
        "name": "Analiza Matematyczna",
        "room": "sala 101",
        "building": "A"
      }
    ]
  }
}
```
