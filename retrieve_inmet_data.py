#!/usr/bin/env python3
"""
Script to retrieve weather data from INMET API.
"""

import argparse
import os
import sys
import requests
from datetime import datetime


def get_inmet_data(data_inicial: str, data_final: str = None, cod_estacao: str = None, hour: str = None) -> dict:
    """
    Retrieve data from INMET API.
    
    Args:
        data_inicial: Initial date (format: YYYY-MM-DD or according to API requirements)
        data_final: Final date (format: YYYY-MM-DD or according to API requirements) - optional
        cod_estacao: Station code - optional
        hour: Hour in UTC timestamp format HHmm (e.g., 1430 for 14:30) - optional
        
    Returns:
        Dictionary with the API response
    """
    # Get token from environment variable
    token = os.getenv("INMET_API_TOKEN")
    
    if not token:
        raise ValueError("Environment variable 'INMET_API_TOKEN' not set")
    
    # Build the URL based on whether hour is provided
    if hour:
        # Use the /dados/ endpoint when hour is provided
        base_url = "https://apitempo.inmet.gov.br/token/estacao/dados"
        url = f"{base_url}/{data_inicial}/{hour}/{token}"
    else:
        # Use the regular endpoint without hour
        base_url = "https://apitempo.inmet.gov.br/token/estacao"
        url = f"{base_url}/{data_inicial}/{data_final}/{cod_estacao}/{token}"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making API request: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Retrieve weather data from INMET API"
    )
    parser.add_argument(
        "data_inicial",
        help="Initial date (e.g., 2025-01-01)"
    )
    parser.add_argument(
        "data_final",
        nargs="?",
        default=None,
        help="Final date (e.g., 2025-01-31) - optional if using --hour"
    )
    parser.add_argument(
        "cod_estacao",
        nargs="?",
        default=None,
        help="Station code - optional if using --hour"
    )
    parser.add_argument(
        "--hour",
        type=str,
        default=None,
        help="Hour in UTC timestamp format HHmm (e.g., 1430 for 14:30) - optional"
    )
    
    args = parser.parse_args()
    
    try:
        data = get_inmet_data(
            args.data_inicial, 
            args.data_final, 
            args.cod_estacao,
            args.hour
        )
        
        # Print the data (can be modified to save to file or process differently)
        import json
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
