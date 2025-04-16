from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="idm-link-harvester",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Batch Streaming-Page Link Harvester for IDM",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/idm-link-harvester",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
    install_requires=[
        "playwright>=1.35.0",
        "pyyaml>=6.0",
        "beautifulsoup4>=4.11.0",
        "asyncio>=3.4.3",
    ],
    entry_points={
        "console_scripts": [
            "harvester=harvester.main:main",
        ],
    },
)
