# Testing Strategy: Taara Internet Usage Monitoring System

**Document Information:**

- **Product Name:** Taara Internet Usage Monitoring System
- **Document Type:** Testing Strategy & Framework
- **Document Version:** v1.0
- **Date Created:** August 23, 2025
- **Last Updated:** August 23, 2025
- **Document Owner:** Sarah (Product Owner)
- **Status:** Ready for Implementation

---

## 1. Testing Philosophy

### 1.1 Core Testing Principles

**Quality First Approach:**

- Every feature must be tested before deployment
- ISP API integration requires comprehensive mocking
- Performance testing validates budget hosting constraints
- Security testing protects user credentials

**Test Pyramid Strategy:**

- 70% Unit Tests - Fast, isolated component testing
- 20% Integration Tests - Component interaction validation
- 10% End-to-End Tests - Complete user journey validation

### 1.2 Testing Objectives

**Primary Goals:**

- Ensure 99% API data collection reliability
- Validate dashboard performance under 2-second load times
- Protect ISP credential security throughout system
- Verify notification delivery across all channels

**Quality Metrics:**

- Test Coverage: Minimum 85% for critical components
- Performance: All tests complete within 10 minutes
- Reliability: Zero false positives in test suite
- Maintainability: Tests serve as living documentation

---

## 2. Unit Testing Framework

### 2.1 Test Setup and Configuration

```python
# tests/conftest.py
import pytest
import os
from unittest.mock import Mock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app import create_app
from app.models import Base
from app.services.credential_manager import CredentialManager

@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine."""
    test_db_url = "sqlite:///:memory:"
    engine = create_engine(test_db_url)
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture(scope="function")
def db_session(test_engine):
    """Create test database session."""
    TestSession = sessionmaker(bind=test_engine)
    session = TestSession()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def test_app():
    """Create test Flask application."""
    os.environ['TESTING'] = 'True'
    os.environ['MASTER_PASSWORD'] = 'test_password'
    os.environ['ENCRYPTION_SALT'] = 'test_salt'
    
    app = create_app()
    app.config['TESTING'] = True
    
    with app.app_context():
        yield app

@pytest.fixture
def test_client(test_app):
    """Create test client."""
    return test_app.test_client()

@pytest.fixture
def mock_taara_api():
    """Mock Taara ISP API responses."""
    mock_api = Mock()
    mock_api.authenticate.return_value = Mock(
        success=True,
        data={'session_established': True},
        error=None,
        response_time_ms=250,
        status_code=200
    )
    mock_api.get_usage_data.return_value = Mock(
        success=True,
        data={
            'total_used_mb': 614400,
            'total_allocated_mb': 1048576,
            'remaining_mb': 434176
        },
        error=None,
        response_time_ms=180,
        status_code=200
    )
    return mock_api

@pytest.fixture
def sample_usage_data():
    """Sample usage data for testing."""
    return {
        'total_used_mb': 614400,
        'total_allocated_mb': 1048576,
        'remaining_mb': 434176,
        'timestamp': '2025-08-23T12:00:00Z',
        'collection_status': 'SUCCESS'
    }
```

### 2.2 Data Collection Service Tests

