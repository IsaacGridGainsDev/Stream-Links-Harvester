"""
Output functions for writing links and IDM scripts.
"""
import os
from pathlib import Path
from typing import List


def write_links(links: List[str], path: Path) -> None:
    """
    Write links to a text file, one per line.
    
    Args:
        links: List of download URLs
        path: Path to write the links to
    """
    with open(path, 'w') as file:
        for link in links:
            file.write(f'DOWNLOAD_DIR="{download_dir}"\n\n')
        
        file.write('if [ ! -f "$IDM_PATH" ]; then\n')
        file.write('    echo "IDM executable not found at $IDM_PATH"\n')
        file.write('    echo "Please edit this script with the correct path to IDMan"\n')
        file.write('    exit 1\n')
        file.write('fi\n\n')
        
        file.write('echo "Adding links to IDM queue..."\n\n')
        
        file.write('while IFS= read -r url; do\n')
        file.write('    echo "Adding: $url"\n')
        file.write('    "$IDM_PATH" /d "$url" /p "$DOWNLOAD_DIR" /n /a\n')
        file.write('    sleep 1\n')
        file.write('done < links.txt\n\n')
        
        file.write('echo "All links have been added to IDM queue."\n')
        file.write('echo "Remember to start IDM to begin downloads."\n')f"{link}\n")


def write_idm_script(
    links: List[str], 
    script_path: Path, 
    idm_path: str, 
    download_dir: str,
    is_windows: bool = True
) -> None:
    """
    Write a script to enqueue links in IDM.
    
    Args:
        links: List of download URLs
        script_path: Path to write the script to
        idm_path: Path to IDM executable
        download_dir: Directory where IDM should save downloads
        is_windows: Whether to generate a Windows batch script (True) or Unix shell script (False)
    """
    if is_windows:
        _write_windows_script(links, script_path, idm_path, download_dir)
    else:
        _write_unix_script(links, script_path, idm_path, download_dir)


def _write_windows_script(links: List[str], script_path: Path, idm_path: str, download_dir: str) -> None:
    """
    Write a Windows batch script to enqueue links in IDM.
    
    Args:
        links: List of download URLs
        script_path: Path to write the script to
        idm_path: Path to IDM executable
        download_dir: Directory where IDM should save downloads
    """
    # Escape double quotes in paths
    idm_path = idm_path.replace('"', '""')
    download_dir = download_dir.replace('"', '""')
    
    with open(script_path, 'w') as file:
        file.write("@echo off\n")
        file.write("echo IDM Link Enqueue Script\n")
        file.write("echo ----------------------\n\n")
        
        file.write(f'set "IDM_PATH={idm_path}"\n')
        file.write(f'set "DOWNLOAD_DIR={download_dir}"\n\n')
        
        file.write('if not exist "%IDM_PATH%" (\n')
        file.write('    echo IDM executable not found at %IDM_PATH%\n')
        file.write('    echo Please edit this script with the correct path to IDMan.exe\n')
        file.write('    pause\n')
        file.write('    exit /b 1\n')
        file.write(')\n\n')
        
        file.write('echo Adding %DOWNLOAD_DIR% as download location...\n\n')
        
        file.write('echo Adding links to IDM queue...\n')
        
        # Either read from a file or use embedded links
        file.write('for /f "usebackq delims=" %%u in ("links.txt") do (\n')
        file.write('    echo Adding: %%u\n')
        file.write('    "%IDM_PATH%" /d "%%u" /p "%DOWNLOAD_DIR%" /n /a\n')
        file.write('    timeout /t 1 /nobreak >nul\n')
        file.write(')\n\n')
        
        file.write('echo All links have been added to IDM queue.\n')
        file.write('echo Remember to start IDM to begin downloads.\n')
        file.write('pause\n')


def _write_unix_script(links: List[str], script_path: Path, idm_path: str, download_dir: str) -> None:
    """
    Write a Unix shell script to enqueue links in IDM.
    
    Args:
        links: List of download URLs
        script_path: Path to write the script to
        idm_path: Path to IDM executable
        download_dir: Directory where IDM should save downloads
    """
    # Escape spaces in paths
    idm_path = idm_path.replace(' ', '\\ ')
    download_dir = download_dir.replace(' ', '\\ ')
    
    with open(script_path, 'w') as file:
        file.write("#!/bin/bash\n\n")
        file.write('echo "IDM Link Enqueue Script"\n')
        file.write('echo "----------------------"\n\n')
        
        file.write(f'IDM_PATH="{idm_path}"\n')
        file.write(
