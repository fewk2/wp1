"""
Knowledge API Validation Script
Comprehensive validation of all knowledge API endpoints
"""
import sys
import json
from server import app
from config import get_config

config = get_config()


def validate():
    """Run comprehensive validation"""
    app.config['TESTING'] = True
    client = app.test_client()
    auth_headers = {'X-API-Key': config.API_SECRET_KEY}
    no_auth_headers = {}
    
    print("=" * 70)
    print("KNOWLEDGE API VALIDATION")
    print("=" * 70)
    
    tests = []
    
    # Test 1: Authentication
    print("\n[1/12] Testing authentication...")
    response = client.get('/api/knowledge/entries', headers=no_auth_headers)
    tests.append(('Auth rejection', response.status_code == 401))
    
    # Test 2: List entries with auth
    print("[2/12] Testing list entries...")
    response = client.get('/api/knowledge/entries', headers=auth_headers)
    tests.append(('List entries', response.status_code == 200))
    data = response.get_json()
    tests.append(('Response format', data and 'success' in data and 'data' in data))
    
    # Test 3: Pagination
    print("[3/12] Testing pagination...")
    response = client.get('/api/knowledge/entries?page=1&page_size=5', headers=auth_headers)
    tests.append(('Pagination', response.status_code == 200))
    data = response.get_json()
    if data and 'data' in data:
        pagination = data['data'].get('pagination', {})
        tests.append(('Pagination metadata', 
                     pagination.get('page') == 1 and pagination.get('page_size') == 5))
    
    # Test 4: Invalid sort field
    print("[4/12] Testing invalid sort field...")
    response = client.get('/api/knowledge/entries?sort=invalid', headers=auth_headers)
    tests.append(('Invalid sort rejection', response.status_code == 400))
    
    # Test 5: Invalid sort order
    print("[5/12] Testing invalid sort order...")
    response = client.get('/api/knowledge/entries?order=INVALID', headers=auth_headers)
    tests.append(('Invalid order rejection', response.status_code == 400))
    
    # Test 6: Tags endpoint
    print("[6/12] Testing tags endpoint...")
    response = client.get('/api/knowledge/tags', headers=auth_headers)
    tests.append(('Tags endpoint', response.status_code == 200))
    data = response.get_json()
    tests.append(('Tags format', data and 'data' in data and 'tags' in data['data']))
    
    # Test 7: Statuses endpoint
    print("[7/12] Testing statuses endpoint...")
    response = client.get('/api/knowledge/statuses', headers=auth_headers)
    tests.append(('Statuses endpoint', response.status_code == 200))
    data = response.get_json()
    tests.append(('Statuses format', data and 'data' in data and 'statuses' in data['data']))
    
    # Test 8: CSV export
    print("[8/12] Testing CSV export...")
    response = client.get('/api/knowledge/export', headers=auth_headers)
    tests.append(('CSV export', response.status_code == 200))
    tests.append(('CSV content type', 'text/csv' in response.content_type))
    
    # Test 9: CSV export with custom fields
    print("[9/12] Testing CSV export with fields...")
    response = client.get('/api/knowledge/export?fields=article_id,status', headers=auth_headers)
    tests.append(('CSV custom fields', response.status_code == 200))
    
    # Test 10: CSV export with invalid fields
    print("[10/12] Testing CSV export with invalid fields...")
    response = client.get('/api/knowledge/export?fields=invalid_field', headers=auth_headers)
    tests.append(('CSV invalid fields rejection', response.status_code == 400))
    
    # Test 11: Entry detail endpoint
    print("[11/12] Testing entry detail endpoint...")
    response = client.get('/api/knowledge/entry/test_id', headers=auth_headers)
    tests.append(('Entry detail', response.status_code in [200, 404]))
    
    # Test 12: Static routes
    print("[12/12] Testing static routes...")
    response = client.get('/kb')
    tests.append(('KB route', response.status_code in [200, 404]))
    
    # Summary
    print("\n" + "=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)
    
    passed = sum(1 for _, result in tests if result)
    total = len(tests)
    
    for name, result in tests:
        status = "✓" if result else "✗"
        print(f"{status} {name}")
    
    print("-" * 70)
    print(f"Total: {passed}/{total} tests passed ({passed*100//total}%)")
    
    if passed == total:
        print("\n✓ ALL VALIDATIONS PASSED")
        return True
    else:
        print(f"\n✗ {total - passed} VALIDATIONS FAILED")
        return False


if __name__ == '__main__':
    try:
        success = validate()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ VALIDATION ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
