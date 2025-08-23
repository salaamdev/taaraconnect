# Technical Architecture Document: Taara Internet Usage Monitoring System

**Document Information:**
- **Product Name:** Taara Internet Usage Monitoring System
- **Document Type:** Technical Architecture
- **Document Version:** v1.0
- **Date Created:** August 23, 2025
- **Last Updated:** August 23, 2025
- **Document Owner:** Sarah (Product Owner)
- **Status:** Ready for Development

---

## 1. Database Schema Design

### 1.1 Core Tables Schema

```sql
-- Primary usage data collection table
CREATE TABLE usage_readings (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    total_used_mb BIGINT NOT NULL,
    total_allocated_mb BIGINT NOT NULL DEFAULT 1048576, -- 1TB in MB
    remaining_mb BIGINT NOT NULL,
    collection_status VARCHAR(20) NOT NULL CHECK (collection_status IN ('SUCCESS', 'FAILED', 'PARTIAL')),
    api_response_time_ms INTEGER,
    raw_api_data JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT usage_readings_timestamp_unique UNIQUE (timestamp),
    CONSTRAINT usage_readings_positive_values CHECK (
        total_used_mb >= 0 AND 
        total_allocated_mb > 0 AND 
        remaining_mb >= 0 AND
        api_response_time_ms >= 0
    )
);

-- Daily aggregated analytics
CREATE TABLE daily_summaries (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL UNIQUE,
    daily_usage_mb BIGINT NOT NULL,
    daily_budget_mb BIGINT NOT NULL,
    budget_variance_mb BIGINT NOT NULL, -- Actual vs budget difference
    usage_efficiency_score DECIMAL(3,2) CHECK (usage_efficiency_score >= 0 AND usage_efficiency_score <= 1),
    peak_usage_hour INTEGER CHECK (peak_usage_hour >= 0 AND peak_usage_hour <= 23),
    reading_count INTEGER NOT NULL DEFAULT 0,
    data_quality_score DECIMAL(3,2) CHECK (data_quality_score >= 0 AND data_quality_score <= 1),
    trend_direction VARCHAR(20) CHECK (trend_direction IN ('INCREASING', 'DECREASING', 'STABLE')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT daily_summaries_positive_values CHECK (
        daily_usage_mb >= 0 AND 
        daily_budget_mb >= 0 AND
        reading_count >= 0
    )
);

-- User preferences and configuration
CREATE TABLE user_preferences (
    id SERIAL PRIMARY KEY,
    isp_username VARCHAR(100) NOT NULL,
    isp_password_encrypted TEXT NOT NULL,
    encryption_key_hash VARCHAR(64) NOT NULL,
    notification_email VARCHAR(255),
    email_enabled BOOLEAN DEFAULT true,
    desktop_notifications_enabled BOOLEAN DEFAULT true,
    alert_threshold_percentage INTEGER DEFAULT 75 CHECK (
        alert_threshold_percentage >= 50 AND alert_threshold_percentage <= 95
    ),
    daily_budget_alerts BOOLEAN DEFAULT true,
    weekly_summary_enabled BOOLEAN DEFAULT true,
    timezone VARCHAR(50) DEFAULT 'UTC',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    credential_last_rotated TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Single household constraint
    CONSTRAINT single_household CHECK (id = 1)
);

-- Alert and notification tracking
CREATE TABLE alert_history (
    id SERIAL PRIMARY KEY,
    alert_type VARCHAR(30) NOT NULL CHECK (
        alert_type IN ('DAILY_BUDGET', 'THRESHOLD_WARNING', 'WEEKLY_SUMMARY', 'OPTIMIZATION_TIP')
    ),
    trigger_usage_mb BIGINT,
    trigger_percentage DECIMAL(5,2),
    delivery_channel VARCHAR(20) CHECK (delivery_channel IN ('EMAIL', 'DESKTOP', 'DASHBOARD')),
    delivery_status VARCHAR(20) CHECK (delivery_status IN ('SENT', 'FAILED', 'PENDING')),
    message_content TEXT,
    user_engagement BOOLEAN DEFAULT false,
    effectiveness_score DECIMAL(3,2),
    sent_at TIMESTAMP WITH TIME ZONE,
    acknowledged_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- System health and performance monitoring
CREATE TABLE system_health (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    api_status VARCHAR(20) CHECK (api_status IN ('HEALTHY', 'DEGRADED', 'DOWN')),
    api_response_time_ms INTEGER,
    database_status VARCHAR(20) CHECK (database_status IN ('HEALTHY', 'SLOW', 'ERROR')),
    memory_usage_mb INTEGER,
    cpu_usage_percentage DECIMAL(5,2),
    disk_usage_percentage DECIMAL(5,2),
    active_sessions INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0
);
```

