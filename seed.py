"""AI Panel Studio — Root Database Seeding Script Wrapper."""

import asyncio
import os
import sys

# Add backend directory to sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

from seed import seed_database

if __name__ == "__main__":
    asyncio.run(seed_database())