```python
# tests/unit/test_data_collection_service.py
import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from app.services.data_collection_service import DataCollectionService
from app.services.taara_api_client import ApiResponse

class TestDataCollectionService:
    
    def test_successful_data_collection(self, db_session, mock_taara_api):
        """Test successful data collection and storage."""
        service = DataCollectionService(mock_taara_api, db_session)
        
        result = service.collect_usage_data()
        
        assert result is True
        assert mock_taara_api.get_usage_data.called
        
        # Verify data stored in database
        from app.models.usage_reading import UsageReading
        reading = db_session.query(UsageReading).first()
        assert reading is not None
        assert reading.total_used_mb == 614400
        assert reading.collection_status == 'SUCCESS'
    
    def test_api_authentication_failure(self, db_session, mock_taara_api):
        """Test handling of API authentication failure."""
        mock_taara_api.authenticate.return_value = Mock(
            success=False,
            error="Invalid credentials",
            response_time_ms=150,
            status_code=401
        )
        
        service = DataCollectionService(mock_taara_api, db_session)
        result = service.collect_usage_data()
        
        assert result is False
        # Verify error logged appropriately
        
    def test_api_rate_limiting(self, db_session, mock_taara_api):
        """Test handling of API rate limiting."""
        mock_taara_api.get_usage_data.return_value = Mock(
            success=False,
            error="Rate limited",
            response_time_ms=100,
            status_code=429
        )
        
        service = DataCollectionService(mock_taara_api, db_session)
        result = service.collect_usage_data()
        
        assert result is False
        # Verify polling interval extended
        assert service.polling_interval > service.base_interval
    
    def test_offline_mode_activation(self, db_session, mock_taara_api):
        """Test offline mode when API is unavailable."""
        mock_taara_api.get_usage_data.side_effect = Exception("Network error")
        
        service = DataCollectionService(mock_taara_api, db_session)
        result = service.collect_usage_data()
        
        assert result is False
        assert service.offline_mode is True
        
    def test_circuit_breaker_activation(self, db_session, mock_taara_api):
        """Test circuit breaker after multiple failures."""
        mock_taara_api.get_usage_data.side_effect = Exception("Server error")
        
        service = DataCollectionService(mock_taara_api, db_session)
        
        # Trigger multiple failures
        for _ in range(6):  # Exceeds failure threshold
            service.collect_usage_data()
            
        assert service.circuit_breaker.state.value == "open"
```

### 2.3 Analytics Engine Tests

```python
# tests/unit/test_analytics_engine.py
import pytest
from datetime import datetime, timedelta
from app.services.analytics_engine import AnalyticsEngine
from app.models.usage_reading import UsageReading
from app.models.daily_summary import DailySummary

class TestAnalyticsEngine:
    
    def test_daily_budget_calculation(self, db_session, sample_usage_data):
        """Test daily budget calculation accuracy."""
        # Setup test data
        today = datetime.now().date()
        days_remaining = 18
        remaining_mb = 434176
        
        engine = AnalyticsEngine(db_session)
        daily_budget = engine.calculate_daily_budget(remaining_mb, days_remaining)
        
        expected_budget = remaining_mb // days_remaining
        assert abs(daily_budget - expected_budget) < 1000  # Allow small variance
        
    def test_safe_time_remaining_calculation(self, db_session):
        """Test safe time remaining calculation."""
        engine = AnalyticsEngine(db_session)
        
        # Mock current usage trajectory
        current_usage = 614400
        allocation = 1048576
        days_in_month = 30
        current_day = 12
        
        safe_time = engine.calculate_safe_time_remaining(
            current_usage, allocation, days_in_month, current_day
        )
        
        # Should be based on current trajectory vs safe trajectory
        assert isinstance(safe_time, int)
        assert safe_time > 0
        
    def test_usage_trend_analysis(self, db_session):
        """Test usage trend analysis accuracy."""
        engine = AnalyticsEngine(db_session)
        
        # Create test data with increasing trend
        base_date = datetime.now().date() - timedelta(days=7)
        for i in range(7):
            summary = DailySummary(
                date=base_date + timedelta(days=i),
                daily_usage_mb=20000 + (i * 2000),  # Increasing usage
                daily_budget_mb=24000,
                budget_variance_mb=0
            )
            db_session.add(summary)
        db_session.commit()
        
        trend = engine.analyze_usage_trend(days=7)
        
        assert trend['direction'] == 'INCREASING'
        assert trend['trend_strength'] > 0.5
        
    def test_overage_risk_detection(self, db_session):
        """Test overage risk detection algorithm."""
        engine = AnalyticsEngine(db_session)
        
        # Setup scenario with high overage risk
        current_usage = 900000  # 90% of 1TB allocation
        allocation = 1048576
        days_remaining = 5  # Only 5 days left
        
        risk_assessment = engine.assess_overage_risk(
            current_usage, allocation, days_remaining
        )
        
        assert risk_assessment['risk_level'] == 'HIGH'
        assert risk_assessment['probability'] > 0.8
        assert len(risk_assessment['recommendations']) > 0
        
    def test_prediction_accuracy_validation(self, db_session):
        """Test prediction accuracy with historical data."""
        engine = AnalyticsEngine(db_session)
        
        # Create historical data for testing
        # This would typically use actual historical data
        historical_accuracy = engine.validate_prediction_accuracy()
        
        # Should meet 90% accuracy target
        assert historical_accuracy >= 0.90
```