### 1.2 Indexing Strategy

```sql
-- Performance indexes for time-series queries
CREATE INDEX idx_usage_readings_timestamp ON usage_readings(timestamp DESC);
CREATE INDEX idx_usage_readings_status ON usage_readings(collection_status);
CREATE INDEX idx_usage_readings_date_range ON usage_readings(timestamp) 
    WHERE collection_status = 'SUCCESS';

-- Daily summary indexes
CREATE INDEX idx_daily_summaries_date ON daily_summaries(date DESC);
CREATE INDEX idx_daily_summaries_trend ON daily_summaries(trend_direction);

-- Alert history indexes  
CREATE INDEX idx_alert_history_type_date ON alert_history(alert_type, sent_at DESC);
CREATE INDEX idx_alert_history_status ON alert_history(delivery_status);

-- System health monitoring
CREATE INDEX idx_system_health_timestamp ON system_health(timestamp DESC);
```

### 1.3 Data Retention Policy

```sql
-- Automated data archival function
CREATE OR REPLACE FUNCTION archive_old_data()
RETURNS void AS $$
BEGIN
    -- Archive usage_readings older than 12 months
    DELETE FROM usage_readings 
    WHERE timestamp < NOW() - INTERVAL '12 months';
    
    -- Archive daily_summaries older than 24 months
    DELETE FROM daily_summaries 
    WHERE date < CURRENT_DATE - INTERVAL '24 months';
    
    -- Archive alert_history older than 6 months
    DELETE FROM alert_history 
    WHERE created_at < NOW() - INTERVAL '6 months';
    
    -- Archive system_health older than 30 days
    DELETE FROM system_health 
    WHERE timestamp < NOW() - INTERVAL '30 days';
    
    -- Vacuum tables for space reclamation
    VACUUM ANALYZE usage_readings, daily_summaries, alert_history, system_health;
END;
$$ LANGUAGE plpgsql;

-- Schedule monthly archival
SELECT cron.schedule('monthly-archival', '0 2 1 * *', 'SELECT archive_old_data();');
```

---

## 2. ISP API Integration Architecture

### 2.1 API Client Pattern

```python
from dataclasses import dataclass
from typing import Optional, Dict, Any
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import time
import logging

@dataclass
class ApiResponse:
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    response_time_ms: int
    status_code: Optional[int]

class TaaraApiClient:
    def __init__(self, base_url: str = "http://192.168.88.1"):
        self.base_url = base_url
        self.session = None
        self.last_auth_time = None
        self.auth_valid_duration = 3600  # 1 hour
        self.max_retries = 3
        self.backoff_factor = 0.3
        self.timeout = (10, 30)  # Connect, read timeouts
        
        # Setup session with retry strategy
        self._setup_session()
        
    def _setup_session(self):
        """Configure HTTP session with retry and timeout strategy."""
        self.session = requests.Session()
        
        # Retry strategy
        retry_strategy = Retry(
            total=self.max_retries,
            backoff_factor=self.backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
    def authenticate(self, username: str, password: str) -> ApiResponse:
        """Authenticate with Taara ISP API."""
        start_time = time.time()
        
        try:
            response = self.session.post(
                f"{self.base_url}/login",
                data={"username": username, "password": password},
                timeout=self.timeout
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                self.last_auth_time = time.time()
                logging.info(f"ISP authentication successful ({response_time}ms)")
                return ApiResponse(
                    success=True,
                    data={"session_established": True},
                    error=None,
                    response_time_ms=response_time,
                    status_code=response.status_code
                )
            else:
                error_msg = f"Authentication failed: HTTP {response.status_code}"
                logging.error(error_msg)
                return ApiResponse(
                    success=False,
                    data=None,
                    error=error_msg,
                    response_time_ms=response_time,
                    status_code=response.status_code
                )
                
        except requests.exceptions.RequestException as e:
            response_time = int((time.time() - start_time) * 1000)
            error_msg = f"Authentication request failed: {str(e)}"
            logging.error(error_msg)
            return ApiResponse(
                success=False,
                data=None,
                error=error_msg,
                response_time_ms=response_time,
                status_code=None
            )
    
    def get_usage_data(self) -> ApiResponse:
        """Retrieve current usage data from ISP API."""
        if not self._is_authenticated():
            return ApiResponse(
                success=False,
                data=None,
                error="Not authenticated",
                response_time_ms=0,
                status_code=None
            )
            
        start_time = time.time()
        
        try:
            response = self.session.get(
                f"{self.base_url}/usage",
                timeout=self.timeout
            )
            
            response_time = int((time.time() - start_time) * 1000)
            
            if response.status_code == 200:
                usage_data = response.json()
                logging.info(f"Usage data retrieved successfully ({response_time}ms)")
                return ApiResponse(
                    success=True,
                    data=usage_data,
                    error=None,
                    response_time_ms=response_time,
                    status_code=response.status_code
                )
            else:
                error_msg = f"Usage data request failed: HTTP {response.status_code}"
                logging.error(error_msg)
                return ApiResponse(
                    success=False,
                    data=None,
                    error=error_msg,
                    response_time_ms=response_time,
                    status_code=response.status_code
                )
                
        except requests.exceptions.RequestException as e:
            response_time = int((time.time() - start_time) * 1000)
            error_msg = f"Usage data request failed: {str(e)}"
            logging.error(error_msg)
            return ApiResponse(
                success=False,
                data=None,
                error=error_msg,
                response_time_ms=response_time,
                status_code=None
            )
    
    def _is_authenticated(self) -> bool:
        """Check if current session is still valid."""
        if self.last_auth_time is None:
            return False
        return (time.time() - self.last_auth_time) < self.auth_valid_duration
```

