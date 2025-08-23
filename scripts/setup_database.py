#!/usr/bin/env python3
"""
Database Setup Script for Taara Internet Usage Monitoring System

This script MUST be run before any application code that uses the database.
It establishes the complete database schema with proper constraints and indexes.

Usage:
    python scripts/setup_database.py [--environment=dev|staging|prod]
    
Prerequisites:
    - PostgreSQL server running and accessible
    - Database credentials configured in environment
    - SQLAlchemy and Alembic installed
"""

import os
import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from alembic.config import Config
from alembic import command
from app.models import db
from app import create_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_prerequisites():
    """Verify all prerequisites are met before database setup."""
    logger.info("Checking prerequisites...")
    
    # Check for required environment variables
    required_env_vars = [
        'DATABASE_URL',
        'SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        logger.error("Please configure environment variables before running setup.")
        return False
    
    # Check database connectivity
    try:
        engine = create_engine(os.getenv('DATABASE_URL'))
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connectivity verified")
        return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        return False

def create_database_schema():
    """Create the complete database schema with all tables and constraints."""
    logger.info("Creating database schema...")
    
    try:
        app = create_app()
        with app.app_context():
            # Create all tables
            db.create_all()
            logger.info("Database tables created successfully")
            
            # Verify table creation
            engine = db.engine
            with engine.connect() as conn:
                # Check that all expected tables exist
                expected_tables = [
                    'usage_readings',
                    'daily_summaries', 
                    'user_preferences',
                    'alert_history'
                ]
                
                for table in expected_tables:
                    result = conn.execute(text(f"""
                        SELECT EXISTS (
                            SELECT FROM information_schema.tables 
                            WHERE table_name = '{table}'
                        );
                    """))
                    if not result.scalar():
                        raise Exception(f"Table {table} was not created")
                
                logger.info("All expected tables verified")
                
    except Exception as e:
        logger.error(f"Schema creation failed: {e}")
        raise

def setup_alembic():
    """Initialize Alembic for database migrations."""
    logger.info("Setting up Alembic migrations...")
    
    try:
        alembic_cfg = Config("alembic.ini")
        
        # Initialize Alembic if not already done
        migrations_dir = Path("migrations")
        if not migrations_dir.exists():
            command.init(alembic_cfg, "migrations")
            logger.info("Alembic initialized")
        
        # Stamp the database with the current revision
        command.stamp(alembic_cfg, "head")
        logger.info("Database stamped with current migration version")
        
    except Exception as e:
        logger.error(f"Alembic setup failed: {e}")
        raise

def create_indexes():
    """Create performance indexes for time-series data queries."""
    logger.info("Creating performance indexes...")
    
    index_queries = [
        # Performance index for usage_readings timestamp queries
        """
        CREATE INDEX IF NOT EXISTS idx_usage_readings_timestamp_desc 
        ON usage_readings(timestamp DESC);
        """,
        
        # Index for usage_readings status filtering
        """
        CREATE INDEX IF NOT EXISTS idx_usage_readings_status 
        ON usage_readings(collection_status);
        """,
        
        # Composite index for usage_readings by date range
        """
        CREATE INDEX IF NOT EXISTS idx_usage_readings_date_status 
        ON usage_readings(timestamp, collection_status);
        """,
        
        # Index for daily_summaries date queries
        """
        CREATE INDEX IF NOT EXISTS idx_daily_summaries_date_desc 
        ON daily_summaries(date DESC);
        """,
        
        # Index for alert_history type and date
        """
        CREATE INDEX IF NOT EXISTS idx_alert_history_type_sent 
        ON alert_history(alert_type, sent_at DESC);
        """,
        
        # Index for alert_history delivery status
        """
        CREATE INDEX IF NOT EXISTS idx_alert_history_delivery_status 
        ON alert_history(delivery_status, sent_at DESC);
        """
    ]
    
    try:
        app = create_app()
        with app.app_context():
            engine = db.engine
            with engine.connect() as conn:
                for query in index_queries:
                    conn.execute(text(query))
                    conn.commit()
                logger.info("Performance indexes created successfully")
                
    except Exception as e:
        logger.error(f"Index creation failed: {e}")
        raise

def setup_user_preferences_defaults():
    """Create default user preferences record if none exists."""
    logger.info("Setting up default user preferences...")
    
    try:
        app = create_app()
        with app.app_context():
            from app.models.user_preferences import UserPreferences
            
            # Check if preferences already exist
            existing = UserPreferences.query.first()
            if existing:
                logger.info("User preferences already exist, skipping default creation")
                return
            
            # Create default preferences (credentials will be set during onboarding)
            default_prefs = UserPreferences(
                isp_username="",  # Will be set during setup wizard
                isp_password_encrypted="",  # Will be set during setup wizard
                encryption_key_hash="",  # Will be generated during setup wizard
                notification_email="",  # Will be set by user
                email_enabled=True,
                desktop_notifications_enabled=True,
                alert_threshold_percentage=75,
                daily_budget_alerts=True,
                weekly_summary_enabled=True,
                timezone='UTC'
            )
            
            db.session.add(default_prefs)
            db.session.commit()
            logger.info("Default user preferences created")
            
    except Exception as e:
        logger.error(f"User preferences setup failed: {e}")
        raise

def validate_schema():
    """Validate that the database schema matches expectations."""
    logger.info("Validating database schema...")
    
    try:
        app = create_app()
        with app.app_context():
            engine = db.engine
            with engine.connect() as conn:
                # Test essential constraints
                test_queries = [
                    # Test usage_readings constraints
                    """
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'usage_readings' 
                    AND column_name IN ('timestamp', 'total_used_mb', 'collection_status');
                    """,
                    
                    # Test daily_summaries constraints
                    """
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'daily_summaries' 
                    AND column_name IN ('date', 'daily_usage_mb', 'daily_budget_mb');
                    """,
                    
                    # Test user_preferences constraints
                    """
                    SELECT column_name, data_type, is_nullable 
                    FROM information_schema.columns 
                    WHERE table_name = 'user_preferences' 
                    AND column_name IN ('isp_username', 'alert_threshold_percentage');
                    """
                ]
                
                for query in test_queries:
                    result = conn.execute(text(query))
                    rows = result.fetchall()
                    if not rows:
                        raise Exception("Schema validation failed - missing expected columns")
                
                logger.info("Database schema validation passed")
                
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        raise

def main():
    """Main setup function that orchestrates database initialization."""
    environment = os.getenv('FLASK_ENV', 'development')
    logger.info(f"Starting database setup for environment: {environment}")
    
    try:
        # Step 1: Check prerequisites
        if not check_prerequisites():
            logger.error("Prerequisites check failed. Aborting setup.")
            sys.exit(1)
        
        # Step 2: Create database schema
        create_database_schema()
        
        # Step 3: Setup Alembic for migrations
        setup_alembic()
        
        # Step 4: Create performance indexes
        create_indexes()
        
        # Step 5: Setup default user preferences
        setup_user_preferences_defaults()
        
        # Step 6: Validate schema
        validate_schema()
        
        logger.info("Database setup completed successfully!")
        logger.info("Database is ready for application use.")
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        logger.error("Please fix the errors and run the setup again.")
        sys.exit(1)

if __name__ == "__main__":
    main()