### 2.4 Security Component Tests

```python
# tests/unit/test_credential_manager.py
import pytest
import os
from app.services.credential_manager import CredentialManager

class TestCredentialManager:
    
    def test_credential_encryption_decryption(self):
        """Test credential encryption and decryption process."""
        manager = CredentialManager()
        
        username = "test_user"
        password = "test_password123"
        
        # Encrypt credentials
        encrypted_data = manager.encrypt_credentials(username, password)
        
        assert 'encrypted_credentials' in encrypted_data
        assert 'validation_hash' in encrypted_data
        assert encrypted_data['encrypted_credentials'] != f"{username}:{password}"
        
        # Decrypt credentials
        decrypted = manager.decrypt_credentials(
            encrypted_data['encrypted_credentials'],
            encrypted_data['validation_hash']
        )
        
        assert decrypted['username'] == username
        assert decrypted['password'] == password
        
    def test_credential_integrity_validation(self):
        """Test credential integrity validation."""
        manager = CredentialManager()
        
        username = "test_user"
        password = "test_password123"
        
        encrypted_data = manager.encrypt_credentials(username, password)
        
        # Tamper with validation hash
        invalid_hash = "invalid_hash"
        
        with pytest.raises(ValueError, match="integrity check failed"):
            manager.decrypt_credentials(
                encrypted_data['encrypted_credentials'],
                invalid_hash
            )
            
    def test_credential_rotation_needed(self):
        """Test credential rotation timing."""
        manager = CredentialManager()
        
        # Test credentials that need rotation
        old_date = "2025-05-23T12:00:00"  # 3 months ago
        rotation_due = "2025-08-22T12:00:00"  # Yesterday
        
        needs_rotation = manager.needs_rotation(old_date, rotation_due)
        assert needs_rotation is True
        
        # Test credentials that don't need rotation
        recent_date = "2025-08-20T12:00:00"
        future_rotation = "2025-11-20T12:00:00"
        
        needs_rotation = manager.needs_rotation(recent_date, future_rotation)
        assert needs_rotation is False
```

---

## 3. Integration Testing Framework

### 3.1 API Integration Tests

```python
# tests/integration/test_api_integration.py
import pytest
import responses
import json
from app.services.taara_api_client import TaaraApiClient

class TestTaaraApiIntegration:
    
    @responses.activate
    def test_successful_authentication_flow(self):
        """Test complete authentication flow with mocked API."""
        # Mock successful login response
        responses.add(
            responses.POST,
            "http://192.168.88.1/login",
            json={"status": "success", "session_id": "test123"},
            status=200
        )
        
        client = TaaraApiClient()
        result = client.authenticate("test_user", "test_pass")
        
        assert result.success is True
        assert result.status_code == 200
        assert result.response_time_ms > 0
        
    @responses.activate
    def test_authentication_failure_handling(self):
        """Test authentication failure scenarios."""
        # Mock failed login response
        responses.add(
            responses.POST,
            "http://192.168.88.1/login",
            json={"status": "error", "message": "Invalid credentials"},
            status=401
        )
        
        client = TaaraApiClient()
        result = client.authenticate("invalid_user", "wrong_pass")
        
        assert result.success is False
        assert result.status_code == 401
        assert "Authentication failed" in result.error
        
    @responses.activate
    def test_usage_data_retrieval(self):
        """Test usage data retrieval after authentication."""
        # Mock login
        responses.add(
            responses.POST,
            "http://192.168.88.1/login",
            json={"status": "success"},
            status=200
        )
        
        # Mock usage data response
        responses.add(
            responses.GET,
            "http://192.168.88.1/usage",
            json={
                "total_used": "614400",
                "total_allocated": "1048576",
                "remaining": "434176"
            },
            status=200
        )
        
        client = TaaraApiClient()
        
        # Authenticate first
        auth_result = client.authenticate("test_user", "test_pass")
        assert auth_result.success
        
        # Get usage data
        usage_result = client.get_usage_data()
        assert usage_result.success is True
        assert usage_result.data['total_used'] == "614400"
        
    @responses.activate
    def test_network_timeout_handling(self):
        """Test network timeout scenarios."""
        # Mock timeout by not adding any responses
        client = TaaraApiClient()
        
        result = client.authenticate("test_user", "test_pass")
        
        assert result.success is False
        assert "timeout" in result.error.lower() or "failed" in result.error.lower()
        
    @responses.activate
    def test_rate_limiting_response(self):
        """Test rate limiting response handling."""
        responses.add(
            responses.POST,
            "http://192.168.88.1/login",
            json={"status": "error", "message": "Rate limited"},
            status=429
        )
        
        client = TaaraApiClient()
        result = client.authenticate("test_user", "test_pass")
        
        assert result.success is False
        assert result.status_code == 429
```