### 2.2 Circuit Breaker Pattern

```python
from enum import Enum
from datetime import datetime, timedelta
import threading

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    def __init__(self, failure_threshold=5, timeout=60, expected_exception=Exception):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.expected_exception = expected_exception
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
        self.lock = threading.Lock()
    
    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker protection."""
        with self.lock:
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitState.HALF_OPEN
                else:
                    raise Exception("Circuit breaker is OPEN")
            
            try:
                result = func(*args, **kwargs)
                self._on_success()
                return result
            except self.expected_exception as e:
                self._on_failure()
                raise e
    
    def _should_attempt_reset(self):
        """Check if enough time has passed to attempt reset."""
        return (datetime.now() - self.last_failure_time) >= timedelta(seconds=self.timeout)
    
    def _on_success(self):
        """Handle successful operation."""
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def _on_failure(self):
        """Handle failed operation."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
```

### 2.3 Graceful Degradation Strategy

```python
from typing import Optional
from datetime import datetime, timedelta

class DataCollectionService:
    def __init__(self, api_client: TaaraApiClient, db_service, circuit_breaker: CircuitBreaker):
        self.api_client = api_client
        self.db_service = db_service
        self.circuit_breaker = circuit_breaker
        self.offline_mode = False
        self.last_successful_collection = None
        
    def collect_usage_data(self) -> bool:
        """Main data collection method with fallback strategies."""
        try:
            # Attempt primary data collection
            result = self.circuit_breaker.call(self._collect_from_api)
            
            if result.success:
                self._store_usage_data(result)
                self._exit_offline_mode()
                return True
            else:
                return self._handle_collection_failure(result)
                
        except Exception as e:
            logging.error(f"Data collection failed: {str(e)}")
            return self._enter_offline_mode()
    
    def _collect_from_api(self) -> ApiResponse:
        """Collect data from ISP API with authentication handling."""
        # Check if re-authentication is needed
        if not self.api_client._is_authenticated():
            credentials = self._get_encrypted_credentials()
            auth_result = self.api_client.authenticate(
                credentials.username, 
                credentials.password
            )
            if not auth_result.success:
                raise Exception(f"Authentication failed: {auth_result.error}")
        
        # Retrieve usage data
        return self.api_client.get_usage_data()
    
    def _handle_collection_failure(self, result: ApiResponse) -> bool:
        """Handle partial failures with degraded service."""
        if result.status_code == 429:  # Rate limited
            logging.warning("API rate limited, extending polling interval")
            self._extend_polling_interval()
            return False
        elif result.status_code in [500, 502, 503, 504]:  # Server errors
            logging.warning("API server error, will retry next cycle")
            return False
        else:
            return self._enter_offline_mode()
    
    def _enter_offline_mode(self) -> bool:
        """Enter offline mode with cached data."""
        self.offline_mode = True
        logging.warning("Entering offline mode - using cached data")
        
        # Store system status
        self.db_service.record_system_status(
            api_status='DOWN',
            error_message="ISP API unavailable",
            offline_mode=True
        )
        
        # Generate estimated usage based on trends
        self._generate_estimated_usage()
        return False
    
    def _exit_offline_mode(self):
        """Exit offline mode when API is available."""
        if self.offline_mode:
            self.offline_mode = False
            logging.info("Exiting offline mode - API connection restored")
            
            self.db_service.record_system_status(
                api_status='HEALTHY',
                offline_mode=False
            )
```

