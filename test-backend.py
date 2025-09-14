#!/usr/bin/env python3
"""
Simple test script to verify backend services are working
"""
import requests
import json
import time

def test_service(name, url, expected_status=200):
    """Test a service endpoint"""
    try:
        print(f"Testing {name}...")
        response = requests.get(url, timeout=5)
        if response.status_code == expected_status:
            print(f"✅ {name} is working (Status: {response.status_code})")
            return True
        else:
            print(f"❌ {name} returned status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ {name} failed: {e}")
        return False

def test_infrastructure():
    """Test infrastructure services"""
    print("🔧 Testing Infrastructure Services...")
    
    # Test Traefik Dashboard
    test_service("Traefik Dashboard", "http://localhost:8081/api/rawdata")
    
    # Test Redis (indirect test via ping)
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, decode_responses=True)
        r.ping()
        print("✅ Redis is working")
    except Exception as e:
        print(f"❌ Redis failed: {e}")
    
    # Test PostgreSQL (indirect test)
    try:
        import psycopg2
        conn = psycopg2.connect(
            host="localhost",
            database="delox",
            user="delox_user",
            password="delox_password",
            port="5432"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        if result[0] == 1:
            print("✅ PostgreSQL is working")
        conn.close()
    except Exception as e:
        print(f"❌ PostgreSQL failed: {e}")

def main():
    print("🚀 Delox Backend Test Suite")
    print("=" * 50)
    
    # Test infrastructure first
    test_infrastructure()
    
    print("\n📡 Testing Backend Services...")
    
    # Test backend services (these will fail if not running)
    services = [
        ("Auth Service", "http://localhost:8001/health"),
        ("User Service", "http://localhost:8002/health"),
        ("Order Service", "http://localhost:8003/health"),
        ("Courier Service", "http://localhost:8004/health"),
        ("Notification Service", "http://localhost:8005/health"),
        ("Analytics Service", "http://localhost:8006/health"),
    ]
    
    working_services = 0
    for name, url in services:
        if test_service(name, url):
            working_services += 1
    
    print(f"\n📊 Summary: {working_services}/{len(services)} backend services are running")
    
    if working_services == 0:
        print("\n💡 To start backend services, run:")
        print("   docker-compose up -d auth-service user-service order-service")
    
    print("\n🌐 Frontend should be available at: http://localhost:3000")
    print("📊 Traefik Dashboard: http://localhost:8081")

if __name__ == "__main__":
    main()