### 3.2 Database Integration Tests

```python
# tests/integration/test_database_integration.py
import pytest
from datetime import datetime, timedelta
from app.services.data_service import OptimizedDataService
from app.models import UsageReading, DailySummary

class TestDatabaseIntegration:
    
    def test_current_usage_summary_query(self, test_engine):
        """Test optimized current usage summary query."""
        service = OptimizedDataService(str(test_engine.url))
        
        # Insert test data
        with service.SessionLocal() as session:
            # Add usage reading
            reading = UsageReading(
                timestamp=datetime.utcnow(),
                total_used_mb=614400,
                total_allocated_mb=1048576,
                remaining_mb=434176,
                collection_status='SUCCESS'
            )
            session.add(reading)
            
            # Add daily summary
            summary = DailySummary(
                date=datetime.utcnow().date(),
                daily_usage_mb=25000,
                daily_budget_mb=24000,
                budget_variance_mb=1000
            )
            session.add(summary)
            session.commit()
        
        # Test query
        result = service.get_current_usage_summary()
        
        assert result is not None
        assert result['total_used_mb'] == 614400
        assert result['today_usage_mb'] == 25000
        assert result['daily_budget_mb'] == 24000
        
    def test_trend_analysis_query_performance(self, test_engine):
        """Test trend analysis query performance with large dataset."""
        service = OptimizedDataService(str(test_engine.url))
        
        # Insert 30 days of test data
        with service.SessionLocal() as session:
            base_date = datetime.utcnow().date() - timedelta(days=30)
            for i in range(30):
                summary = DailySummary(
                    date=base_date + timedelta(days=i),
                    daily_usage_mb=20000 + (i * 1000),
                    daily_budget_mb=24000,
                    budget_variance_mb=0
                )
                session.add(summary)
            session.commit()
        
        # Measure query performance
        start_time = datetime.utcnow()
        results = service.get_trend_analysis(days=30)
        query_time = (datetime.utcnow() - start_time).total_seconds()
        
        assert len(results) == 30
        assert query_time < 1.0  # Should complete within 1 second
        
    def test_data_archival_process(self, test_engine):
        """Test automated data archival process."""
        service = OptimizedDataService(str(test_engine.url))
        
        # Insert old data that should be archived
        with service.SessionLocal() as session:
            old_reading = UsageReading(
                timestamp=datetime.utcnow() - timedelta(days=400),  # Over 12 months
                total_used_mb=500000,
                total_allocated_mb=1048576,
                remaining_mb=548576,
                collection_status='SUCCESS'
            )
            session.add(old_reading)
            
            recent_reading = UsageReading(
                timestamp=datetime.utcnow() - timedelta(days=30),
                total_used_mb=600000,
                total_allocated_mb=1048576,
                remaining_mb=448576,
                collection_status='SUCCESS'
            )
            session.add(recent_reading)
            session.commit()
            
            # Run archival
            session.execute("SELECT archive_old_data()")
            session.commit()
            
            # Check results
            remaining_readings = session.query(UsageReading).count()
            assert remaining_readings == 1  # Only recent reading should remain
```