---

## 3. Security Architecture

### 3.1 Credential Management

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import os
import base64
import hashlib
from datetime import datetime, timedelta

class CredentialManager:
    def __init__(self):
        self.master_key = self._derive_master_key()
        self.cipher_suite = Fernet(self.master_key)
        self.rotation_interval = timedelta(days=90)  # Rotate every 90 days
        
    def _derive_master_key(self) -> bytes:
        """Derive encryption key from environment variables and salt."""
        password = os.environ.get('MASTER_PASSWORD', '').encode()
        salt = os.environ.get('ENCRYPTION_SALT', 'default_salt').encode()
        
        if not password:
            raise ValueError("MASTER_PASSWORD environment variable required")
            
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt_credentials(self, username: str, password: str) -> Dict[str, str]:
        """Encrypt ISP credentials for secure storage."""
        combined = f"{username}:{password}"
        encrypted_data = self.cipher_suite.encrypt(combined.encode())
        
        # Create validation hash
        validation_hash = hashlib.sha256(
            f"{username}:{password}".encode()
        ).hexdigest()
        
        return {
            'encrypted_credentials': base64.urlsafe_b64encode(encrypted_data).decode(),
            'validation_hash': validation_hash,
            'encrypted_at': datetime.utcnow().isoformat(),
            'rotation_due': (datetime.utcnow() + self.rotation_interval).isoformat()
        }
    
    def decrypt_credentials(self, encrypted_data: str, validation_hash: str) -> Dict[str, str]:
        """Decrypt ISP credentials for API usage."""
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_bytes)
            combined = decrypted_data.decode()
            
            username, password = combined.split(':', 1)
            
            # Validate integrity
            computed_hash = hashlib.sha256(combined.encode()).hexdigest()
            if computed_hash != validation_hash:
                raise ValueError("Credential integrity check failed")
            
            return {
                'username': username,
                'password': password
            }
            
        except Exception as e:
            logging.error(f"Credential decryption failed: {str(e)}")
            raise ValueError("Failed to decrypt credentials")
    
    def needs_rotation(self, encrypted_at: str, rotation_due: str) -> bool:
        """Check if credentials need rotation."""
        rotation_time = datetime.fromisoformat(rotation_due)
        return datetime.utcnow() >= rotation_time
    
    def rotate_credentials(self, current_encrypted: str, validation_hash: str) -> Dict[str, str]:
        """Rotate encryption for existing credentials."""
        # Decrypt with current key
        credentials = self.decrypt_credentials(current_encrypted, validation_hash)
        
        # Re-encrypt with fresh key derivation
        self.master_key = self._derive_master_key()
        self.cipher_suite = Fernet(self.master_key)
        
        # Encrypt with new key
        return self.encrypt_credentials(
            credentials['username'], 
            credentials['password']
        )

class SessionManager:
    def __init__(self):
        self.session_timeout = timedelta(hours=24)
        self.max_sessions = 5
        
    def create_session(self, user_id: str) -> str:
        """Create secure session token."""
        session_token = base64.urlsafe_b64encode(os.urandom(32)).decode()
        session_data = {
            'user_id': user_id,
            'created_at': datetime.utcnow().isoformat(),
            'expires_at': (datetime.utcnow() + self.session_timeout).isoformat(),
            'last_activity': datetime.utcnow().isoformat()
        }
        
        # Store in secure session storage (Redis or encrypted database)
        self._store_session(session_token, session_data)
        return session_token
    
    def validate_session(self, session_token: str) -> bool:
        """Validate session token and update activity."""
        session_data = self._get_session(session_token)
        
        if not session_data:
            return False
            
        expires_at = datetime.fromisoformat(session_data['expires_at'])
        if datetime.utcnow() >= expires_at:
            self._delete_session(session_token)
            return False
        
        # Update last activity
        session_data['last_activity'] = datetime.utcnow().isoformat()
        self._store_session(session_token, session_data)
        return True
