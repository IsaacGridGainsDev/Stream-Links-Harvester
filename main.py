#!/usr/bin/env python3
"""
Batch Streaming-Page Link Harvester for IDM

CLI entrypoint: parses arguments, loads config, and orchestrates the link harvesting process.
"""
import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Optional

from harvester.browser_client import BrowserClient
from harvester.config import Config, load_config
from harvester.extractor import extract_download_url
from harvester.logger import setup_logger
from harvester.output import write_idm_script, write_links
from harvester.utils import deduplicate_links


async def process_url(browser_client: BrowserClient, url: str, logger: logging.Logger) -> Optional[str]:
    """Process a single URL and extract the download link."""
    logger.info(f"Processing URL: {url}")
    try:
        download_url = await browser_client.fetch_and_extract(url)
        if download_url:
            logger.info(f"Found download URL: {download_url}")
            return download_url
        else:
            logger.warning(f"No download URL found for: {url}")
            return None
    except Exception as e:
        logger.error(f"Error processing URL {url}: {e}")
        return None


def load_urls_from_file(file_path: str) -> List[str]:
    """Load URLs from a text file, one per line."""
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Batch Streaming-Page Link Harvester for IDM")
    
    # Input options
    parser.add_argument("--input", "-i", help="Path to text file containing URLs (one per line)")
    parser.add_argument("--urls", help="Comma-separated list of URLs to process")
    
    # Output options
    parser.add_argument("--output-dir", "-o", default="./out", help="Directory for output files")
    parser.add_argument("--idm-path", default="C:/Program Files (x86)/Internet Download Manager/IDMan.exe", 
                        help="Path to IDM executable")
    parser.add_argument("--download-dir", default="C:/Downloads", 
                        help="Directory where IDM should save downloads")
    
    # Timing and rate-limit options
    parser.add_argument("--delay", "-d", type=int, default=5, 
                        help="Delay between page loads in seconds")
    parser.add_argument("--max-per-minute", "-m", type=int, default=10, 
                        help="Maximum pages to process per minute")
    parser.add_argument("--timeout", "-t", type=int, default=15, 
                        help="Timeout for waiting for download link in seconds")
    
    # Configuration
    parser.add_argument("--config", "-c", help="Path to YAML configuration file")
    
    # Logging
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        default="INFO", help="Logging level")
    parser.add_argument("--log-file", help="Path to log file (if not specified, logs to console)")
    
    return parser.parse_args()


async def main() -> int:
    """Main entry point for the link harvester."""
    args = parse_arguments()
    
    # Load configuration (CLI args take precedence over config file)
    config = Config()
    if args.config:
        config = load_config(args.config)
    
    # Override config with CLI args
    config.delay_between_requests = args.delay
    config.max_requests_per_minute = args.max_per_minute
    config.timeout = args.timeout
    config.output_dir = args.output_dir
    config.idm_path = args.idm_path
    config.download_dir = args.download_dir
    
    # Set up logging
    logger = setup_logger(args.log_level, args.log_file)
    logger.info("Starting Batch Streaming-Page Link Harvester")
    
    # Create output directory if it doesn't exist
    output_dir = Path(config.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get URLs to process
    urls = []
    if args.input:
        logger.info(f"Loading URLs from file: {args.input}")
        urls = load_urls_from_file(args.input)
    elif args.urls:
        logger.info("Using URLs provided via command line")
        urls = [url.strip() for url in args.urls.split(",") if url.strip()]
    else:
        logger.error("No URLs provided. Use --input or --urls")
        return 1
    
    logger.info(f"Found {len(urls)} URLs to process")
    
    # Initialize browser client
    browser_client = BrowserClient(
        delay_between_requests=config.delay_between_requests,
        max_requests_per_minute=config.max_requests_per_minute,
        timeout=config.timeout,
        logger=logger
    )
    
    # Process URLs and collect download links
    try:
        await browser_client.initialize()
        tasks = [process_url(browser_client, url, logger) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=False)
        download_urls = [url for url in results if url]
    finally:
        await browser_client.cleanup()
    
    # Deduplicate links
    unique_links = deduplicate_links(download_urls)
    logger.info(f"Found {len(unique_links)} unique download links")
    
    # Write output files
    links_path = output_dir / "links.txt"
    write_links(unique_links, links_path)
    logger.info(f"Download links written to {links_path}")
    
    # Determine OS and write appropriate script
    is_windows = sys.platform.startswith('win')
    script_name = "idm_queue.bat" if is_windows else "idm_queue.sh"
    script_path = output_dir / script_name
    
    write_idm_script(
        unique_links, 
        script_path, 
        config.idm_path, 
        config.download_dir,
        is_windows
    )
    logger.info(f"IDM script written to {script_path}")
    
    if not unique_links:
        logger.error("No download links were found")
        return 1
    
    logger.info("Batch Streaming-Page Link Harvester completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
