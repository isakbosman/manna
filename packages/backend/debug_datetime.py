"""Debug script to understand datetime serialization issue."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from fastapi.testclient import TestClient
from datetime import datetime

from src.main import app
from tests.conftest import test_user, auth_headers, client, db_session

def test_debug():
    """Debug datetime serialization."""
    with TestClient(app) as test_client:
        # Test the root endpoint
        response = test_client.get("/")
        print("Root response:", response.status_code, response.json())
        
        # Test health endpoint 
        response = test_client.get("/health")
        print("Health response:", response.status_code)
        if response.status_code == 200:
            print("Health data:", response.json())
        else:
            print("Health error:", response.text)

if __name__ == "__main__":
    test_debug()