```

### 3.2 Security Monitoring

```python
import logging
from datetime import datetime, timedelta
from typing import List, Dict

class SecurityMonitor:
    def __init__(self):
        self.failed_auth_threshold = 5
        self.time_window = timedelta(minutes=15)
        self.failed_attempts = {}
        
    def log_auth_attempt(self, ip_address: str, success: bool, username: str = None):
        """Log authentication attempt for monitoring."""
        attempt = {
            'timestamp': datetime.utcnow(),
            'ip_address': ip_address,
            'success': success,
            'username': username
        }
        
        if not success:
            self._track_failed_attempt(ip_address)
            
        # Log to security audit trail
        logging.getLogger('security').info(
            f"Auth attempt: IP={ip_address}, Success={success}, User={username}"
        )
    
    def _track_failed_attempt(self, ip_address: str):
        """Track failed authentication attempts."""
        now = datetime.utcnow()
        
        if ip_address not in self.failed_attempts:
            self.failed_attempts[ip_address] = []
            
        # Add current attempt
        self.failed_attempts[ip_address].append(now)
        
        # Remove old attempts outside time window
        cutoff = now - self.time_window
        self.failed_attempts[ip_address] = [
            attempt for attempt in self.failed_attempts[ip_address]
            if attempt > cutoff
        ]
        
        # Check if threshold exceeded
        if len(self.failed_attempts[ip_address]) >= self.failed_auth_threshold:
            self._trigger_security_alert(ip_address)
    
    def _trigger_security_alert(self, ip_address: str):
        """Trigger security alert for suspicious activity."""
        alert_data = {
            'type': 'EXCESSIVE_FAILED_AUTH',
            'ip_address': ip_address,
            'attempt_count': len(self.failed_attempts[ip_address]),
            'time_window': str(self.time_window),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logging.getLogger('security').warning(
            f"Security Alert: {alert_data}"
        )
        
        # Could trigger additional actions:
        # - Temporary IP blocking
        # - Admin notification
        # - Enhanced monitoring
```

---

## 4. Performance Optimization

### 4.1 Adaptive Polling Strategy

```python
import time
from datetime import datetime, timedelta
from enum import Enum

class PollingMode(Enum):
    NORMAL = "normal"
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"
    BACKOFF = "backoff"

class AdaptivePoller:
    def __init__(self):
        self.mode = PollingMode.NORMAL
        self.base_interval = 600  # 10 minutes
        self.current_interval = self.base_interval
        self.success_count = 0
        self.failure_count = 0
        self.last_adjustment = datetime.utcnow()
        
        # Mode configurations
        self.mode_config = {
            PollingMode.NORMAL: {'interval': 600, 'factor': 1.0},
            PollingMode.CONSERVATIVE: {'interval': 900, 'factor': 1.5},
            PollingMode.AGGRESSIVE: {'interval': 300, 'factor': 0.5},
            PollingMode.BACKOFF: {'interval': 1800, 'factor': 3.0}
        }
    
    def get_next_poll_interval(self) -> int:
        """Calculate next polling interval based on current performance."""
        self._evaluate_mode_adjustment()
        return self.current_interval
    
    def record_poll_result(self, success: bool, response_time_ms: int):
        """Record polling result for adaptive adjustment."""
        if success:
            self.success_count += 1
            self.failure_count = max(0, self.failure_count - 1)
            
            # Improve mode if consistently successful
            if self.success_count >= 10 and self.mode != PollingMode.AGGRESSIVE:
                self._adjust_mode_up()
                
        else:
            self.failure_count += 1
            self.success_count = max(0, self.success_count - 1)
            
            # Degrade mode if consistently failing
            if self.failure_count >= 3:
                self._adjust_mode_down()
    
    def _evaluate_mode_adjustment(self):
        """Evaluate if polling mode should be adjusted."""
        now = datetime.utcnow()
        time_since_adjustment = (now - self.last_adjustment).total_seconds()
        
        # Only adjust mode every 30 minutes minimum
        if time_since_adjustment < 1800:
            return
            
        success_rate = self.success_count / max(1, self.success_count + self.failure_count)
        
        if success_rate >= 0.95 and self.mode != PollingMode.AGGRESSIVE:
            self._adjust_mode_up()
        elif success_rate <= 0.8 and self.mode != PollingMode.BACKOFF:
            self._adjust_mode_down()
    
    def _adjust_mode_up(self):
        """Improve polling mode for better performance."""
        mode_order = [PollingMode.BACKOFF, PollingMode.CONSERVATIVE, 
                     PollingMode.NORMAL, PollingMode.AGGRESSIVE]
        
        current_index = mode_order.index(self.mode)
        if current_index < len(mode_order) - 1:
            self.mode = mode_order[current_index + 1]
            self._update_interval()
            logging.info(f"Polling mode improved to {self.mode.value}")
    
    def _adjust_mode_down(self):
        """Degrade polling mode for stability."""
        mode_order = [PollingMode.AGGRESSIVE, PollingMode.NORMAL, 
                     PollingMode.CONSERVATIVE, PollingMode.BACKOFF]
        
        current_index = mode_order.index(self.mode)
        if current_index < len(mode_order) - 1:
            self.mode = mode_order[current_index + 1]
            self._update_interval()
            logging.warning(f"Polling mode degraded to {self.mode.value}")
    
    def _update_interval(self):
        """Update current interval based on mode."""
        config = self.mode_config[self.mode]
        self.current_interval = config['interval']
        self.last_adjustment = datetime.utcnow()
        
        # Reset counters
        self.success_count = 0
        self.failure_count = 0
```

### 4.2 Database Query Optimization

```python
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta

class OptimizedDataService:
    def __init__(self, database_url: str):
        self.engine = create_engine(
            database_url,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300
        )
        self.SessionLocal = sessionmaker(bind=self.engine)
    
    def get_current_usage_summary(self) -> Dict[str, Any]:
        """Optimized query for dashboard current status."""
        query = text("""
            WITH latest_reading AS (
                SELECT 
                    total_used_mb,
                    total_allocated_mb,
                    remaining_mb,
                    timestamp,
                    collection_status
                FROM usage_readings 
                WHERE collection_status = 'SUCCESS'
                ORDER BY timestamp DESC 
                LIMIT 1
            ),
            today_summary AS (
                SELECT 
                    daily_usage_mb,
                    daily_budget_mb,
                    budget_variance_mb,
                    usage_efficiency_score
                FROM daily_summaries 
                WHERE date = CURRENT_DATE
            ),
            trend_data AS (
                SELECT 
                    AVG(daily_usage_mb) as avg_weekly_usage,
                    COUNT(*) as days_tracked
                FROM daily_summaries 
                WHERE date >= CURRENT_DATE - INTERVAL '7 days'
            )
            SELECT 
                lr.total_used_mb,
                lr.total_allocated_mb,
                lr.remaining_mb,
                lr.timestamp as last_updated,
                COALESCE(ts.daily_usage_mb, 0) as today_usage_mb,
                COALESCE(ts.daily_budget_mb, 0) as daily_budget_mb,
                COALESCE(ts.usage_efficiency_score, 0) as efficiency_score,
                COALESCE(td.avg_weekly_usage, 0) as avg_weekly_usage,
                EXTRACT(DAY FROM (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' - CURRENT_DATE)) as days_remaining
            FROM latest_reading lr
            LEFT JOIN today_summary ts ON true
            LEFT JOIN trend_data td ON true
        """)
        
        with self.SessionLocal() as session:
            result = session.execute(query).fetchone()
            if result:
                return {
                    'total_used_mb': result.total_used_mb,
                    'total_allocated_mb': result.total_allocated_mb,
                    'remaining_mb': result.remaining_mb,
                    'last_updated': result.last_updated,
                    'today_usage_mb': result.today_usage_mb,
                    'daily_budget_mb': result.daily_budget_mb,
                    'efficiency_score': float(result.efficiency_score),
                    'avg_weekly_usage': float(result.avg_weekly_usage),
                    'days_remaining': int(result.days_remaining)
                }
            return {}
    
    def get_trend_analysis(self, days: int = 30) -> List[Dict[str, Any]]:
        """Optimized query for trend analysis."""
        query = text("""
            SELECT 
                date,
                daily_usage_mb,
                daily_budget_mb,
                budget_variance_mb,
                usage_efficiency_score,
                trend_direction
            FROM daily_summaries 
            WHERE date >= CURRENT_DATE - INTERVAL :days DAY
            ORDER BY date DESC
        """)
        
        with self.SessionLocal() as session:
            results = session.execute(query, {'days': days}).fetchall()
            return [
                {
                    'date': row.date,
                    'daily_usage_mb': row.daily_usage_mb,
                    'daily_budget_mb': row.daily_budget_mb,
                    'variance_mb': row.budget_variance_mb,
                    'efficiency_score': float(row.usage_efficiency_score),
                    'trend': row.trend_direction
                }
                for row in results
            ]
```

### 4.3 Caching Strategy

```python
import redis
import json
from typing import Optional, Any
from datetime import timedelta

class CacheManager:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)
        self.default_ttl = 300  # 5 minutes
        
    def get_cached_data(self, key: str) -> Optional[Any]:
        """Retrieve data from cache."""
        try:
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logging.error(f"Cache retrieval failed for {key}: {str(e)}")
            return None
    
    def set_cached_data(self, key: str, data: Any, ttl: Optional[int] = None) -> bool:
        """Store data in cache with TTL."""
        try:
            ttl = ttl or self.default_ttl
            serialized = json.dumps(data, default=str)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logging.error(f"Cache storage failed for {key}: {str(e)}")
            return False
    
    def invalidate_cache(self, pattern: str):
        """Invalidate cache entries matching pattern."""
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
        except Exception as e:
            logging.error(f"Cache invalidation failed for {pattern}: {str(e)}")
    
    def cache_dashboard_data(self, user_id: str, data: Dict[str, Any]):
        """Cache dashboard data with appropriate TTL."""
        self.set_cached_data(f"dashboard:{user_id}", data, ttl=120)  # 2 minutes
    
    def cache_trend_data(self, data: List[Dict[str, Any]]):
        """Cache trend analysis with longer TTL."""
        self.set_cached_data("trends:daily", data, ttl=1800)  # 30 minutes
