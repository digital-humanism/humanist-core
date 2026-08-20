"""conftest.py

Pytest path configuration..
"""
import sys
import os

# Add the project root to sys.path.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))