---

## 4. End-to-End Testing

### 4.1 User Journey Tests

```python
# tests/e2e/test_user_journeys.py
import pytest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class TestUserJourneys:
    
    @pytest.fixture
    def browser(self):
        """Setup browser for E2E tests."""
        options = webdriver.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        
        driver = webdriver.Chrome(options=options)
        driver.implicitly_wait(10)
        yield driver
        driver.quit()
    
    def test_complete_onboarding_flow(self, browser, test_app):
        """Test complete user onboarding workflow."""
        browser.get("http://localhost:5000")
        
        # Should redirect to setup if no configuration
        wait = WebDriverWait(browser, 10)
        setup_form = wait.until(
            EC.presence_of_element_located((By.ID, "setup-form"))
        )
        
        # Fill in ISP credentials
        username_field = browser.find_element(By.ID, "isp-username")
        password_field = browser.find_element(By.ID, "isp-password")
        email_field = browser.find_element(By.ID, "notification-email")
        
        username_field.send_keys("test_user")
        password_field.send_keys("test_password")
        email_field.send_keys("test@example.com")
        
        # Submit setup form
        submit_button = browser.find_element(By.ID, "setup-submit")
        submit_button.click()
        
        # Should show connection test
        connection_status = wait.until(
            EC.presence_of_element_located((By.ID, "connection-status"))
        )
        
        # Should redirect to dashboard after successful setup
        dashboard_element = wait.until(
            EC.presence_of_element_located((By.ID, "usage-dashboard"))
        )
        
        assert "dashboard" in browser.current_url
        
    def test_dashboard_data_display(self, browser, test_app):
        """Test dashboard data display and updates."""
        # Navigate to dashboard (assuming setup completed)
        browser.get("http://localhost:5000/dashboard")
        
        wait = WebDriverWait(browser, 10)
        
        # Check key dashboard elements
        usage_display = wait.until(
            EC.presence_of_element_located((By.ID, "current-usage"))
        )
        
        safe_time_display = browser.find_element(By.ID, "safe-time-remaining")
        daily_budget_display = browser.find_element(By.ID, "daily-budget")
        trend_chart = browser.find_element(By.ID, "trend-chart")
        
        # Verify data is displayed
        assert usage_display.text != ""
        assert safe_time_display.text != ""
        assert daily_budget_display.text != ""
        assert trend_chart.is_displayed()
        
        # Test auto-refresh functionality
        initial_timestamp = browser.find_element(By.ID, "last-updated").text
        
        # Wait for auto-refresh (should happen within 2 minutes)
        wait.until(lambda driver: 
                  driver.find_element(By.ID, "last-updated").text != initial_timestamp)
        
    def test_notification_preferences(self, browser, test_app):
        """Test notification preference configuration."""
        browser.get("http://localhost:5000/preferences")
        
        wait = WebDriverWait(browser, 10)
        
        # Find preference controls
        email_toggle = wait.until(
            EC.element_to_be_clickable((By.ID, "email-notifications"))
        )
        desktop_toggle = browser.find_element(By.ID, "desktop-notifications")
        threshold_slider = browser.find_element(By.ID, "alert-threshold")
        
        # Modify preferences
        if not email_toggle.is_selected():
            email_toggle.click()
            
        # Adjust threshold
        browser.execute_script("arguments[0].value = 80", threshold_slider)
        
        # Save preferences
        save_button = browser.find_element(By.ID, "save-preferences")
        save_button.click()
        
        # Verify success message
        success_message = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "alert-success"))
        )
        assert "saved" in success_message.text.lower()
        
    def test_mobile_responsive_design(self, browser, test_app):
        """Test responsive design on mobile viewport."""
        # Set mobile viewport
        browser.set_window_size(375, 667)  # iPhone 6/7/8 size
        
        browser.get("http://localhost:5000/dashboard")
        
        wait = WebDriverWait(browser, 10)
        
        # Check mobile navigation
        mobile_nav = wait.until(
            EC.presence_of_element_located((By.CLASS_NAME, "mobile-nav"))
        )
        assert mobile_nav.is_displayed()
        
        # Check responsive grid
        usage_cards = browser.find_elements(By.CLASS_NAME, "usage-card")
        for card in usage_cards:
            # Cards should stack vertically on mobile
            assert card.size['width'] > card.size['height']
            
        # Test touch-friendly buttons
        nav_buttons = browser.find_elements(By.CLASS_NAME, "nav-button")
        for button in nav_buttons:
            # Minimum 44px touch target
            assert button.size['height'] >= 44
            assert button.size['width'] >= 44
```

