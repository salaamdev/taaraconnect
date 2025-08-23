#!/usr/bin/env python3
"""
ISP API Mock Server for Testing

This mock server simulates the Taara ISP API for reliable testing without
depending on the actual ISP infrastructure. It MUST be running before
any tests that involve ISP API integration.

Usage:
    python scripts/mock_isp_api.py [--port=8080] [--scenario=normal]
    
Scenarios:
    - normal: Standard responses with realistic usage data
    - slow: Responses with delays to test timeout handling
    - error: Error responses to test failure scenarios
    - offline: Simulates complete API unavailability
"""

import json
import time
import random
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, session
from werkzeug.exceptions import Unauthorized, ServiceUnavailable
import argparse
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = 'mock_isp_secret_key'

# Mock data storage
mock_sessions = {}
current_scenario = 'normal'

# Realistic usage data patterns
BASE_USAGE_MB = 614400  # ~600GB used of 1TB allocation
DAILY_VARIATION = 25000  # ±25GB daily variation
HOURLY_VARIATION = 2000  # ±2GB hourly variation

def get_current_usage():
    """Generate realistic usage data based on time of day."""
    now = datetime.now()
    
    # Simulate daily usage patterns
    hour = now.hour
    if 6 <= hour <= 10:  # Morning peak
        usage_modifier = 1.2
    elif 18 <= hour <= 23:  # Evening peak
        usage_modifier = 1.5
    elif 0 <= hour <= 6:  # Night low usage
        usage_modifier = 0.3
    else:  # Day moderate usage
        usage_modifier = 1.0
    
    # Add some randomness
    daily_offset = random.randint(-DAILY_VARIATION, DAILY_VARIATION)
    hourly_offset = random.randint(-HOURLY_VARIATION, HOURLY_VARIATION) * usage_modifier
    
    current_usage = BASE_USAGE_MB + daily_offset + int(hourly_offset)
    
    # Ensure usage doesn't exceed allocation or go negative
    current_usage = max(0, min(current_usage, 1048576))  # 1TB = 1,048,576 MB
    
    return current_usage

@app.route('/login', methods=['POST'])
def login():
    """Mock ISP login endpoint."""
    global current_scenario
    
    if current_scenario == 'offline':
        raise ServiceUnavailable("ISP API temporarily unavailable")
    
    if current_scenario == 'slow':
        time.sleep(5)  # Simulate slow response
    
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')
    
    # Simulate authentication
    if not username or not password:
        raise Unauthorized("Username and password required")
    
    if current_scenario == 'error' and random.random() < 0.3:
        raise Unauthorized("Authentication failed")
    
    # Valid test credentials
    valid_credentials = {
        'test_user': 'test_password',
        'demo_user': 'demo_password',
        'family_admin': 'secure_password'
    }
    
    if username not in valid_credentials or valid_credentials[username] != password:
        raise Unauthorized("Invalid credentials")
    
    # Create mock session
    session_id = f"mock_session_{int(time.time())}_{random.randint(1000, 9999)}"
    mock_sessions[session_id] = {
        'username': username,
        'created_at': datetime.now(),
        'last_accessed': datetime.now()
    }
    
    session['session_id'] = session_id
    
    logger.info(f"Mock login successful for user: {username}")
    
    return jsonify({
        'status': 'success',
        'message': 'Authentication successful',
        'session_id': session_id
    })

@app.route('/usage', methods=['GET'])
def get_usage():
    """Mock ISP usage data endpoint."""
    global current_scenario
    
    if current_scenario == 'offline':
        raise ServiceUnavailable("ISP API temporarily unavailable")
    
    if current_scenario == 'slow':
        time.sleep(3)  # Simulate slow response
    
    # Check session
    session_id = session.get('session_id')
    if not session_id or session_id not in mock_sessions:
        raise Unauthorized("Invalid or expired session")
    
    # Update last accessed time
    mock_sessions[session_id]['last_accessed'] = datetime.now()
    
    if current_scenario == 'error' and random.random() < 0.2:
        return jsonify({'error': 'Internal server error'}), 500
    
    # Generate realistic usage data
    total_used_mb = get_current_usage()
    total_allocated_mb = 1048576  # 1TB
    remaining_mb = total_allocated_mb - total_used_mb
    
    # Calculate additional metrics
    percentage_used = (total_used_mb / total_allocated_mb) * 100
    
    # Simulate billing cycle (30 days)
    today = datetime.now()
    billing_start = today.replace(day=1)
    days_in_cycle = 30
    days_elapsed = (today - billing_start).days + 1
    days_remaining = days_in_cycle - days_elapsed
    
    response_data = {
        'status': 'success',
        'timestamp': datetime.now().isoformat(),
        'usage': {
            'total_used_mb': total_used_mb,
            'total_allocated_mb': total_allocated_mb,
            'remaining_mb': remaining_mb,
            'percentage_used': round(percentage_used, 2),
            'billing_cycle': {
                'start_date': billing_start.isoformat(),
                'days_elapsed': days_elapsed,
                'days_remaining': days_remaining,
                'total_days': days_in_cycle
            }
        },
        'connection': {
            'status': 'active',
            'download_speed_mbps': random.randint(45, 55),  # ~50 Mbps
            'upload_speed_mbps': random.randint(8, 12),     # ~10 Mbps
            'latency_ms': random.randint(15, 25)            # ~20ms
        }
    }
    
    logger.info(f"Mock usage data returned: {total_used_mb}MB used of {total_allocated_mb}MB")
    
    return jsonify(response_data)

