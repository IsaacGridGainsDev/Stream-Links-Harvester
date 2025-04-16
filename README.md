# Stream-Links-Harvester
It loads up streaming service, captures links and uses IDM to create a batch download
# Batch Streaming-Page Link Harvester for IDM

A CLI tool that extracts download URLs from streaming sites and generates IDM import scripts for batch downloading.

## Problem & Solution

**Problem:** Streaming sites only reveal the true download link after the video player has fully loaded its manifest via JavaScript. Manually clicking "Download" on ~100 episode pages is tedious.

**Solution:** This tool automates link discovery across multiple URLs, then hands off to Internet Download Manager (IDM) in one go—via a text file and batch script.

## Features

- Processes a list of URLs from a text file or command line
- Uses headless browser automation (Playwright) to extract hidden download links
- Implements rate limiting to avoid IP bans
- Generates a text file with all download links and a script to queue them in IDM
- Provides configurable timeouts, delays, and output paths

## Installation

1. Clone this repository or download the source code
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

3. Install Playwright browsers:

```bash
python -m playwright install chromium
```

## Usage

### Basic Usage

Process URLs from a file:

```bash
python -m harvester --input urls.txt
```

Process URLs from the command line:

```bash
python -m harvester --urls "https://example.com/video1,https://example.com/video2"
```

### Full Options

```bash
python -m harvester \
  --input urls.txt \
  --output-dir ./out \
  --idm-path "C:/Program Files (x86)/Internet Download Manager/IDMan.exe" \
  --download-dir "C:/Downloads" \
  --delay 5 \
  --max-per-minute 10 \
  --timeout 15 \
  --log-level INFO \
  --log-file harvester.log
```

### Configuration File

You can also use a YAML configuration file:

```bash
python -m harvester --config config.yaml
```

Example `config.yaml`:

```yaml
delay_between_requests: 5
max_requests_per_minute: 10
timeout: 15
output_dir: "./out"
idm_path: "C:/Program Files (x86)/Internet Download Manager/IDMan.exe"
download_dir: "C:/Downloads"
download_link_selector: "a.download-button, a[data-download], a.video-download"
```

## Output Files

The tool generates the following files in the output directory:

- `links.txt`: One download URL per line, deduplicated
- `idm_queue.bat` (Windows) or `idm_queue.sh` (Linux/macOS): A script to queue the links in IDM
- Log file (if specified): Records successes, failures, and timings

## Usage Flow

1. Run the tool against your list of URLs
2. Check the generated `links.txt` file to ensure the links look valid
3. Run the generated `idm_queue.bat` or `idm_queue.sh` script to add the links to IDM's queue
4. Start IDM to begin downloading

## Customization

The tool uses several strategies to find download links:

1. Looking for common download link selectors in the DOM
2. Intercepting XHR/fetch requests for media files
3. Extracting sources from video and iframe elements

If you're having trouble with a specific site, you may need to customize the selectors or detection patterns in the `config.py` file.

## Troubleshooting

- If the tool isn't finding links, try increasing the timeout value.
- Make sure your target site isn't detecting the headless browser. You may need to modify the browser configuration in `browser_client.py`.
- Check the log file for detailed error messages and warnings.

## License

Creative Commons Universal License
N.B: This is for educational or informational use only, I will not be held liable for any inaapropriate use of this program
