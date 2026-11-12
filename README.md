# parkrun special events table

This project extracts selected events from the [parkrun Australia special events page](https://www.parkrun.com.au/special-events/), creates a compact HTML table, and can export that table as a PNG.

The current selection includes:

- Every event in the Australian Capital Territory.
- The requested New South Wales events: Braidwood Showground, Bungendore Common, Goulburn, Jerrabomberra Mountain Reserve, Jindabyne, Nijong Oval, Queanbeyan, and Riverbank.

The selection is configured in [`selection.toml`](selection.toml), so other users can change it without editing the Python script. The output is sorted alphabetically by event name.

## Configure the selection

Add a region to `regions` to include every event in that region:

```toml
regions = ["Australian Capital Territory", "Victoria"]
```

Add selected events from another region under `extra_events`:

```toml
[extra_events."New South Wales"]
events = [
  "Riverbank parkrun",
  "Goulburn parkrun",
]
```

Event names must match the source table exactly. You can omit `regions` or leave it empty when you only want selected events:

```toml
regions = []

[extra_events."New South Wales"]
events = ["Riverbank parkrun", "Goulburn parkrun"]
```

You can select events from multiple regions in the same file:

```toml
regions = []

[extra_events."New South Wales"]
events = ["Riverbank parkrun"]

[extra_events."Victoria"]
events = ["Albert parkrun, Melbourne", "Aintree Reserve parkrun"]
```

To use a different configuration file:

```bash
python extract_selected_events.py --selection another-selection.toml
```

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