@app.route('/status', methods=['GET'])
def get_status():
    """Mock ISP status endpoint."""
    global current_scenario
    
    if current_scenario == 'offline':
        raise ServiceUnavailable("ISP API temporarily unavailable")
    
    # Check session
    session_id = session.get('session_id')
    if not session_id or session_id not in mock_sessions:
        raise Unauthorized("Invalid or expired session")
    
    return jsonify({
        'status': 'success',
        'api_version': '1.0',
        'server_time': datetime.now().isoformat(),
        'session_valid': True,
        'maintenance_mode': False
    })

@app.route('/logout', methods=['POST'])
def logout():
    """Mock ISP logout endpoint."""
    session_id = session.get('session_id')
    if session_id and session_id in mock_sessions:
        del mock_sessions[session_id]
        session.pop('session_id', None)
        logger.info("Mock logout successful")
    
    return jsonify({
        'status': 'success',
        'message': 'Logout successful'
    })

# Administrative endpoints for testing control

@app.route('/mock/scenario', methods=['POST'])
def set_scenario():
    """Change the mock scenario for testing different conditions."""
    global current_scenario
    data = request.get_json() or {}
    scenario = data.get('scenario', 'normal')
    
    valid_scenarios = ['normal', 'slow', 'error', 'offline']
    if scenario in valid_scenarios:
        current_scenario = scenario
        logger.info(f"Mock scenario changed to: {scenario}")
        return jsonify({'status': 'success', 'scenario': scenario})
    else:
        return jsonify({
            'status': 'error', 
            'message': f'Invalid scenario. Valid options: {valid_scenarios}'
        }), 400

@app.route('/mock/sessions', methods=['GET'])
def get_sessions():
    """Get current active mock sessions."""
    active_sessions = []
    now = datetime.now()
    
    for session_id, session_data in mock_sessions.items():
        # Remove expired sessions (24 hours)
        if (now - session_data['last_accessed']).total_seconds() > 86400:
            continue
            
        active_sessions.append({
            'session_id': session_id,
            'username': session_data['username'],
            'created_at': session_data['created_at'].isoformat(),
            'last_accessed': session_data['last_accessed'].isoformat()
        })
    
    return jsonify({
        'status': 'success',
        'active_sessions': active_sessions,
        'current_scenario': current_scenario
    })

@app.route('/mock/health', methods=['GET'])
def health():
    """Health check endpoint for the mock server."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'scenario': current_scenario,
        'active_sessions': len(mock_sessions)
    })

@app.errorhandler(401)
def unauthorized(error):
    return jsonify({
        'status': 'error',
        'error_code': 'UNAUTHORIZED',
        'message': str(error.description)
    }), 401

@app.errorhandler(503)
def service_unavailable(error):
    return jsonify({
        'status': 'error',
        'error_code': 'SERVICE_UNAVAILABLE',
        'message': str(error.description)
    }), 503

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        'status': 'error',
        'error_code': 'INTERNAL_ERROR',
        'message': 'Internal server error'
    }), 500

def cleanup_expired_sessions():
    """Clean up expired sessions periodically."""
    global mock_sessions
    now = datetime.now()
    expired_sessions = []
    
    for session_id, session_data in mock_sessions.items():
        if (now - session_data['last_accessed']).total_seconds() > 86400:  # 24 hours
            expired_sessions.append(session_id)
    
    for session_id in expired_sessions:
        del mock_sessions[session_id]
    
    if expired_sessions:
        logger.info(f"Cleaned up {len(expired_sessions)} expired sessions")

def main():
    parser = argparse.ArgumentParser(description='Taara ISP API Mock Server')
    parser.add_argument('--port', type=int, default=8080, help='Port to run the mock server on')
    parser.add_argument('--scenario', choices=['normal', 'slow', 'error', 'offline'], 
                       default='normal', help='Initial testing scenario')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    args = parser.parse_args()
    
    global current_scenario
    current_scenario = args.scenario
    
    logger.info(f"Starting Taara ISP API Mock Server on port {args.port}")
    logger.info(f"Initial scenario: {current_scenario}")
    logger.info("Available endpoints:")
    logger.info("  POST /login - Authenticate with ISP")
    logger.info("  GET /usage - Get current usage data")
    logger.info("  GET /status - Check API status")
    logger.info("  POST /logout - End session")
    logger.info("  POST /mock/scenario - Change testing scenario")
    logger.info("  GET /mock/sessions - View active sessions")
    logger.info("  GET /mock/health - Health check")
    
    app.run(host='0.0.0.0', port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()
