"""
Test script to verify the API routes are correctly configured after the prefix fix
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from main import app

def check_routes():
    """Check the registered routes in the FastAPI app"""
    print("Registered routes:")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            methods = ', '.join(sorted(route.methods))
            print(f"  {methods} {route.path}")
    
    # Check specifically for KRS routes
    krs_routes = [route for route in app.routes if '/api/krs' in route.path]
    print(f"\nFound {len(krs_routes)} KRS routes:")
    for route in krs_routes:
        methods = ', '.join(sorted(route.methods))
        print(f"  {methods} {route.path}")
    
    # Check if there are any duplicate prefixes
    api_krs_count = sum(1 for route in app.routes if route.path.count('/api/krs') > 1)
    print(f"\nRoutes with duplicate '/api/krs' prefix: {api_krs_count}")
    
    if api_krs_count > 0:
        print("ERROR: Found routes with duplicate prefix!")
        for route in app.routes:
            if route.path.count('/api/krs') > 1:
                print(f"  Problematic route: {route.path}")
        return False
    else:
        print("SUCCESS: No duplicate prefixes found!")
        return True

if __name__ == "__main__":
    success = check_routes()
    if not success:
        sys.exit(1)