#!/usr/bin/env python3
"""
Comprehensive Test Suite for Taara Internet Monitor
Tests all system components including API, database, web interface, and data collection
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta

try:
    import requests
    from sqlalchemy import create_engine, text
    from sqlalchemy.orm import sessionmaker
    REQUESTS_AVAILABLE = True
    SQLALCHEMY_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    SQLALCHEMY_AVAILABLE = False

# Add the app directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.taara_api import TaaraAPI
from app.database import DataUsageRecord, ApiLog, SessionLocal, Base, create_tables
from app.data_collector import DataCollector
from app.main import app

class TestSuite:
    """Main test suite class"""
    
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.api_client = None
        self.test_results = []
        
    def log_test(self, test_name, status, message="", execution_time=0):
        """Log test results"""
        self.test_results.append({
            "test": test_name,
            "status": status,
            "message": message,
            "execution_time": execution_time,
            "timestamp": datetime.now().isoformat()
        })
        
    def print_result(self, test_name, status, message=""):
        """Print test result with formatting"""
        emoji = "✅" if status == "PASS" else "❌" if status == "FAIL" else "⚠️"
        print(f"{emoji} {test_name}: {status}")
        if message:
            print(f"   {message}")
        print()

    def test_environment_setup(self):
        """Test 1: Environment and Configuration"""
        print("=" * 60)
        print("TEST SUITE 1: ENVIRONMENT AND CONFIGURATION")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test environment variables
        required_env_vars = [
            'TAARA_PHONE_COUNTRY_CODE',
            'TAARA_PHONE_NUMBER', 
            'TAARA_PASSCODE',
            'TAARA_PARTNER_ID',
            'TAARA_HOTSPOT_ID'
        ]
        
        missing_vars = []
        for var in required_env_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            self.log_test("Environment Variables", "FAIL", f"Missing: {', '.join(missing_vars)}")
            self.print_result("Environment Variables", "FAIL", f"Missing: {', '.join(missing_vars)}")
        else:
            self.log_test("Environment Variables", "PASS", "All required variables present")
            self.print_result("Environment Variables", "PASS", "All required variables present")
        
        # Test database file existence
        db_file = "taara_monitoring.db"
        if os.path.exists(db_file):
            self.log_test("Database File", "PASS", f"Found {db_file}")
            self.print_result("Database File", "PASS", f"Found {db_file}")
        else:
            self.log_test("Database File", "WARNING", f"{db_file} not found, will be created")
            self.print_result("Database File", "WARNING", f"{db_file} not found, will be created")
        
        # Test requirements
        try:
            import fastapi, uvicorn, sqlalchemy, requests, plotly
            self.log_test("Python Dependencies", "PASS", "All packages available")
            self.print_result("Python Dependencies", "PASS", "All packages available")
        except ImportError as e:
            self.log_test("Python Dependencies", "FAIL", f"Missing package: {e}")
            self.print_result("Python Dependencies", "FAIL", f"Missing package: {e}")
        
        execution_time = time.time() - start_time
        print(f"Environment tests completed in {execution_time:.2f}s\n")

    def test_database_operations(self):
        """Test 2: Database Operations"""
        print("=" * 60)
        print("TEST SUITE 2: DATABASE OPERATIONS")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # Test database creation
            create_tables()
            self.log_test("Database Creation", "PASS", "Tables created successfully")
            self.print_result("Database Creation", "PASS", "Tables created successfully")
            
            # Test database connection
            session = SessionLocal()
            session.execute(text("SELECT 1"))
            session.close()
            self.log_test("Database Connection", "PASS", "Connection established")
            self.print_result("Database Connection", "PASS", "Connection established")
            
            # Test record insertion
            session = SessionLocal()
            test_record = DataUsageRecord(
                subscriber_id="test-id",
                plan_name="Test Plan",
                plan_id="test-plan-id",
                remaining_balance_gb=100.5,
                remaining_balance_bytes=107374182400,
                total_data_usage_bytes=1073741824,
                expires_in_days=30,
                is_active=True,
                is_home_plan=True
            )
            session.add(test_record)
            session.commit()
            
            # Verify insertion
            count = session.query(DataUsageRecord).filter(
                DataUsageRecord.subscriber_id == "test-id"
            ).count()
            session.close()
            
            if count > 0:
                self.log_test("Database Write", "PASS", "Test record inserted")
                self.print_result("Database Write", "PASS", "Test record inserted")
            else:
                self.log_test("Database Write", "FAIL", "Test record not found")
                self.print_result("Database Write", "FAIL", "Test record not found")
                
        except Exception as e:
            self.log_test("Database Operations", "FAIL", str(e))
            self.print_result("Database Operations", "FAIL", str(e))
        
        execution_time = time.time() - start_time
        print(f"Database tests completed in {execution_time:.2f}s\n")

    def test_taara_api(self):
        """Test 3: Taara API Integration"""
        print("=" * 60)
        print("TEST SUITE 3: TAARA API INTEGRATION")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # Initialize API client
            self.api_client = TaaraAPI(
                phone_country_code=os.getenv('TAARA_PHONE_COUNTRY_CODE', '254'),
                phone_number=os.getenv('TAARA_PHONE_NUMBER'),
                passcode=os.getenv('TAARA_PASSCODE'),
                partner_id=os.getenv('TAARA_PARTNER_ID'),
                hotspot_id=os.getenv('TAARA_HOTSPOT_ID')
            )
            
            # Test login
            login_start = time.time()
            login_result = self.api_client.login()
            login_time = time.time() - login_start
            
            if login_result['success']:
                self.log_test("API Login", "PASS", f"Login successful in {login_time:.2f}s")
                self.print_result("API Login", "PASS", f"Login successful in {login_time:.2f}s")
            else:
                self.log_test("API Login", "FAIL", login_result.get('error', 'Unknown error'))
                self.print_result("API Login", "FAIL", login_result.get('error', 'Unknown error'))
                return
            
            # Test bundle data retrieval
            bundle_start = time.time()
            bundle_result = self.api_client.get_customer_bundle()
            bundle_time = time.time() - bundle_start
            
            if bundle_result['success']:
                parsed_data = self.api_client.parse_bundle_data(bundle_result['data'])
                plan_count = len(parsed_data)
                self.log_test("Bundle Data Retrieval", "PASS", f"Retrieved {plan_count} plans in {bundle_time:.2f}s")
                self.print_result("Bundle Data Retrieval", "PASS", f"Retrieved {plan_count} plans in {bundle_time:.2f}s")
                
                # Test data parsing
                if parsed_data:
                    plan = parsed_data[0]
                    required_fields = ['plan_name', 'remaining_balance_gb', 'expires_in_days', 'is_active']
                    missing_fields = [field for field in required_fields if field not in plan]
                    
                    if not missing_fields:
                        self.log_test("Data Parsing", "PASS", "All required fields present")
                        self.print_result("Data Parsing", "PASS", "All required fields present")
                    else:
                        self.log_test("Data Parsing", "FAIL", f"Missing fields: {missing_fields}")
                        self.print_result("Data Parsing", "FAIL", f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Data Parsing", "WARNING", "No plan data to parse")
                    self.print_result("Data Parsing", "WARNING", "No plan data to parse")
            else:
                self.log_test("Bundle Data Retrieval", "FAIL", bundle_result.get('error', 'Unknown error'))
                self.print_result("Bundle Data Retrieval", "FAIL", bundle_result.get('error', 'Unknown error'))
            
            # Test logout
            logout_result = self.api_client.logout()
            if logout_result['success']:
                self.log_test("API Logout", "PASS", "Logout successful")
                self.print_result("API Logout", "PASS", "Logout successful")
            else:
                self.log_test("API Logout", "FAIL", logout_result.get('error', 'Unknown error'))
                self.print_result("API Logout", "FAIL", logout_result.get('error', 'Unknown error'))
                
        except Exception as e:
            self.log_test("API Integration", "FAIL", str(e))
            self.print_result("API Integration", "FAIL", str(e))
        
        execution_time = time.time() - start_time
        print(f"API tests completed in {execution_time:.2f}s\n")

    def test_data_collector(self):
        """Test 4: Data Collection System"""
        print("=" * 60)
        print("TEST SUITE 4: DATA COLLECTION SYSTEM")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # Test data collector initialization
            collector = DataCollector()
            self.log_test("Data Collector Init", "PASS", "Collector initialized")
            self.print_result("Data Collector Init", "PASS", "Collector initialized")
            
            # Test data collection
            collection_start = time.time()
            result = collector.collect_data()
            collection_time = time.time() - collection_start
            
            if result:
                self.log_test("Data Collection", "PASS", f"Collection completed in {collection_time:.2f}s")
                self.print_result("Data Collection", "PASS", f"Collection completed in {collection_time:.2f}s")
                
                # Verify data was stored
                session = SessionLocal()
                recent_records = session.query(DataUsageRecord).filter(
                    DataUsageRecord.timestamp >= datetime.now() - timedelta(minutes=5)
                ).count()
                session.close()
                
                if recent_records > 0:
                    self.log_test("Data Storage", "PASS", f"Stored {recent_records} records")
                    self.print_result("Data Storage", "PASS", f"Stored {recent_records} records")
                else:
                    self.log_test("Data Storage", "WARNING", "No recent records found")
                    self.print_result("Data Storage", "WARNING", "No recent records found")
            else:
                self.log_test("Data Collection", "FAIL", "Collection failed")
                self.print_result("Data Collection", "FAIL", "Collection failed")
                
        except Exception as e:
            self.log_test("Data Collection System", "FAIL", str(e))
            self.print_result("Data Collection System", "FAIL", str(e))
        
        execution_time = time.time() - start_time
        print(f"Data collection tests completed in {execution_time:.2f}s\n")

    def test_web_api_endpoints(self):
        """Test 5: Web API Endpoints"""
        print("=" * 60)
        print("TEST SUITE 5: WEB API ENDPOINTS")
        print("=" * 60)
        
        start_time = time.time()
        
        endpoints = [
            ("/api/data", "GET", "Latest Data"),
            ("/api/stats", "GET", "Statistics"),
            ("/api/history", "GET", "Usage History"),
            ("/api/collect", "POST", "Manual Collection")
        ]
        
        for endpoint, method, name in endpoints:
            try:
                endpoint_start = time.time()
                if method == "GET":
                    response = requests.get(f"{self.base_url}{endpoint}", timeout=10)
                else:
                    response = requests.post(f"{self.base_url}{endpoint}", timeout=10)
                endpoint_time = time.time() - endpoint_start
                
                if response.status_code == 200:
                    try:
                        data = response.json()
                        self.log_test(f"API {name}", "PASS", f"Status 200, {endpoint_time:.2f}s")
                        self.print_result(f"API {name}", "PASS", f"Status 200, Response time: {endpoint_time:.2f}s")
                    except json.JSONDecodeError:
                        self.log_test(f"API {name}", "FAIL", "Invalid JSON response")
                        self.print_result(f"API {name}", "FAIL", "Invalid JSON response")
                else:
                    self.log_test(f"API {name}", "FAIL", f"Status {response.status_code}")
                    self.print_result(f"API {name}", "FAIL", f"Status {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.log_test(f"API {name}", "FAIL", f"Request failed: {e}")
                self.print_result(f"API {name}", "FAIL", f"Request failed: {e}")
        
        execution_time = time.time() - start_time
        print(f"API endpoint tests completed in {execution_time:.2f}s\n")

    def test_dashboard_interface(self):
        """Test 6: Dashboard Web Interface"""
        print("=" * 60)
        print("TEST SUITE 6: DASHBOARD WEB INTERFACE")
        print("=" * 60)
        
        start_time = time.time()
        
        try:
            # Test main dashboard
            dashboard_start = time.time()
            response = requests.get(self.base_url, timeout=10)
            dashboard_time = time.time() - dashboard_start
            
            if response.status_code == 200:
                html_content = response.text
                
                # Check for key elements
                required_elements = [
                    "Taara Internet Monitor",
                    "Current Balance",
                    "Days Remaining",
                    "Usage Rate"
                ]
                
                missing_elements = []
                for element in required_elements:
                    if element not in html_content:
                        missing_elements.append(element)
                
                if not missing_elements:
                    self.log_test("Dashboard Content", "PASS", f"All elements present, {dashboard_time:.2f}s")
                    self.print_result("Dashboard Content", "PASS", f"All elements present, Load time: {dashboard_time:.2f}s")
                else:
                    self.log_test("Dashboard Content", "FAIL", f"Missing: {missing_elements}")
                    self.print_result("Dashboard Content", "FAIL", f"Missing: {missing_elements}")
                    
                # Check for responsive design indicators
                responsive_indicators = ["viewport", "responsive", "bootstrap", "mobile"]
                found_responsive = any(indicator in html_content.lower() for indicator in responsive_indicators)
                
                if found_responsive:
                    self.log_test("Responsive Design", "PASS", "Responsive indicators found")
                    self.print_result("Responsive Design", "PASS", "Responsive indicators found")
                else:
                    self.log_test("Responsive Design", "WARNING", "No responsive indicators found")
                    self.print_result("Responsive Design", "WARNING", "No responsive indicators found")
                    
            else:
                self.log_test("Dashboard Access", "FAIL", f"Status {response.status_code}")
                self.print_result("Dashboard Access", "FAIL", f"Status {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            self.log_test("Dashboard Interface", "FAIL", f"Request failed: {e}")
            self.print_result("Dashboard Interface", "FAIL", f"Request failed: {e}")
        
        execution_time = time.time() - start_time
        print(f"Dashboard tests completed in {execution_time:.2f}s\n")

    def test_performance_stress(self):
        """Test 7: Performance and Stress Testing"""
        print("=" * 60)
        print("TEST SUITE 7: PERFORMANCE AND STRESS TESTING")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test multiple concurrent API calls
        import concurrent.futures
        import threading
        
        def make_api_call():
            try:
                response = requests.get(f"{self.base_url}/api/data", timeout=5)
                return response.status_code == 200, response.elapsed.total_seconds()
            except:
                return False, 0
        
        # Run 10 concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            stress_start = time.time()
            futures = [executor.submit(make_api_call) for _ in range(10)]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            stress_time = time.time() - stress_start
        
        successful_requests = sum(1 for success, _ in results if success)
        response_times = [time for success, time in results if success]
        avg_response_time = sum(response_times) / len(response_times) if response_times else 0
        
        if successful_requests >= 8:  # Allow 2 failures
            self.log_test("Concurrent Requests", "PASS", f"{successful_requests}/10 successful, avg: {avg_response_time:.2f}s")
            self.print_result("Concurrent Requests", "PASS", f"{successful_requests}/10 successful, Avg response: {avg_response_time:.2f}s")
        else:
            self.log_test("Concurrent Requests", "FAIL", f"Only {successful_requests}/10 successful")
            self.print_result("Concurrent Requests", "FAIL", f"Only {successful_requests}/10 successful")
        
        # Test database query performance
        session = SessionLocal()
        query_start = time.time()
        records = session.query(DataUsageRecord).limit(100).all()
        query_time = time.time() - query_start
        session.close()
        
        if query_time < 1.0:  # Should be fast for 100 records
            self.log_test("Database Performance", "PASS", f"100 records in {query_time:.3f}s")
            self.print_result("Database Performance", "PASS", f"100 records in {query_time:.3f}s")
        else:
            self.log_test("Database Performance", "WARNING", f"Slow query: {query_time:.3f}s")
            self.print_result("Database Performance", "WARNING", f"Slow query: {query_time:.3f}s")
        
        execution_time = time.time() - start_time
        print(f"Performance tests completed in {execution_time:.2f}s\n")

    def test_error_handling(self):
        """Test 8: Error Handling and Edge Cases"""
        print("=" * 60)
        print("TEST SUITE 8: ERROR HANDLING AND EDGE CASES")
        print("=" * 60)
        
        start_time = time.time()
        
        # Test invalid API endpoints
        invalid_endpoints = [
            "/api/invalid",
            "/api/data/999999",
            "/nonexistent"
        ]
        
        for endpoint in invalid_endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code in [404, 422]:  # Expected error codes
                    self.log_test(f"Invalid Endpoint {endpoint}", "PASS", f"Proper error: {response.status_code}")
                    self.print_result(f"Invalid Endpoint {endpoint}", "PASS", f"Proper error: {response.status_code}")
                else:
                    self.log_test(f"Invalid Endpoint {endpoint}", "WARNING", f"Unexpected: {response.status_code}")
                    self.print_result(f"Invalid Endpoint {endpoint}", "WARNING", f"Unexpected: {response.status_code}")
            except:
                self.log_test(f"Invalid Endpoint {endpoint}", "FAIL", "Request failed")
                self.print_result(f"Invalid Endpoint {endpoint}", "FAIL", "Request failed")
        
        # Test API with invalid credentials (temporary)
        try:
            invalid_api = TaaraAPI(
                phone_country_code="000",
                phone_number="0000000000",
                passcode="0000",
                partner_id="0000",
                hotspot_id="0000"
            )
            
            login_result = invalid_api.login()
            if not login_result['success']:
                self.log_test("Invalid Credentials", "PASS", "Properly rejected invalid credentials")
                self.print_result("Invalid Credentials", "PASS", "Properly rejected invalid credentials")
            else:
                self.log_test("Invalid Credentials", "WARNING", "Invalid credentials accepted")
                self.print_result("Invalid Credentials", "WARNING", "Invalid credentials accepted")
        except Exception as e:
            self.log_test("Invalid Credentials", "PASS", f"Exception caught: {type(e).__name__}")
            self.print_result("Invalid Credentials", "PASS", f"Exception caught: {type(e).__name__}")
        
        execution_time = time.time() - start_time
        print(f"Error handling tests completed in {execution_time:.2f}s\n")

    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("=" * 60)
        print("COMPREHENSIVE TEST REPORT")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['status'] == 'PASS'])
        failed_tests = len([t for t in self.test_results if t['status'] == 'FAIL'])
        warning_tests = len([t for t in self.test_results if t['status'] == 'WARNING'])
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests} ({passed_tests/total_tests*100:.1f}%)")
        print(f"Failed: {failed_tests} ({failed_tests/total_tests*100:.1f}%)")
        print(f"Warnings: {warning_tests} ({warning_tests/total_tests*100:.1f}%)")
        print()
        
        # Detailed results
        print("DETAILED RESULTS:")
        print("-" * 40)
        
        for result in self.test_results:
            status_emoji = "✅" if result['status'] == 'PASS' else "❌" if result['status'] == 'FAIL' else "⚠️"
            print(f"{status_emoji} {result['test']}: {result['status']}")
            if result['message']:
                print(f"   {result['message']}")
            if result['execution_time'] > 0:
                print(f"   Execution time: {result['execution_time']:.2f}s")
            print()
        
        # Save report to file
        report_file = f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump({
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed_tests,
                    "failed": failed_tests,
                    "warnings": warning_tests,
                    "success_rate": passed_tests/total_tests*100
                },
                "results": self.test_results,
                "generated_at": datetime.now().isoformat()
            }, f, indent=2)
        
        print(f"📄 Detailed report saved to: {report_file}")
        
        # Overall assessment
        success_rate = passed_tests / total_tests * 100
        if success_rate >= 90:
            print("🎉 EXCELLENT: System is performing very well!")
        elif success_rate >= 75:
            print("👍 GOOD: System is working well with minor issues")
        elif success_rate >= 50:
            print("⚠️ FAIR: System has some issues that need attention")
        else:
            print("🚨 POOR: System has significant issues requiring immediate attention")

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 STARTING COMPREHENSIVE TAARA SYSTEM TESTS")
        print("=" * 60)
        
        overall_start = time.time()
        
        # Run all test suites
        self.test_environment_setup()
        self.test_database_operations()
        self.test_taara_api()
        self.test_data_collector()
        self.test_web_api_endpoints()
        self.test_dashboard_interface()
        self.test_performance_stress()
        self.test_error_handling()
        
        overall_time = time.time() - overall_start
        
        print(f"🏁 ALL TESTS COMPLETED in {overall_time:.2f}s")
        print()
        
        # Generate final report
        self.generate_test_report()

def main():
    """Main test execution"""
    test_suite = TestSuite()
    test_suite.run_all_tests()

if __name__ == "__main__":
    main()
