#!/usr/bin/env python3
"""
EmberEdge - NDVI Data Fetcher
Fetches real NDVI from Copernicus Sentinel-2 for Portuguese cities.
Can be run standalone or scheduled via auto_update_data.py.
"""

import sys
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

from sentinel_ndvi import fetch_all_ndvi


def main():
    print("=" * 70)
    print("EMBEREDGE - NDVI DATA FETCHER")
    print("=" * 70)
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Source: Copernicus Data Space (Sentinel-2 L2A)")
    print("=" * 70)

    results = fetch_all_ndvi(force_refresh=True)

    real_count = sum(1 for d in results.values() if 'estimated' not in d.get('source', ''))
    estimated_count = sum(1 for d in results.values() if 'estimated' in d.get('source', ''))

    print("\n" + "=" * 70)
    print(f"✅ NDVI UPDATE COMPLETE")
    print(f"   Real NDVI: {real_count} cities")
    print(f"   Estimated (fallback): {estimated_count} cities")
    print("=" * 70)

    return real_count > 0


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)