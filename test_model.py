"""
Test script to verify the model works correctly
Run this to test incident classification and duplicate detection
"""

import requests
import json
from datetime import datetime, timedelta
import math

API_URL = 'http://localhost:5000'

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two coordinates in meters using Haversine formula"""
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def test_classification():
    """Test incident classification"""
    print("=" * 70)
    print("TEST 1: Incident Classification")
    print("=" * 70)
    
    test_cases = [
        {
            "text": "بلاغ اختطاف طفل في الرياض",
            "expected_severity": "عالي",
            "lat": 24.7136,
            "lng": 46.6753
        },
        {
            "text": "سيارة متوقفة في الشارع في جدة",
            "expected_severity": "عادي",
            "lat": 21.4858,
            "lng": 39.1925
        },
        {
            "text": "مشاجرة بين شباب في مكة",
            "expected_severity": "متوسط",
            "lat": 21.3891,
            "lng": 39.8579
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test['text']}")
        try:
            response = requests.post(f"{API_URL}/api/analyze", json={
                "text": test['text'],
                "latitude": test['lat'],
                "longitude": test['lng']
            })
            
            if response.status_code == 200:
                data = response.json()
                classification = data.get('classification', {})
                severity = classification.get('severity', 'N/A')
                confidence = classification.get('confidence', 0)
                
                print(f"  [OK] Status: Success")
                print(f"  [OK] Severity: {severity} (Expected: {test['expected_severity']})")
                print(f"  [OK] Confidence: {confidence:.2%}")
                print(f"  [OK] Location: {data.get('location', {}).get('city', 'N/A')}")
                print(f"  [OK] Similar incidents: {len(data.get('similar_incidents', []))}")
                
                if severity == test['expected_severity']:
                    print(f"  [PASSED]")
                else:
                    print(f"  [WARNING] Severity mismatch")
            else:
                print(f"  [FAILED] HTTP {response.status_code}")
                print(f"  Error: {response.text}")
        except Exception as e:
            print(f"  [FAILED] {str(e)}")

def test_duplicate_detection():
    """Test duplicate detection (20 minutes + 200 meters)"""
    print("\n" + "=" * 70)
    print("TEST 2: Duplicate Detection")
    print("=" * 70)
    
    # Test cases for duplicate detection
    base_time = datetime.now()
    
    test_cases = [
        {
            "name": "Same location, within 20 minutes",
            "text": "بلاغ سرقة في الرياض",
            "lat": 24.7136,
            "lng": 46.6753,
            "time_offset": timedelta(minutes=10),  # 10 minutes ago
            "distance": 50,  # 50 meters away
            "should_be_duplicate": True
        },
        {
            "name": "Same location, more than 20 minutes",
            "text": "بلاغ سرقة في الرياض",
            "lat": 24.7136,
            "lng": 46.6753,
            "time_offset": timedelta(minutes=30),  # 30 minutes ago
            "distance": 50,  # 50 meters away
            "should_be_duplicate": False
        },
        {
            "name": "Different location (>200m), within 20 minutes",
            "text": "بلاغ سرقة في الرياض",
            "lat": 24.7150,  # ~200m away
            "lng": 46.6770,
            "time_offset": timedelta(minutes=10),
            "distance": 250,
            "should_be_duplicate": False
        },
        {
            "name": "Same location, within 200m, within 20 minutes",
            "text": "بلاغ سرقة في الرياض",
            "lat": 24.7138,  # ~100m away
            "lng": 46.6755,
            "time_offset": timedelta(minutes=15),
            "distance": 100,
            "should_be_duplicate": True
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test['name']}")
        print(f"  Time offset: {test['time_offset']}")
        print(f"  Distance: {test['distance']}m")
        print(f"  Expected duplicate: {test['should_be_duplicate']}")
        
        try:
            response = requests.post(f"{API_URL}/api/analyze", json={
                "text": test['text'],
                "latitude": test['lat'],
                "longitude": test['lng'],
                "timestamp": (base_time - test['time_offset']).isoformat()
            })
            
            if response.status_code == 200:
                data = response.json()
                classification = data.get('classification', {})
                is_duplicate = classification.get('is_duplicate', False)
                
                print(f"  [OK] Result: {'Duplicate' if is_duplicate else 'Not duplicate'}")
                
                if is_duplicate == test['should_be_duplicate']:
                    print(f"  [PASSED]")
                else:
                    print(f"  [FAILED] Expected {test['should_be_duplicate']}, got {is_duplicate}")
            else:
                print(f"  [FAILED] HTTP {response.status_code}")
        except Exception as e:
            print(f"  [FAILED] {str(e)}")

def test_location_detection():
    """Test area-based location detection"""
    print("\n" + "=" * 70)
    print("TEST 3: Area-Based Location Detection")
    print("=" * 70)
    
    test_cases = [
        {
            "text": "حادث في منطقة العليا في الرياض",
            "expected_city": "الرياض"
        },
        {
            "text": "بلاغ في حي الزهراء في جدة",
            "expected_city": "جدة"
        },
        {
            "text": "مشكلة في حي العزيزية في مكة",
            "expected_city": "مكة"
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\nTest Case {i}: {test['text']}")
        try:
            response = requests.post(f"{API_URL}/api/analyze", json={
                "text": test['text']
            })
            
            if response.status_code == 200:
                data = response.json()
                location = data.get('location', {})
                city = location.get('city', 'N/A')
                
                print(f"  [OK] Detected city: {city}")
                print(f"  [OK] Expected city: {test['expected_city']}")
                print(f"  [OK] Coordinates: ({location.get('latitude', 'N/A')}, {location.get('longitude', 'N/A')})")
                
                if city == test['expected_city']:
                    print(f"  [PASSED]")
                else:
                    print(f"  [WARNING] City mismatch")
            else:
                print(f"  [FAILED] HTTP {response.status_code}")
        except Exception as e:
            print(f"  [FAILED] {str(e)}")

def test_api_health():
    """Test API health endpoint"""
    print("\n" + "=" * 70)
    print("TEST 0: API Health Check")
    print("=" * 70)
    
    try:
        response = requests.get(f"{API_URL}/api/health")
        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] Status: {data.get('status', 'N/A')}")
            print(f"  [OK] Dataset records: {data.get('dataset_records', 0)}")
            print(f"  [OK] API key set: {data.get('api_key_set', False)}")
            print(f"  [PASSED] API is healthy")
            return True
        else:
            print(f"  [FAILED] HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"  [FAILED] Cannot connect to API - {str(e)}")
        print(f"  Make sure the backend server is running on {API_URL}")
        return False

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("KOLNA AMN MODEL TEST SUITE")
    print("=" * 70)
    
    # Check API health first
    if not test_api_health():
        print("\n[WARNING] Cannot proceed with tests. Please start the backend server first.")
        print("   Run: python backend.py")
        exit(1)
    
    # Run tests
    test_classification()
    test_location_detection()
    test_duplicate_detection()
    
    print("\n" + "=" * 70)
    print("TEST SUITE COMPLETED")
    print("=" * 70)