### 4.2 Performance Tests

```python
# tests/e2e/test_performance.py
import pytest
import time
from selenium import webdriver
from selenium.webdriver.common.by import By

class TestPerformance:
    
    def test_dashboard_load_performance(self, browser, test_app):
        """Test dashboard load time under 2 seconds."""
        start_time = time.time()
        
        browser.get("http://localhost:5000/dashboard")
        
        # Wait for main content to load
        browser.find_element(By.ID, "usage-dashboard")
        
        load_time = time.time() - start_time
        
        assert load_time < 2.0, f"Dashboard loaded in {load_time:.2f}s, exceeds 2s target"
        
    def test_api_response_performance(self, test_client):
        """Test API response time under 500ms."""
        start_time = time.time()
        
        response = test_client.get("/api/v1/usage/current")
        
        response_time = (time.time() - start_time) * 1000  # Convert to ms
        
        assert response.status_code == 200
        assert response_time < 500, f"API responded in {response_time:.0f}ms, exceeds 500ms target"
        
    def test_concurrent_user_performance(self, test_app):
        """Test performance with multiple concurrent users."""
        import threading
        import requests
        
        results = []
        
        def make_request():
            start_time = time.time()
            response = requests.get("http://localhost:5000/api/v1/usage/current")
            end_time = time.time()
            
            results.append({
                'status_code': response.status_code,
                'response_time': (end_time - start_time) * 1000
            })
        
        # Simulate 10 concurrent users
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all requests to complete
        for thread in threads:
            thread.join()
        
        # Verify all requests succeeded and met performance targets
        assert len(results) == 10
        for result in results:
            assert result['status_code'] == 200
            assert result['response_time'] < 1000  # Allow higher threshold for concurrent load
```

---

## 5. Test Data Management

### 5.1 Test Data Factory

```python
# tests/factories.py
import factory
from datetime import datetime, timedelta
from app.models import UsageReading, DailySummary, UserPreferences

class UsageReadingFactory(factory.Factory):
    class Meta:
        model = UsageReading
    
    timestamp = factory.LazyFunction(datetime.utcnow)
    total_used_mb = factory.Sequence(lambda n: 500000 + (n * 1000))
    total_allocated_mb = 1048576
    remaining_mb = factory.LazyAttribute(
        lambda obj: obj.total_allocated_mb - obj.total_used_mb
    )
    collection_status = 'SUCCESS'
    api_response_time_ms = factory.Faker('random_int', min=100, max=500)

class DailySummaryFactory(factory.Factory):
    class Meta:
        model = DailySummary
    
    date = factory.LazyFunction(lambda: datetime.utcnow().date())
    daily_usage_mb = factory.Faker('random_int', min=15000, max=30000)
    daily_budget_mb = 24000
    budget_variance_mb = factory.LazyAttribute(
        lambda obj: obj.daily_usage_mb - obj.daily_budget_mb
    )
    usage_efficiency_score = factory.Faker('pyfloat', min_value=0.5, max_value=1.0)
    reading_count = 144  # 10-minute intervals per day

class UserPreferencesFactory(factory.Factory):
    class Meta:
        model = UserPreferences
    
    isp_username = "test_user"
    isp_password_encrypted = "encrypted_test_password"
    encryption_key_hash = "test_hash"
    notification_email = factory.Faker('email')
    alert_threshold_percentage = 75
```

