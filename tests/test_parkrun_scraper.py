import pytest
from datetime import datetime
import pandas as pd
from unittest.mock import patch, MagicMock

from parkrun_scraper import _parse_time, _parse_age_grade, _parse_date, fetch_parkrunner_results

def test_parse_time():
    assert _parse_time("21:30") == 21 * 60 + 30
    assert _parse_time("1:05:10") == 3600 + 5 * 60 + 10
    assert _parse_time("") is None
    assert _parse_time("invalid") is None

def test_parse_age_grade():
    assert _parse_age_grade("65.4%") == 65.4
    assert _parse_age_grade("43.14%") == 43.14
    assert _parse_age_grade("") is None

def test_parse_date():
    assert _parse_date("12/05/2023") == datetime(2023, 5, 12)
    assert _parse_date("") is None
    assert _parse_date("invalid") is None

@patch("parkrun_scraper.requests.get")
def test_fetch_parkrunner_results_success(mock_get):
    html_content = """
    <html>
        <h2>Athlete 12345</h2>
        <table>
            <tr>
                <th>Event</th>
                <th>Run Date</th>
                <th>Run Number</th>
                <th>Pos</th>
                <th>Time</th>
                <th>AgeGrade</th>
                <th>PB?</th>
            </tr>
            <tr>
                <td>Bushy parkrun</td>
                <td>01/01/2023</td>
                <td>100</td>
                <td>42</td>
                <td>20:00</td>
                <td>70.5%</td>
                <td>PB</td>
            </tr>
        </table>
    </html>
    """
    mock_response = MagicMock()
    mock_response.text = html_content
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    df, runner_name, error = fetch_parkrunner_results("12345")

    assert error is None
    assert runner_name == "Athlete 12345"
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert df.iloc[0]["event"] == "Bushy parkrun"
    assert df.iloc[0]["run_date"] == datetime(2023, 1, 1)
    assert df.iloc[0]["run_number"] == 100
    assert df.iloc[0]["position"] == 42
    assert df.iloc[0]["time_sec"] == 1200
    assert df.iloc[0]["age_grade"] == 70.5
    assert bool(df.iloc[0]["is_pb"]) is True

@patch("parkrun_scraper.requests.get")
def test_fetch_parkrunner_results_invalid_id(mock_get):
    df, runner_name, error = fetch_parkrunner_results("abc")
    assert df is None
    assert "Please enter a valid athlete number" in error

@patch("parkrun_scraper.requests.get")
def test_fetch_parkrunner_results_network_error(mock_get):
    from requests.exceptions import RequestException
    mock_get.side_effect = RequestException("Network error")

    df, runner_name, error = fetch_parkrunner_results("12345")

    assert df is None
    assert "Could not load results" in error
