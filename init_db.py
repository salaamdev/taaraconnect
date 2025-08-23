#!/usr/bin/env python3
"""
Initialize database with tables
"""

import sys
import os

# Set Python path to use system packages
sys.path.insert(0, '/usr/lib/python3/dist-packages')

from app.database import create_tables

if __name__ == "__main__":
    try:
        create_tables()
        print("✅ Database tables created successfully!")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        sys.exit(1)
