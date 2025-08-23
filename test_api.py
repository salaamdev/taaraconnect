"""
Test script for Taara API
Run this to verify your API credentials work
"""

import os
import sys

# Add the app directory to the path
sys.path.append('.')

from app.taara_api import TaaraAPI

def test_api():
    """Test the Taara API connection"""
    
    print("Testing Taara API connection...")
    print("=" * 50)
    
    # Initialize API client
    api = TaaraAPI(
        phone_country_code=os.getenv('TAARA_PHONE_COUNTRY_CODE', '254'),
        phone_number=os.getenv('TAARA_PHONE_NUMBER', '718920243'),
        passcode=os.getenv('TAARA_PASSCODE', '888344'),
        partner_id=os.getenv('TAARA_PARTNER_ID', '313324693'),
        hotspot_id=os.getenv('TAARA_HOTSPOT_ID', '596370186')
    )
    
    # Test login
    print("1. Testing login...")
    login_result = api.login()
    
    if login_result['success']:
        print("✅ Login successful!")
        print(f"   Access token: {login_result['access_token'][:50]}...")
        print(f"   Subscriber ID: {login_result.get('subscriber_id', 'Not found')}")
        print(f"   Response time: {login_result.get('response_time_ms', 0):.2f}ms")
    else:
        print("❌ Login failed!")
        print(f"   Error: {login_result.get('error', 'Unknown error')}")
        return False
    
    print()
    
    # Test getting bundle data
    print("2. Testing bundle data retrieval...")
    bundle_result = api.get_customer_bundle()
    
    if bundle_result['success']:
        print("✅ Bundle data retrieval successful!")
        
        # Parse the data
        parsed_data = api.parse_bundle_data(bundle_result['data'])
        
        print(f"   Found {len(parsed_data)} active plans:")
        for plan in parsed_data:
            print(f"   - {plan['plan_name']}: {plan['remaining_balance_gb']:.1f} GB remaining")
            print(f"     Expires in: {plan['expires_in_days']} days")
            print(f"     Active: {plan['is_active']}")
            print()
        
    else:
        print("❌ Bundle data retrieval failed!")
        print(f"   Error: {bundle_result.get('error', 'Unknown error')}")
        return False
    
    print()
    
    # Test logout
    print("3. Testing logout...")
    logout_result = api.logout()
    
    if logout_result['success']:
        print("✅ Logout successful!")
        print(f"   Response time: {logout_result.get('response_time_ms', 0):.2f}ms")
    else:
        print("❌ Logout failed!")
        print(f"   Error: {logout_result.get('error', 'Unknown error')}")
    
    print()
    print("=" * 50)
    print("✅ API test completed successfully!")
    print("Your credentials are working correctly.")
    
    return True

if __name__ == "__main__":
    try:
        success = test_api()
        if not success:
            print("\n❌ API test failed. Please check your credentials in the .env file.")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during API test: {str(e)}")
        print("Please check your internet connection and credentials.")
        sys.exit(1)
