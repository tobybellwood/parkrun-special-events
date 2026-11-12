# parkrun special events table

This project extracts selected events from the [parkrun Australia special events page](https://www.parkrun.com.au/special-events/), creates a compact HTML table, and can export that table as a PNG.

The selected table includes:

- Every event in the Australian Capital Territory.
- The requested New South Wales events: Braidwood Showground, Bungendore Common, Goulburn, Jerrabomberra Mountain Reserve, Jindabyne, Nijong Oval, Queanbeyan, and Riverbank.

The output is sorted alphabetically by event name.

## Requirements

Install [mise](https://mise.jdx.dev/) and trust this project directory if mise asks you to do so.

The project pins these runtimes in `mise.toml`:

- Python 3.14.10
- Node.js 26.3.1

## Setup

Install the configured runtimes:

```bash
mise install
```

Install the Node dependencies and the Playwright Chromium browser:

```bash
mise run setup
```

## Tasks

Update the local page and regenerate the filtered HTML table:

```bash
mise run update-page
```

Generate the HTML table and PNG in one step:

```bash
mise run generate-image
```

The generated files are:

- `selected_special_events.html`
- `selected_special_events.png`

## Download and fallback behavior

`extract_selected_events.py` first downloads the live page and saves it as `special_events_live.html`. It validates that the downloaded page contains the expected event table before using it.

If downloading or validation fails, the script reports the error and falls back to the saved local snapshot:

```text
Special Events _ parkrun Australia.html
```

The fallback file can also be supplied explicitly:

```bash
python extract_selected_events.py --input "Special Events _ parkrun Australia.html"
```

## PNG export

`export_table_png.js` opens the generated HTML file in headless Chromium and captures only the table at 2× resolution.

To export an existing HTML file directly:

```bash
node export_table_png.js selected_special_events.html selected_special_events.png
```
