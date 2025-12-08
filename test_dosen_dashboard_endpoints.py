"""
Test script to verify the new KRS endpoints for course-based student lookup
"""
import requests
import json

# Configuration - adjust these based on your running server
BASE_URL = "http://localhost:8000"

def test_new_endpoints():
    print("Testing new KRS endpoints...")
    
    # First, let's test the login to get a token
    print("\n1. Testing login to get token...")
    try:
        login_response = requests.post(f"{BASE_URL}/api/auth/login", 
                                     json={"username": "admin", "password": "admin"})
        if login_response.status_code == 200:
            token = login_response.json().get("access_token")
            print("✓ Login successful, got token")
            headers = {"Authorization": f"Bearer {token}"}
        else:
            print("✗ Login failed")
            print("Response:", login_response.json())
            return
    except Exception as e:
        print(f"✗ Error during login: {e}")
        return
    
    # Test the new endpoint to get students by course
    print("\n2. Testing /api/krs/course/{matakuliah_id} endpoint...")
    try:
        # First, let's get a list of courses to have an ID to test with
        matakuliah_response = requests.get(f"{BASE_URL}/api/matakuliah", headers=headers)
        if matakuliah_response.status_code == 200:
            matakuliah_list = matakuliah_response.json()
            if matakuliah_list:
                # Use the first course ID as an example
                example_course_id = matakuliah_list[0]['id']
                example_course_kode = matakuliah_list[0]['kode']
                print(f"Using course ID: {example_course_id}, kode: {example_course_kode}")
                
                # Test the new endpoint
                students_response = requests.get(f"{BASE_URL}/api/krs/course/{example_course_id}", headers=headers)
                if students_response.status_code == 200:
                    students = students_response.json()
                    print(f"✓ Successfully got {len(students)} students for course ID {example_course_id}")
                    if students:
                        print("Sample student:", students[0])
                else:
                    print(f"✗ Failed to get students for course {example_course_id}")
                    print("Response:", students_response.json())
            else:
                print("No matakuliah found to test with")
        else:
            print("Failed to get matakuliah list")
            print("Response:", matakuliah_response.json())
    except Exception as e:
        print(f"✗ Error testing course endpoint: {e}")
    
    # Test the new endpoint to get course by kode
    print("\n3. Testing /api/krs/kode/{kode_mk} endpoint...")
    try:
        # Use the example course kode from above or use a default
        if 'example_course_kode' in locals():
            kode = example_course_kode
        else:
            # Use a default kode if no matakuliah was found
            kode = "IF101"  # Common default
        
        course_by_kode_response = requests.get(f"{BASE_URL}/api/krs/kode/{kode}", headers=headers)
        if course_by_kode_response.status_code == 200:
            course = course_by_kode_response.json()
            print(f"✓ Successfully got course by kode {kode}:")
            print(f"   ID: {course.get('id')}, Name: {course.get('nama')}")
        elif course_by_kode_response.status_code == 404:
            print(f"✓ Correctly returned 404 for non-existent course kode: {kode}")
        else:
            print(f"✗ Failed to get course by kode {kode}")
            print("Response:", course_by_kode_response.json())
    except Exception as e:
        print(f"✗ Error testing course by kode endpoint: {e}")
    
    print("\nTest completed!")

if __name__ == "__main__":
    test_new_endpoints()