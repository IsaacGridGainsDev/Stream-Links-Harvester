"""
Utility functions for the link harvester.
"""
import asyncio
import functools
import logging
import time
from typing import Any, Callable, List, Optional, TypeVar

T = TypeVar('T')


def deduplicate_links(links: List[str]) -> List[str]:
    """
    Remove duplicate links while preserving order.
    
    Args:
        links: List of links to deduplicate
        
    Returns:
        Deduplicated list of links
    """
    seen = set()
    result = []
    
    for link in links:
        if link and link not in seen:
            seen.add(link)
            result.append(link)
    
    return result


def retry(
    max_retries: int = 3, 
    retry_delay: float = 1.0,
    exceptions: tuple = (Exception,),
    logger: Optional[logging.Logger] = None
) -> Callable:
    """
    Decorator to retry a function on failure.
    
    Args:
        max_retries: Maximum number of retries
        retry_delay: Delay between retries in seconds
        exceptions: Exceptions to catch and retry on
        logger: Logger instance
        
    Returns:
        Decorated function
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
            local_logger = logger or logging.getLogger(__name__)
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        local_logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                            f"Retrying in {wait_time:.2f}s."
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        local_logger.error(
                            f"All {max_retries + 1} attempts failed. Last error: {e}"
                        )
            
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
            local_logger = logger or logging.getLogger(__name__)
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_retries:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        local_logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                            f"Retrying in {wait_time:.2f}s."
                        )
                        time.sleep(wait_time)
                    else:
                        local_logger.error(
                            f"All {max_retries + 1} attempts failed. Last error: {e}"
                        )
            
            raise last_exception
        
        # Return the appropriate wrapper based on whether the function is async or not
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def format_time(seconds: float) -> str:
    """
    Format seconds into a human-readable string.
    
    Args:
        seconds: Time in seconds
        
    Returns:
        Formatted time string (e.g., "2m 30s")
    """
    minutes, seconds = divmod(int(seconds), 60)
    hours, minutes = divmod(minutes, 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"
