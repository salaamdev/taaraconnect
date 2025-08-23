import requests
import time
import json
from datetime import datetime
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

class TaaraAPI:
    def __init__(self, phone_country_code: str, phone_number: str, passcode: str, 
                 partner_id: str, hotspot_id: str):
        self.phone_country_code = phone_country_code
        self.phone_number = phone_number
        self.passcode = passcode
        self.partner_id = partner_id
        self.hotspot_id = hotspot_id
        self.access_token: Optional[str] = None
        self.subscriber_id: Optional[str] = None
        
        # API URLs
        self.login_url = "https://share.taara.company/v1/users/subscriber/login"
        self.bundle_url = f"https://share.taara.company/v1/customers/get-customer-bundle?hotspotId={hotspot_id}"
        self.hotspot_config_url = f"https://share.taara.company/v1/hotspot/GetHotspotConfig?hotspotId={hotspot_id}"
        self.logout_url = "https://share.taara.company/v1/users/subscriber/logout"
        
        # Headers template
        self.base_headers = {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-US,en;q=0.9",
            "content-type": "application/json",
            "sec-ch-ua": '"Not;A=Brand";v="99", "Microsoft Edge";v="139", "Chromium";v="139"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
        }

    def login(self) -> Dict[str, Any]:
        """Login to Taara API and get access token"""
        payload = {
            "phoneNumber": {
                "countryCode": self.phone_country_code,
                "nationalNumber": self.phone_number
            },
            "passcode": self.passcode,
            "partnerId": self.partner_id
        }
        
        headers = self.base_headers.copy()
        headers["referer"] = f"https://share.taara.company/cp/customers/login?hotspotId={self.hotspot_id}"
        
        try:
            start_time = time.time()
            response = requests.post(
                self.login_url, 
                json=payload, 
                headers=headers,
                timeout=30
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code in [200, 201]:
                data = response.json()
                self.access_token = data.get("accessToken")
                
                # Extract subscriber ID from token (JWT decode)
                if self.access_token:
                    import base64
                    try:
                        # Simple JWT decode without verification for subscriber ID
                        parts = self.access_token.split('.')
                        payload_part = parts[1]
                        # Add padding if needed
                        padding = len(payload_part) % 4
                        if padding:
                            payload_part += '=' * (4 - padding)
                        decoded = base64.urlsafe_b64decode(payload_part)
                        jwt_data = json.loads(decoded)
                        self.subscriber_id = jwt_data.get("sub")
                    except Exception as e:
                        logger.warning(f"Could not decode JWT: {e}")
                
                logger.info("Successfully logged in to Taara API")
                return {
                    "success": True,
                    "access_token": self.access_token,
                    "subscriber_id": self.subscriber_id,
                    "response_time_ms": response_time
                }
            else:
                logger.error(f"Login failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "response_time_ms": response_time
                }
                
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": 0
            }

    def get_customer_bundle(self) -> Dict[str, Any]:
        """Get customer bundle information"""
        if not self.access_token:
            login_result = self.login()
            if not login_result["success"]:
                return login_result
        
        headers = self.base_headers.copy()
        headers["authorization"] = f"Bearer {self.access_token}"
        headers["referer"] = f"https://share.taara.company/cp/customers/home?hotspotId={self.hotspot_id}"
        
        try:
            start_time = time.time()
            response = requests.get(
                self.bundle_url,
                headers=headers,
                timeout=30
            )
            response_time = (time.time() - start_time) * 1000
            
            if response.status_code == 200:
                data = response.json()
                logger.info("Successfully retrieved customer bundle data")
                return {
                    "success": True,
                    "data": data,
                    "response_time_ms": response_time
                }
            else:
                logger.error(f"Bundle request failed: {response.status_code} - {response.text}")
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}: {response.text}",
                    "response_time_ms": response_time
                }
                
        except Exception as e:
            logger.error(f"Bundle request error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": 0
            }

    def logout(self) -> Dict[str, Any]:
        """Logout from Taara API"""
        if not self.subscriber_id:
            return {"success": True, "message": "Not logged in"}
        
        logout_url = f"{self.logout_url}/{self.subscriber_id}"
        headers = self.base_headers.copy()
        headers["referer"] = f"https://share.taara.company/cp/customers/home?hotspotId={self.hotspot_id}"
        
        try:
            start_time = time.time()
            response = requests.get(logout_url, headers=headers, timeout=30)
            response_time = (time.time() - start_time) * 1000
            
            self.access_token = None
            self.subscriber_id = None
            
            logger.info("Successfully logged out from Taara API")
            return {
                "success": True,
                "response_time_ms": response_time
            }
            
        except Exception as e:
            logger.error(f"Logout error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "response_time_ms": 0
            }

    def parse_bundle_data(self, bundle_response: Dict[str, Any]) -> list:
        """Parse bundle response and extract usage data"""
        parsed_data = []
        
        try:
            data = bundle_response.get("data", {})
            subscriber_id = data.get("subscriberId", "")
            active_plans = data.get("subscriberActiveAndUnusedPlans", [])
            
            for plan in active_plans:
                # Parse remaining balance
                remaining_balance_str = plan.get("remainingBalance", "0 GB")
                remaining_balance_gb = 0
                remaining_balance_bytes = 0
                
                if "GB" in remaining_balance_str:
                    try:
                        remaining_balance_gb = float(remaining_balance_str.replace("GB", "").strip())
                        remaining_balance_bytes = int(remaining_balance_gb * 1024 * 1024 * 1024)
                    except ValueError:
                        pass
                elif "MB" in remaining_balance_str:
                    try:
                        remaining_balance_mb = float(remaining_balance_str.replace("MB", "").strip())
                        remaining_balance_gb = remaining_balance_mb / 1024
                        remaining_balance_bytes = int(remaining_balance_mb * 1024 * 1024)
                    except ValueError:
                        pass
                
                # Parse expires in days
                expires_in_str = plan.get("expiresIn", "0 days")
                expires_in_days = 0
                try:
                    expires_in_days = int(expires_in_str.replace("days", "").strip())
                except ValueError:
                    pass
                
                # Get total data usage from purchase history if available
                total_data_usage_bytes = 0
                purchase_history = data.get("purchasedHistory", [])
                if purchase_history:
                    for history in purchase_history:
                        for history_plan in history.get("purchasedHistoryPlans", []):
                            if history_plan.get("planDisplayName") == plan.get("planName"):
                                usage_data = history_plan.get("dataUsage", {})
                                total_data_usage_bytes = usage_data.get("totalDataUsage", 0)
                                break
                
                parsed_record = {
                    "subscriber_id": subscriber_id,
                    "plan_name": plan.get("planName", ""),
                    "plan_id": plan.get("planId", ""),
                    "remaining_balance_gb": remaining_balance_gb,
                    "remaining_balance_bytes": remaining_balance_bytes,
                    "total_data_usage_bytes": total_data_usage_bytes,
                    "expires_in_days": expires_in_days,
                    "is_active": plan.get("isActive", False),
                    "is_home_plan": plan.get("isHomePlan", False),
                    "raw_response": json.dumps(bundle_response)
                }
                
                parsed_data.append(parsed_record)
                
        except Exception as e:
            logger.error(f"Error parsing bundle data: {str(e)}")
            
        return parsed_data
