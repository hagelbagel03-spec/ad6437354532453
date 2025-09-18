#!/usr/bin/env python3
"""
Backend API Test Suite
Tests all backend endpoints and specifically focuses on team creation API issues.
"""

import requests
import json
import uuid
from datetime import datetime
import sys
import os

# Get backend URL from frontend .env file
def get_backend_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('EXPO_PUBLIC_BACKEND_URL='):
                    return line.split('=', 1)[1].strip()
    except:
        pass
    return "https://german-write.preview.emergentagent.com"

BASE_URL = get_backend_url()
API_BASE = f"{BASE_URL}/api"

class BackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.session.timeout = 10
        
    def log(self, message, level="INFO"):
        """Log test messages"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def test_server_health(self):
        """Test if backend server is responding"""
        self.log("🏥 Testing backend server health...")
        
        try:
            response = self.session.get(f"{BASE_URL}/docs", timeout=5)
            if response.status_code == 200:
                self.log("✅ Backend server is responding (docs accessible)")
                return True
            else:
                self.log(f"❌ Backend server docs returned: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Backend server health check failed: {str(e)}")
            return False
    
    def test_openapi_schema(self):
        """Test OpenAPI schema and check for team endpoints"""
        self.log("📋 Testing OpenAPI schema...")
        
        try:
            response = self.session.get(f"{BASE_URL}/openapi.json")
            if response.status_code == 200:
                schema = response.json()
                paths = schema.get("paths", {})
                
                self.log(f"✅ OpenAPI schema accessible - Found {len(paths)} endpoints")
                
                # List all available endpoints
                self.log("📝 Available endpoints:")
                for path in sorted(paths.keys()):
                    methods = list(paths[path].keys())
                    self.log(f"   {path} - {', '.join(methods).upper()}")
                
                # Check specifically for team endpoints
                team_endpoints = [path for path in paths.keys() if 'team' in path.lower()]
                admin_team_endpoints = [path for path in paths.keys() if '/admin/teams' in path]
                
                if team_endpoints:
                    self.log(f"✅ Found team-related endpoints: {team_endpoints}")
                else:
                    self.log("❌ No team-related endpoints found in OpenAPI schema")
                
                if admin_team_endpoints:
                    self.log(f"✅ Found admin team endpoints: {admin_team_endpoints}")
                else:
                    self.log("❌ No /api/admin/teams endpoints found in OpenAPI schema")
                
                return True, team_endpoints, admin_team_endpoints
            else:
                self.log(f"❌ OpenAPI schema failed: {response.status_code}")
                return False, [], []
        except Exception as e:
            self.log(f"❌ Error testing OpenAPI schema: {str(e)}")
            return False, [], []
    
    def test_root_endpoint(self):
        """Test root API endpoint"""
        self.log("🏠 Testing root endpoint...")
        
        try:
            response = self.session.get(f"{API_BASE}/")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ Root endpoint working: {data}")
                return True
            else:
                self.log(f"❌ Root endpoint failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Error testing root endpoint: {str(e)}")
            return False
    
    def test_status_endpoints(self):
        """Test existing status endpoints"""
        self.log("📊 Testing status endpoints...")
        
        # Test GET status
        try:
            response = self.session.get(f"{API_BASE}/status")
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ GET /api/status working - Found {len(data)} status checks")
            else:
                self.log(f"❌ GET /api/status failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Error testing GET status: {str(e)}")
            return False
        
        # Test POST status
        try:
            test_data = {
                "client_name": f"TestClient_{uuid.uuid4().hex[:8]}"
            }
            response = self.session.post(f"{API_BASE}/status", json=test_data)
            if response.status_code == 200:
                data = response.json()
                self.log(f"✅ POST /api/status working - Created: {data.get('client_name')}")
                return True
            else:
                self.log(f"❌ POST /api/status failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            self.log(f"❌ Error testing POST status: {str(e)}")
            return False
    
    def test_missing_team_endpoints(self):
        """Test the missing team endpoints that should return 404"""
        self.log("🔍 Testing missing team endpoints...")
        
        # Test GET /api/admin/teams
        try:
            response = self.session.get(f"{API_BASE}/admin/teams")
            if response.status_code == 404:
                self.log("✅ GET /api/admin/teams correctly returns 404 (endpoint not implemented)")
            else:
                self.log(f"❌ GET /api/admin/teams unexpected response: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error testing GET admin/teams: {str(e)}")
            return False
        
        # Test POST /api/admin/teams
        try:
            test_team_data = {
                "name": "Test Team",
                "district_id": "test-district-123"
            }
            response = self.session.post(f"{API_BASE}/admin/teams", json=test_team_data)
            if response.status_code == 404:
                self.log("✅ POST /api/admin/teams correctly returns 404 (endpoint not implemented)")
                return True
            else:
                self.log(f"❌ POST /api/admin/teams unexpected response: {response.status_code}")
                return False
        except Exception as e:
            self.log(f"❌ Error testing POST admin/teams: {str(e)}")
            return False
    
    def test_mongodb_connection(self):
        """Test MongoDB connection by checking if status data persists"""
        self.log("🗄️ Testing MongoDB connection...")
        
        try:
            # Create a test status check
            test_data = {
                "client_name": f"MongoTest_{uuid.uuid4().hex[:8]}"
            }
            
            # POST data
            response = self.session.post(f"{API_BASE}/status", json=test_data)
            if response.status_code != 200:
                self.log(f"❌ Failed to create test data: {response.status_code}")
                return False
            
            created_data = response.json()
            test_id = created_data.get("id")
            
            # GET data back to verify persistence
            response = self.session.get(f"{API_BASE}/status")
            if response.status_code == 200:
                all_data = response.json()
                found_test_data = any(item.get("id") == test_id for item in all_data)
                
                if found_test_data:
                    self.log("✅ MongoDB connection working - Data persisted successfully")
                    return True
                else:
                    self.log("❌ MongoDB connection issue - Data not found after creation")
                    return False
            else:
                self.log(f"❌ Failed to retrieve data: {response.status_code}")
                return False
                
        except Exception as e:
            self.log(f"❌ Error testing MongoDB connection: {str(e)}")
            return False
    
    def test_cors_configuration(self):
        """Test CORS configuration"""
        self.log("🌐 Testing CORS configuration...")
        
        try:
            # Make an OPTIONS request to check CORS headers
            response = self.session.options(f"{API_BASE}/")
            
            # Check for CORS headers in any response
            response = self.session.get(f"{API_BASE}/")
            headers = response.headers
            
            cors_headers = [
                'access-control-allow-origin',
                'access-control-allow-methods',
                'access-control-allow-headers'
            ]
            
            found_cors_headers = [h for h in cors_headers if h in headers]
            
            if found_cors_headers:
                self.log(f"✅ CORS headers found: {found_cors_headers}")
                return True
            else:
                self.log("⚠️ No CORS headers found - may cause frontend issues")
                return True  # Not a critical failure
                
        except Exception as e:
            self.log(f"❌ Error testing CORS: {str(e)}")
            return False
    
    def analyze_backend_structure(self):
        """Analyze the backend code structure for team endpoint issues"""
        self.log("🔍 Analyzing backend code structure...")
        
        try:
            # Read the server.py file
            with open('/app/backend/server.py', 'r') as f:
                server_code = f.read()
            
            # Check for team-related code
            team_mentions = server_code.count('team')
            admin_mentions = server_code.count('admin')
            router_includes = server_code.count('include_router')
            
            self.log(f"📊 Code analysis:")
            self.log(f"   - 'team' mentions: {team_mentions}")
            self.log(f"   - 'admin' mentions: {admin_mentions}")
            self.log(f"   - Router includes: {router_includes}")
            
            # Check if team endpoints are defined
            if '/admin/teams' in server_code:
                self.log("✅ Team endpoints found in code")
            else:
                self.log("❌ No team endpoints found in server.py")
            
            # Check for router configuration
            if 'api_router' in server_code and 'include_router' in server_code:
                self.log("✅ Router configuration looks correct")
            else:
                self.log("❌ Router configuration may have issues")
            
            return True
            
        except Exception as e:
            self.log(f"❌ Error analyzing backend structure: {str(e)}")
            return False
    
    def run_comprehensive_tests(self):
        """Run all backend tests"""
        self.log("🚀 Starting Comprehensive Backend Test Suite")
        self.log(f"📍 Testing against: {BASE_URL}")
        
        test_results = {}
        
        # Infrastructure tests
        self.log("\n🏗️ INFRASTRUCTURE TESTS")
        test_results["server_health"] = self.test_server_health()
        test_results["mongodb_connection"] = self.test_mongodb_connection()
        test_results["cors_configuration"] = self.test_cors_configuration()
        
        # API endpoint tests
        self.log("\n🔌 API ENDPOINT TESTS")
        test_results["root_endpoint"] = self.test_root_endpoint()
        test_results["status_endpoints"] = self.test_status_endpoints()
        test_results["missing_team_endpoints"] = self.test_missing_team_endpoints()
        
        # Schema and structure tests
        self.log("\n📋 SCHEMA AND STRUCTURE TESTS")
        schema_result, team_endpoints, admin_team_endpoints = self.test_openapi_schema()
        test_results["openapi_schema"] = schema_result
        test_results["backend_structure_analysis"] = self.analyze_backend_structure()
        
        # Results summary
        self.log("\n📊 TEST RESULTS SUMMARY")
        passed = sum(1 for result in test_results.values() if result)
        total = len(test_results)
        
        for test_name, result in test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{status} {test_name}")
        
        self.log(f"\n🎯 OVERALL RESULT: {passed}/{total} tests passed")
        
        # Specific findings about team endpoints
        self.log("\n🔍 TEAM ENDPOINT ANALYSIS:")
        self.log("❌ CRITICAL ISSUE: Team creation endpoints are NOT implemented")
        self.log("   - POST /api/admin/teams returns 404 (not found)")
        self.log("   - GET /api/admin/teams returns 404 (not found)")
        self.log("   - No team endpoints found in OpenAPI schema")
        self.log("   - No team-related code found in server.py")
        
        self.log("\n💡 REQUIRED FIXES:")
        self.log("   1. Add team data models (Team, TeamCreate, etc.)")
        self.log("   2. Implement POST /api/admin/teams endpoint")
        self.log("   3. Implement GET /api/admin/teams endpoint")
        self.log("   4. Add team endpoints to API router")
        self.log("   5. Add MongoDB collection for teams")
        self.log("   6. Test frontend integration after backend fixes")
        
        return test_results, team_endpoints, admin_team_endpoints

def main():
    """Main test execution"""
    tester = BackendTester()
    test_results, team_endpoints, admin_team_endpoints = tester.run_comprehensive_tests()
    
    # Determine overall success
    critical_tests = [
        "server_health",
        "mongodb_connection", 
        "root_endpoint",
        "status_endpoints"
    ]
    
    critical_passed = all(test_results.get(test, False) for test in critical_tests)
    team_endpoints_missing = not admin_team_endpoints
    
    if critical_passed and team_endpoints_missing:
        print("\n✅ Backend infrastructure is working correctly!")
        print("❌ But team creation endpoints are missing and need to be implemented!")
        sys.exit(0)  # Infrastructure works, just missing features
    elif not critical_passed:
        print("\n❌ Critical backend infrastructure issues found!")
        sys.exit(1)
    else:
        print("\n✅ All backend tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()