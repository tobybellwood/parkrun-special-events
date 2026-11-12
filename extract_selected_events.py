#!/usr/bin/env python3
"""Extract configured parkrun events into a minimal HTML table."""

from __future__ import annotations

import argparse
import sys
import tomllib
import urllib.error
import urllib.request
from html import escape
from html.parser import HTMLParser
from pathlib import Path


HEADINGS = ("Event", "Region", "Christmas Day", "New Year's Day")
LIVE_URL = "https://www.parkrun.com.au/special-events/"


class ResultsTableParser(HTMLParser):
    """Read visible cell text from the source table with id="results"."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_results_table = False
        self.table_depth = 0
        self.in_row = False
        self.in_cell = False
        self.current_cell: list[str] = []
        self.current_row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        if tag == "table" and attributes.get("id") == "results":
            self.in_results_table = True
            self.table_depth = 1
            return

        if not self.in_results_table:
            return

        if tag == "table":
            self.table_depth += 1
        elif tag == "tr":
            self.in_row = True
            self.current_row = []
        elif tag in {"th", "td"} and self.in_row:
            self.in_cell = True
            self.current_cell = []

    def handle_endtag(self, tag: str) -> None:
        if not self.in_results_table:
            return

        if tag in {"th", "td"} and self.in_cell:
            self.current_row.append("".join(self.current_cell).strip())
            self.current_cell = []
            self.in_cell = False
        elif tag == "tr" and self.in_row:
            if self.current_row:
                self.rows.append(self.current_row)
            self.current_row = []
            self.in_row = False
        elif tag == "table":
            self.table_depth -= 1
            if self.table_depth == 0:
                self.in_results_table = False

    def handle_data(self, data: str) -> None:
        if self.in_results_table and self.in_cell:
            self.current_cell.append(data)


def parse_events(source_text: str, source_name: str) -> list[dict[str, str]]:
    parser = ResultsTableParser()
    parser.feed(source_text)

    if not parser.rows:
        raise ValueError(f'Could not find a populated table with id="results" in {source_name}')

    headings = tuple(parser.rows[0])
    if headings != HEADINGS:
        raise ValueError(f"Unexpected table headings in {source_name}: {headings!r}")

    events = []
    for row in parser.rows[1:]:
        if len(row) != len(HEADINGS):
            continue
        events.append(dict(zip(HEADINGS, row)))
    return events


def read_events(source: Path) -> list[dict[str, str]]:
    return parse_events(source.read_text(encoding="utf-8"), str(source))


def download_live_page(url: str, cache: Path) -> Path:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15"
            ),
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        page = response.read().decode("utf-8")

    # Validate the downloaded response before using it as the source.
    parse_events(page, url)
    cache.write_text(page, encoding="utf-8")
    return cache


def read_selection(source: Path) -> tuple[set[str], dict[str, set[str]]]:
    config = tomllib.loads(source.read_text(encoding="utf-8"))
    regions = config.get("regions", [])
    extra_event_groups = config.get("extra_events", {})

    if not isinstance(regions, list) or not all(isinstance(region, str) for region in regions):
        raise ValueError(f"{source} must define regions as a list of strings")
    if not isinstance(extra_event_groups, dict):
        raise ValueError(f"{source} must define extra_events as region tables")

    extra_events: dict[str, set[str]] = {}
    for region, group in extra_event_groups.items():
        if not isinstance(region, str) or not isinstance(group, dict):
            raise ValueError(f"{source} has an invalid extra_events group")
        events = group.get("events", [])
        if not isinstance(events, list) or not all(isinstance(event, str) for event in events):
            raise ValueError(f'{source} extra_events.{region!r} must define events as a list of strings')
        extra_events[region] = set(events)

    return set(regions), extra_events


def select_events(
    events: list[dict[str, str]],
    regions: set[str],
    extra_events: dict[str, set[str]],
) -> list[dict[str, str]]:
    selected = [
        event
        for event in events
        if event["Region"] in regions
        or event["Event"] in extra_events.get(event["Region"], set())
    ]
    return sorted(selected, key=lambda event: event["Event"].casefold())


def render_html(events: list[dict[str, str]]) -> str:
    rows = []
    for event in events:
        cells = []
        for heading in HEADINGS:
            value = escape(event[heading])
            class_name = ' class="status"' if heading in {"Christmas Day", "New Year's Day"} else ""
            cells.append(f"        <td{class_name}>{value}</td>")
        rows.append("      <tr>\n" + "\n".join(cells) + "\n      </tr>")

    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Selected parkrun special events</title>
  <style>
    body {{
      margin: 24px;
      background: #fff;
      color: #272727;
      font-family: Montserrat, Arial, sans-serif;
    }}
    table {{
      border-collapse: collapse;
      width: 100%;
      max-width: 1180px;
      margin: 0 auto;
      font-size: 14px;
    }}
    tr {{
      height: 34px;
    }}
    th, td {{
      border: 1px solid #272727;
      padding: 8px;
      text-align: left;
    }}
    th {{
      font-size: 16px;
      font-weight: 400;
      white-space: nowrap;
      text-align: center;
    }}
    tbody tr:nth-child(odd) {{
      background: #f2f2f2;
    }}
    .status {{
      width: 145px;
      text-align: center;
    }}
  </style>
</head>
<body>
  <table>
    <thead>
      <tr>
        <th>Event</th>
        <th>Region</th>
        <th>Christmas Day</th>
        <th>New Year's Day</th>
      </tr>
    </thead>
    <tbody>
{chr(10).join(rows)}
    </tbody>
  </table>
</body>
</html>
'''


def main() -> None:
    workspace = Path(__file__).resolve().parent
    argument_parser = argparse.ArgumentParser(description=__doc__)
    argument_parser.add_argument(
        "--selection",
        type=Path,
        default=workspace / "selection.toml",
        help="TOML file defining included regions and extra events",
    )
    argument_parser.add_argument(
        "--url",
        default=LIVE_URL,
        help="Live page to download before parsing",
    )
    argument_parser.add_argument(
        "--input",
        type=Path,
        default=workspace / "Special Events _ parkrun Australia.html",
        help="Local fallback HTML page to read if downloading fails",
    )
    argument_parser.add_argument(
        "--cache",
        type=Path,
        default=workspace / "special_events_live.html",
        help="Local file in which to save a successful download",
    )
    argument_parser.add_argument(
        "--output",
        type=Path,
        default=workspace / "selected_special_events.html",
        help="HTML file to create",
    )
    args = argument_parser.parse_args()
    regions, extra_events = read_selection(args.selection)

    try:
        source = download_live_page(args.url, args.cache)
        events = read_events(source)
        print(f"Downloaded live page and saved it to {source}")
    except (OSError, TimeoutError, urllib.error.URLError, ValueError) as error:
        print(
            f"Could not download or validate {args.url}: {error}. "
            f"Falling back to local file {args.input}.",
            file=sys.stderr,
        )
        events = read_events(args.input)
        source = args.input

    selected = select_events(events, regions, extra_events)
    args.output.write_text(render_html(selected), encoding="utf-8")
    print(f"Wrote {args.output} with {len(selected)} event rows using {source}")


if __name__ == "__main__":
    main()
