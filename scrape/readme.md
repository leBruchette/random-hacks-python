# usac-scraper

## Description
`usac-scraper` is a Python project designed to scrape data from the USAC website and process it for various uses.

## Installation
1. Create and activate a virtual environment:
    ```sh
    python3 -m venv venv
    source venv/bin/activate  # On Windows use `.\venv\Scripts\activate`
    ```
2. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage
1. Run scraper.py with your USAC ID as an argument:
    ```sh
    python scraper.py <your-usac-id>
    ```
2. The scraper will produce a JSON file containing the scraped data, located in the `output` directory.
