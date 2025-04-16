"""
Functions for extracting download URLs from web pages.
"""
import asyncio
import logging
import re
from typing import Dict, List, Optional

import playwright.async_api as pw


async def extract_download_url(
    page: pw.Page, 
    xhr_responses: Dict[str, str],
    timeout: int
) -> Optional[str]:
    """
    Extract the download URL from a page.
    
    Args:
        page: Playwright page object
        xhr_responses: Dictionary of XHR responses
        timeout: Maximum time to wait for the download link
        
    Returns:
        The download URL if found, None otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Try multiple strategies to find the download URL
    download_url = await _try_find_download_link(page, timeout)
    if download_url:
        return download_url
    
    # If we didn't find a visible download link, check XHR responses
    download_url = _analyze_xhr_responses(xhr_responses)
    if download_url:
        return download_url
    
    # Try to find video elements
    download_url = await _extract_from_video_source(page)
    if download_url:
        return download_url
    
    # Try to find iframe sources that might contain videos
    download_url = await _extract_from_iframe(page)
    if download_url:
        return download_url
    
    logger.warning("Could not find download URL using any extraction method")
    return None


async def _try_find_download_link(page: pw.Page, timeout: int) -> Optional[str]:
    """
    Try to find a download link on the page.
    
    Args:
        page: Playwright page object
        timeout: Maximum time to wait for the download link
        
    Returns:
        The download URL if found, None otherwise
    """
    logger = logging.getLogger(__name__)
    
    # List of common selectors for download links
    selectors = [
        "a.download-button",
        "a[data-download]",
        "a.video-download",
        "a[href*='download']",
        "a[href*='.mp4']",
        "a[href*='.m3u8']",
        "a[href*='.mpd']",
        "button.download-button",
        "[data-download-url]",
        "[data-video-url]"
    ]
    
    # Try each selector
    for selector in selectors:
        try:
            logger.debug(f"Trying selector: {selector}")
            # Wait for the element to be visible
            element = await page.wait_for_selector(
                selector,
                state="visible",
                timeout=timeout * 1000 / len(selectors)  # Divide timeout among selectors
            )
            
            if element:
                # Try to get href attribute
                href = await element.get_attribute("href")
                if href and _is_valid_download_url(href):
                    logger.info(f"Found download link with selector {selector}: {href}")
                    return href
                
                # Try to get data-download-url attribute
                data_url = await element.get_attribute("data-download-url")
                if data_url and _is_valid_download_url(data_url):
                    logger.info(f"Found download link with data attribute: {data_url}")
                    return data_url
                
                # Try to get data-video-url attribute
                data_video = await element.get_attribute("data-video-url")
                if data_video and _is_valid_download_url(data_video):
                    logger.info(f"Found video link with data attribute: {data_video}")
                    return data_video
                
                # For buttons, check if clicking them reveals a URL
                if "button" in selector:
                    logger.debug("Found button, attempting to click")
                    await element.click()
                    await asyncio.sleep(2)  # Wait for any popups or reveals
                    
                    # Try to find newly revealed download links
                    popup_url = await _check_for_popup_link(page)
                    if popup_url:
                        return popup_url
        except Exception as e:
            logger.debug(f"Error with selector {selector}: {e}")
    
    logger.debug("No download link found with static selectors")
    return None


def _analyze_xhr_responses(xhr_responses: Dict[str, str]) -> Optional[str]:
    """
    Analyze XHR responses to find the download URL.
    
    Args:
        xhr_responses: Dictionary of XHR responses
        
    Returns:
        The download URL if found, None otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Look for common video file patterns in XHR responses
    video_patterns = [".mp4", ".m3u8", ".mpd", "/media/", "/video/", "stream"]
    
    for url in xhr_responses.values():
        if any(pattern in url for pattern in video_patterns):
            logger.info(f"Found potential video URL in XHR: {url}")
            if _is_valid_download_url(url):
                return url
    
    return None


async def _extract_from_video_source(page: pw.Page) -> Optional[str]:
    """
    Extract video source URL from video elements.
    
    Args:
        page: Playwright page object
        
    Returns:
        The video source URL if found, None otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Check for video elements
    video_elements = await page.query_selector_all("video")
    for video in video_elements:
        src = await video.get_attribute("src")
        if src and _is_valid_download_url(src):
            logger.info(f"Found video source: {src}")
            return src
        
        # Check for source elements inside the video
        source_elements = await video.query_selector_all("source")
        for source in source_elements:
            src = await source.get_attribute("src")
            if src and _is_valid_download_url(src):
                logger.info(f"Found video source: {src}")
                return src
    
    return None


async def _extract_from_iframe(page: pw.Page) -> Optional[str]:
    """
    Extract video URL from iframes.
    
    Args:
        page: Playwright page object
        
    Returns:
        The video URL if found, None otherwise
    """
    logger = logging.getLogger(__name__)
    
    # Check for iframe elements
    iframe_elements = await page.query_selector_all("iframe")
    for iframe in iframe_elements:
        src = await iframe.get_attribute("src")
        if src and _is_iframe_video_source(src):
            logger.info(f"Found iframe source: {src}")
            return src
    
    return None


async def _check_for_popup_link(page: pw.Page) -> Optional[str]:
    """
    Check for download links that may have appeared after clicking a button.
    
    Args:
        page: Playwright page object
        
    Returns:
        The download URL if found, None otherwise
    """
    # List of selectors that might appear in popups or modals
    popup_selectors = [
        "a.download-link",
        "a[download]",
        ".modal a[href*='.mp4']",
        ".popup a[href*='download']"
    ]
    
    for selector in popup_selectors:
        try:
            element = await page.query_selector(selector)
            if element:
                href = await element.get_attribute("href")
                if href and _is_valid_download_url(href):
                    return href
        except Exception:
            pass
    
    return None


def _is_valid_download_url(url: str) -> bool:
    """
    Check if a URL is a valid download URL.
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is a valid download URL, False otherwise
    """
    if not url:
        return False
    
    # URL should start with http:// or https://
    if not url.startswith(("http://", "https://")):
        return False
    
    # URL should contain a file extension or streaming pattern
    video_patterns = [".mp4", ".m3u8", ".mpd", "/media/", "/video/", "stream", "download"]
    if not any(pattern in url for pattern in video_patterns):
        return False
    
    return True


def _is_iframe_video_source(url: str) -> bool:
    """
    Check if an iframe source URL is likely to be a video source.
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL is likely to be a video source, False otherwise
    """
    if not url:
        return False
    
    # Check for common video hosting services
    video_hosts = [
        "youtube.com/embed",
        "player.vimeo.com",
        "dailymotion.com/embed",
        "streamable.com/e",
        "jwplayer",
        "brightcove",
        "vidyard",
        "wistia",
        "videojs"
    ]
    
    return any(host in url for host in video_hosts)
