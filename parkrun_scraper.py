"""
Scraper for parkrun athlete results from parkrun.org.uk.
Fetches the 'all results' page and parses the results table.
Use respectfully: one request per athlete, personal/non-commercial use only.
"""

import re
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.parkrun.org.uk"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


def _parse_time(time_str: str) -> float:
    """Convert time string (MM:SS or H:MM:SS) to total seconds."""
    if not time_str or not time_str.strip():
        return None
    parts = time_str.strip().split(":")
    if len(parts) == 2:
        try:
            return int(parts[0]) * 60 + float(parts[1])
        except ValueError:
            return None
    if len(parts) == 3:
        try:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        except ValueError:
            return None
    return None


def _parse_age_grade(ag_str: str):
    """Convert age grade string like '43.14%' to float."""
    if not ag_str:
        return None
    m = re.search(r"([\d.]+)", str(ag_str))
    return float(m.group(1)) if m else None


def _parse_date(date_str: str) -> datetime | None:
    """Parse DD/MM/YYYY to datetime."""
    if not date_str or not date_str.strip():
        return None
    try:
        return datetime.strptime(date_str.strip(), "%d/%m/%Y")
    except ValueError:
        return None


def _text(cell) -> str:
    """Get stripped text from a BeautifulSoup cell."""
    if cell is None:
        return ""
    return (cell.get_text() or "").strip()


def fetch_parkrunner_results(athlete_id: str) -> tuple[pd.DataFrame | None, str, str | None]:
    """
    Fetch all results for a parkrunner from parkrun.org.uk.

    Args:
        athlete_id: Athlete number (e.g. '2099834' from URL .../parkrunner/2099834/all/).

    Returns:
        (DataFrame, runner_name, error_message). On success error_message is None.
        On failure DataFrame is None and runner_name is fallback "Athlete {id}".
    """
    athlete_id = str(athlete_id).strip()
    if not athlete_id or not athlete_id.isdigit():
        return None, f"Athlete {athlete_id or '?'}", "Please enter a valid athlete number (digits only)."

    url = f"{BASE_URL}/parkrunner/{athlete_id}/all/"
    headers = {"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"}

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        err_str = str(e)
        # 404 often happens on run days when parkrun's servers are overloaded
        if "404" in err_str or "not found" in err_str.lower() or (
            getattr(e, "response", None) is not None and getattr(e.response, "status_code", None) == 404
        ):
            return None, f"Athlete {athlete_id}", (
                "parkrun's servers may be busy (e.g. on run days like Saturday). Please try again later."
            )
        return None, f"Athlete {athlete_id}", f"Could not load results: {e}"

    soup = BeautifulSoup(resp.text, "html.parser")
    runner_name = f"Athlete {athlete_id}"
    h2 = soup.find("h2")
    if h2:
        runner_name = _text(h2) or runner_name
    tables = soup.find_all("table")

    rows_out = []
    for table in tables:
        header_cells = table.find_all("th")
        header_texts = [_text(th).lower() for th in header_cells]
        # Look for the "All Results" style table: Event, Run Date, Run Number, Pos, Time, AgeGrade, PB?
        if "event" not in header_texts or "run date" not in header_texts:
            continue
        if "pos" not in header_texts and "position" not in [h.replace(" ", "") for h in header_texts]:
            # Allow "Pos" or "Overall Position" etc
            pos_ok = any("pos" in h for h in header_texts)
            if not pos_ok:
                continue

        for tr in table.find_all("tr")[1:]:  # skip header
            tds = tr.find_all("td")
            if len(tds) < 5:
                continue
            # Assume order: Event, Run Date, Run Number, Pos, Time, AgeGrade, [PB?]
            event = _text(tds[0])
            run_date_str = _text(tds[1])
            run_number_str = _text(tds[2])
            pos_str = _text(tds[3])
            time_str = _text(tds[4])
            age_grade_str = _text(tds[5]) if len(tds) > 5 else ""
            is_pb = "pb" in (_text(tds[6]).lower() if len(tds) > 6 else "")

            run_date = _parse_date(run_date_str)
            time_sec = _parse_time(time_str)
            age_grade = _parse_age_grade(age_grade_str)
            try:
                position = int(pos_str) if pos_str else None
            except ValueError:
                position = None
            try:
                run_number = int(run_number_str) if run_number_str else None
            except ValueError:
                run_number = None

            rows_out.append({
                "event": event or None,
                "run_date": run_date,
                "run_number": run_number,
                "position": position,
                "time_sec": time_sec,
                "time_str": time_str,
                "age_grade": age_grade,
                "is_pb": is_pb,
            })

        if rows_out:
            break

    if not rows_out:
        return None, runner_name, "No results table found for this athlete. Check the ID or try again later."

    df = pd.DataFrame(rows_out)
    # Sort by date ascending so run 1, 2, 3... is chronological
    df = df.sort_values("run_date").reset_index(drop=True)
    df["run_index"] = (df.index + 1).astype(int)
    return df, runner_name, None