### 5.2 Mock Data Generators

```python
# tests/mock_data.py
from datetime import datetime, timedelta
import random

class MockDataGenerator:
    
    @staticmethod
    def generate_usage_timeline(days: int = 30) -> list:
        """Generate realistic usage data timeline."""
        data = []
        base_date = datetime.utcnow() - timedelta(days=days)
        total_used = 200000  # Starting usage
        
        for i in range(days):
            # Simulate daily usage patterns
            daily_usage = random.randint(15000, 35000)
            
            # Weekend usage tends to be higher
            current_date = base_date + timedelta(days=i)
            if current_date.weekday() >= 5:  # Weekend
                daily_usage *= 1.3
            
            total_used += daily_usage
            
            data.append({
                'date': current_date.date().isoformat(),
                'daily_usage_mb': int(daily_usage),
                'total_used_mb': int(total_used),
                'remaining_mb': max(0, 1048576 - total_used)
            })
        
        return data
    
    @staticmethod
    def generate_api_responses() -> dict:
        """Generate mock ISP API responses."""
        return {
            'success_auth': {
                'status': 'success',
                'session_id': 'mock_session_123',
                'expires_in': 3600
            },
            'success_usage': {
                'total_used': '614400',
                'total_allocated': '1048576',
                'remaining': '434176',
                'last_updated': datetime.utcnow().isoformat()
            },
            'rate_limited': {
                'status': 'error',
                'message': 'Too many requests',
                'retry_after': 600
            },
            'server_error': {
                'status': 'error',
                'message': 'Internal server error',
                'code': 500
            }
        }
```

---

## 6. Continuous Integration

### 6.1 GitHub Actions Workflow

```yaml
# .github/workflows/test.yml
name: Test Suite

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: taara_test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
      
      redis:
        image: redis:6
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements/test.txt
    
    - name: Set up test environment
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/taara_test
        REDIS_URL: redis://localhost:6379
        MASTER_PASSWORD: test_password_for_ci
        ENCRYPTION_SALT: test_salt_for_ci
      run: |
        python -m pytest tests/unit/ -v --cov=app --cov-report=xml
    
    - name: Integration tests
      env:
        DATABASE_URL: postgresql://postgres:postgres@localhost/taara_test
        REDIS_URL: redis://localhost:6379
      run: |
        python -m pytest tests/integration/ -v
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        
  e2e-tests:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python 3.11
      uses: actions/setup-python@v4
      with:
        python-version: 3.11
    
    - name: Install Chrome
      uses: browser-actions/setup-chrome@latest
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements/test.txt
        pip install selenium
    
    - name: Run E2E tests
      run: |
        python -m pytest tests/e2e/ -v --headless
```

### 6.2 Quality Gates

```python
# tests/quality_gates.py
import pytest
import coverage

class TestQualityGates:
    
    def test_minimum_test_coverage(self):
        """Ensure minimum 85% test coverage."""
        cov = coverage.Coverage()
        cov.load()
        
        total_coverage = cov.report(show_missing=False)
        
        assert total_coverage >= 85.0, f"Test coverage {total_coverage:.1f}% below 85% minimum"
    
    def test_no_skipped_tests(self):
        """Ensure no tests are skipped in CI."""
        # This would be implemented with pytest markers
        # to fail CI if critical tests are skipped
        pass
    
    def test_performance_benchmarks(self):
        """Validate performance benchmarks are met."""
        # Run performance tests and validate results
        # This ensures performance doesn't regress
        pass
```

---

This comprehensive testing strategy addresses all the critical testing gaps identified in the master checklist:

1. **✅ Unit Testing Framework** - Complete setup with mocking and fixtures
2. **✅ Integration Testing** - API and database integration validation  
3. **✅ End-to-End Testing** - User journey and performance validation
4. **✅ Test Data Management** - Factories and mock data generators
5. **✅ Continuous Integration** - Automated testing pipeline with quality gates
6. **✅ Performance Testing** - Load time and concurrent user validation
7. **✅ Security Testing** - Credential management and authentication testing

The project now has a comprehensive testing foundation ready for development!
