#!/usr/bin/env python3
"""
Initialize Browserforge data files during Docker build
This must run as root before switching to app user
"""
try:
    print("Initializing browserforge data files...")
    from browserforge.headers import HeaderGenerator
    from browserforge.fingerprints import Fingerprint
    print("✅ Browserforge data initialized successfully")
except Exception as e:
    print(f"⚠️  Warning: Could not initialize browserforge: {e}")
    print("   This is OK - fallback to Selenium will work")