```

---

## 5. Resource Management

### 5.1 Memory Optimization

```python
import psutil
import gc
from typing import Dict, Any

class ResourceMonitor:
    def __init__(self):
        self.memory_threshold = 400  # MB
        self.cpu_threshold = 15      # %
        
    def check_system_resources(self) -> Dict[str, Any]:
        """Monitor system resource usage."""
        memory = psutil.virtual_memory()
        cpu_percent = psutil.cpu_percent(interval=1)
        disk = psutil.disk_usage('/')
        
        resources = {
            'memory_used_mb': memory.used // 1024 // 1024,
            'memory_available_mb': memory.available // 1024 // 1024,
            'memory_percent': memory.percent,
            'cpu_percent': cpu_percent,
            'disk_used_gb': disk.used // 1024 // 1024 // 1024,
            'disk_free_gb': disk.free // 1024 // 1024 // 1024,
            'disk_percent': (disk.used / disk.total) * 100
        }
        
        # Check if intervention needed
        if resources['memory_used_mb'] > self.memory_threshold:
            self._optimize_memory_usage()
            
        if resources['cpu_percent'] > self.cpu_threshold:
            self._optimize_cpu_usage()
            
        return resources
    
    def _optimize_memory_usage(self):
        """Optimize memory usage when threshold exceeded."""
        logging.warning("Memory threshold exceeded, optimizing...")
        
        # Force garbage collection
        gc.collect()
        
        # Clear application caches
        from app.services.cache_manager import cache_manager
        cache_manager.invalidate_cache("temp:*")
        
        # Log memory status
        memory = psutil.virtual_memory()
        logging.info(f"Memory after optimization: {memory.used // 1024 // 1024}MB")
    
    def _optimize_cpu_usage(self):
        """Optimize CPU usage when threshold exceeded."""
        logging.warning("CPU threshold exceeded, optimizing...")
        
        # Reduce polling frequency temporarily
        from app.services.data_collection import data_collector
        data_collector.enter_conservative_mode()
```

---

This technical architecture document addresses all the critical gaps identified in the master checklist:

1. **✅ Database Schema Design** - Complete schema with indexing and retention policies
2. **✅ ISP API Integration** - Comprehensive patterns with circuit breaker and fallback
3. **✅ Security Architecture** - Credential rotation, session management, and monitoring
4. **✅ Performance Optimization** - Adaptive polling, query optimization, and caching
5. **✅ Resource Management** - Memory and CPU monitoring with optimization strategies

The project is now architecturally ready for development with proper technical foundations!
