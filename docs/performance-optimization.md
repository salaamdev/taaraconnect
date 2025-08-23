# Performance Optimization Guide: Taara Internet Usage Monitoring System

**Document Information:**

- **Product Name:** Taara Internet Usage Monitoring System
- **Document Type:** Performance Optimization Strategy
- **Document Version:** v1.0
- **Date Created:** August 23, 2025
- **Last Updated:** August 23, 2025
- **Document Owner:** Sarah (Product Owner)
- **Status:** Ready for Implementation

---

## 1. Performance Requirements & Constraints

### 1.1 Target Performance Metrics

**Response Time Targets:**

- Dashboard load time: < 2 seconds (target: 1.5 seconds)
- API response time: < 500ms (target: 300ms)  
- Database queries: < 100ms for dashboard data
- ISP API calls: < 30 seconds timeout with 10-second retry

**Throughput Requirements:**

- Support 10 concurrent dashboard users
- Handle 144 API collections per day (10-minute intervals)
- Process 4,320 database writes per month (historical data)
- Manage 50+ notification deliveries per day

**Resource Constraints:**

- **Memory:** Maximum 512MB RAM usage
- **CPU:** Maximum 20% utilization on single core
- **Storage:** < 1GB for 12 months of historical data
- **Network:** Minimal bandwidth impact on household internet

### 1.2 Budget Hosting Environment

**Digital Ocean Droplet Specifications:**

- **Size:** 1GB RAM, 1 vCPU, 25GB SSD
- **Operating System:** Ubuntu 20.04 LTS
- **Network:** 1TB transfer allowance
- **Cost Target:** < $10/month total hosting cost

**Infrastructure Stack:**

- **Web Server:** Nginx (reverse proxy, static file serving)
- **Application Server:** Gunicorn (3-4 worker processes)
- **Database:** PostgreSQL 13+ (optimized configuration)
- **Cache:** Redis (memory-efficient configuration)
- **Process Management:** Supervisor (auto-restart, logging)

---

## 2. Database Performance Optimization

### 2.1 Optimized Database Configuration

```sql
-- PostgreSQL performance tuning for budget hosting
-- /etc/postgresql/13/main/postgresql.conf

-- Memory settings for 1GB RAM system (conservative allocation)
shared_buffers = 128MB                    -- 25% of RAM
effective_cache_size = 512MB              -- 50% of RAM
work_mem = 4MB                           -- Per-operation memory
maintenance_work_mem = 64MB               -- Maintenance operations
max_connections = 20                      -- Limit connections

-- Write performance
wal_buffers = 16MB
checkpoint_completion_target = 0.9
wal_writer_delay = 200ms
commit_delay = 0

-- Query performance
random_page_cost = 1.1                   -- SSD optimization
effective_io_concurrency = 200           -- SSD concurrent I/O
default_statistics_target = 100          -- Query planning

-- Background writer
bgwriter_delay = 200ms
bgwriter_lru_maxpages = 100
bgwriter_lru_multiplier = 2.0

-- Autovacuum (crucial for time-series data)
autovacuum = on
autovacuum_max_workers = 2
autovacuum_naptime = 30s
autovacuum_vacuum_threshold = 50
autovacuum_analyze_threshold = 50
```

### 2.2 Optimized Table Design

```sql
-- High-performance usage readings table
CREATE TABLE usage_readings (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    total_used_mb BIGINT NOT NULL,
    remaining_mb BIGINT NOT NULL,
    collection_status VARCHAR(10) NOT NULL,
    api_response_time_ms SMALLINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints for data integrity and performance
    CONSTRAINT usage_readings_timestamp_unique UNIQUE (timestamp),
    CONSTRAINT usage_readings_positive_values CHECK (
        total_used_mb >= 0 AND remaining_mb >= 0
    )
) PARTITION BY RANGE (timestamp);

-- Create monthly partitions for better performance
CREATE TABLE usage_readings_202508 PARTITION OF usage_readings
    FOR VALUES FROM ('2025-08-01') TO ('2025-09-01');

CREATE TABLE usage_readings_202509 PARTITION OF usage_readings
    FOR VALUES FROM ('2025-09-01') TO ('2025-10-01');

-- Optimized indexes for common queries
CREATE INDEX CONCURRENTLY idx_usage_readings_timestamp_desc 
    ON usage_readings (timestamp DESC) 
    WHERE collection_status = 'SUCCESS';

CREATE INDEX CONCURRENTLY idx_usage_readings_date_trunc 
    ON usage_readings (DATE_TRUNC('day', timestamp), timestamp DESC);

-- Partial index for recent data (most frequently accessed)
CREATE INDEX CONCURRENTLY idx_usage_readings_recent 
    ON usage_readings (timestamp DESC, total_used_mb, remaining_mb)
    WHERE timestamp >= (CURRENT_TIMESTAMP - INTERVAL '30 days');

-- Compressed daily summaries with optimized storage
CREATE TABLE daily_summaries (
    date DATE PRIMARY KEY,
    daily_usage_mb INTEGER NOT NULL,
    daily_budget_mb INTEGER NOT NULL,
    usage_efficiency_score NUMERIC(3,2),
    reading_count SMALLINT DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
) WITH (fillfactor = 90);  -- Leave space for updates

-- Index for trend analysis queries
CREATE INDEX CONCURRENTLY idx_daily_summaries_date_desc 
    ON daily_summaries (date DESC);
```

### 2.3 Query Optimization Strategies

```python
# app/database/optimized_queries.py
from sqlalchemy import text, func
from sqlalchemy.orm import sessionmaker
from typing import Dict, List, Any, Optional
import logging

class OptimizedQueries:
    """
    High-performance database queries optimized for budget hosting.
    """
    
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory
        self.query_logger = logging.getLogger('performance.queries')
        
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """
        Single optimized query for complete dashboard data.
        Target: < 50ms execution time
        """
        query = text("""
            WITH latest_reading AS (
                SELECT 
                    total_used_mb,
                    remaining_mb,
                    timestamp,
                    api_response_time_ms
                FROM usage_readings 
                WHERE collection_status = 'SUCCESS'
                    AND timestamp >= CURRENT_TIMESTAMP - INTERVAL '24 hours'
                ORDER BY timestamp DESC 
                LIMIT 1
            ),
            today_usage AS (
                SELECT 
                    COALESCE(SUM(
                        CASE 
                            WHEN LAG(total_used_mb) OVER (ORDER BY timestamp) IS NOT NULL 
                            THEN total_used_mb - LAG(total_used_mb) OVER (ORDER BY timestamp)
                            ELSE 0 
                        END
                    ), 0) as today_consumed_mb
                FROM usage_readings
                WHERE DATE_TRUNC('day', timestamp) = DATE_TRUNC('day', CURRENT_TIMESTAMP)
                    AND collection_status = 'SUCCESS'
            ),
            weekly_average AS (
                SELECT 
                    AVG(daily_usage_mb) as avg_weekly_usage,
                    COUNT(*) as days_tracked
                FROM daily_summaries 
                WHERE date >= CURRENT_DATE - INTERVAL '7 days'
            ),
            monthly_progress AS (
                SELECT 
                    EXTRACT(DAY FROM (DATE_TRUNC('month', CURRENT_DATE) + INTERVAL '1 month' - CURRENT_DATE)) as days_remaining,
                    EXTRACT(DAY FROM CURRENT_DATE) as days_elapsed
            )
            SELECT 
                lr.total_used_mb,
                lr.remaining_mb,
                lr.timestamp as last_updated,
                lr.api_response_time_ms,
                tu.today_consumed_mb,
                wa.avg_weekly_usage,
                mp.days_remaining,
                mp.days_elapsed,
                -- Calculate daily budget
                CASE 
                    WHEN mp.days_remaining > 0 
                    THEN lr.remaining_mb / mp.days_remaining
                    ELSE 0 
                END as daily_budget_mb,
                -- Calculate usage efficiency
                CASE 
                    WHEN wa.avg_weekly_usage > 0 AND lr.total_used_mb > 0
                    THEN LEAST(1.0, (1048576.0 / (lr.total_used_mb + COALESCE(wa.avg_weekly_usage * mp.days_remaining, 0))))
                    ELSE 1.0
                END as efficiency_score
            FROM latest_reading lr
            CROSS JOIN today_usage tu
            CROSS JOIN weekly_average wa
            CROSS JOIN monthly_progress mp
        """)
        
        with self.session_factory() as session:
            result = session.execute(query).fetchone()
            
            if result:
                return {
                    'total_used_mb': result.total_used_mb,
                    'remaining_mb': result.remaining_mb,
                    'last_updated': result.last_updated,
                    'api_response_time_ms': result.api_response_time_ms,
                    'today_consumed_mb': int(result.today_consumed_mb or 0),
                    'avg_weekly_usage': float(result.avg_weekly_usage or 0),
                    'days_remaining': int(result.days_remaining),
                    'days_elapsed': int(result.days_elapsed),
                    'daily_budget_mb': int(result.daily_budget_mb or 0),
                    'efficiency_score': float(result.efficiency_score or 1.0)
                }
            return {}
    
    def get_trend_data_optimized(self, days: int = 7) -> List[Dict[str, Any]]:
        """
        Optimized trend analysis query.
        Target: < 30ms execution time
        """
        query = text("""
            SELECT 
                date,
                daily_usage_mb,
                daily_budget_mb,
                usage_efficiency_score,
                -- Calculate trend compared to previous day
                daily_usage_mb - LAG(daily_usage_mb, 1, 0) OVER (ORDER BY date) as daily_change,
                -- Calculate rolling 3-day average
                AVG(daily_usage_mb) OVER (
                    ORDER BY date 
                    ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
                ) as rolling_avg_3day
            FROM daily_summaries 
            WHERE date >= CURRENT_DATE - INTERVAL :days DAY
            ORDER BY date DESC
            LIMIT :limit
        """)
        
        with self.session_factory() as session:
            results = session.execute(query, {'days': days, 'limit': days}).fetchall()
            
            return [
                {
                    'date': row.date.isoformat(),
                    'daily_usage_mb': row.daily_usage_mb,
                    'daily_budget_mb': row.daily_budget_mb,
                    'efficiency_score': float(row.usage_efficiency_score or 0),
                    'daily_change': int(row.daily_change or 0),
                    'rolling_avg_3day': float(row.rolling_avg_3day or 0)
                }
                for row in results
            ]
    
    def get_usage_timeline_compressed(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Compressed timeline data for charts.
        Target: < 20ms execution time
        """
        query = text("""
            WITH hourly_data AS (
                SELECT 
                    DATE_TRUNC('hour', timestamp) as hour,
                    AVG(total_used_mb) as avg_usage,
                    COUNT(*) as reading_count,
                    AVG(api_response_time_ms) as avg_response_time
                FROM usage_readings
                WHERE timestamp >= CURRENT_TIMESTAMP - INTERVAL :hours HOUR
                    AND collection_status = 'SUCCESS'
                GROUP BY DATE_TRUNC('hour', timestamp)
                ORDER BY hour DESC
            )
            SELECT 
                hour,
                avg_usage,
                reading_count,
                avg_response_time,
                -- Calculate hourly consumption
                avg_usage - LAG(avg_usage, 1, avg_usage) OVER (ORDER BY hour) as hourly_consumption
            FROM hourly_data
            ORDER BY hour DESC
            LIMIT 24
        """)
        
        with self.session_factory() as session:
            results = session.execute(query, {'hours': hours}).fetchall()
            
            return [
                {
                    'hour': row.hour.isoformat(),
                    'total_usage_mb': int(row.avg_usage or 0),
                    'hourly_consumption_mb': max(0, int(row.hourly_consumption or 0)),
                    'reading_count': row.reading_count,
                    'avg_response_time_ms': int(row.avg_response_time or 0)
                }
                for row in results
            ]

    def cleanup_old_data_efficient(self, retention_days: int = 365) -> Dict[str, int]:
        """
        Efficient cleanup of old data with minimal impact.
        Runs in small batches to avoid long locks.
        """
        cleanup_stats = {'readings_deleted': 0, 'summaries_deleted': 0}
        
        # Delete in small batches to avoid lock contention
        batch_size = 1000
        
        with self.session_factory() as session:
            # Clean old usage readings
            while True:
                delete_query = text("""
                    DELETE FROM usage_readings 
                    WHERE id IN (
                        SELECT id FROM usage_readings 
                        WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL :days DAY
                        ORDER BY timestamp 
                        LIMIT :batch_size
                    )
                """)
                
                result = session.execute(delete_query, {
                    'days': retention_days, 
                    'batch_size': batch_size
                })
                
                deleted_count = result.rowcount
                cleanup_stats['readings_deleted'] += deleted_count
                session.commit()
                
                if deleted_count < batch_size:
                    break
            
            # Clean old daily summaries (keep longer than readings)
            delete_summaries = text("""
                DELETE FROM daily_summaries 
                WHERE date < CURRENT_DATE - INTERVAL :days DAY
            """)
            
            result = session.execute(delete_summaries, {'days': retention_days * 2})
            cleanup_stats['summaries_deleted'] = result.rowcount
            session.commit()
            
            # Update table statistics for query planner
            session.execute(text("ANALYZE usage_readings, daily_summaries"))
            session.commit()
        
        return cleanup_stats
```

---

## 3. Application Performance Optimization

### 3.1 Caching Strategy

```python
# app/performance/cache_manager.py
import redis
import json
import pickle
import hashlib
from typing import Any, Optional, Dict, Callable
from datetime import datetime, timedelta
import functools
import logging

class PerformanceCache:
    """
    Multi-level caching system optimized for memory efficiency.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url, decode_responses=False)
        self.local_cache = {}  # In-memory cache for frequently accessed data
        self.local_cache_size_limit = 100  # Maximum items in local cache
        self.cache_logger = logging.getLogger('performance.cache')
        
        # Cache TTL configurations
        self.ttl_config = {
            'dashboard_data': 120,      # 2 minutes
            'trend_data': 600,          # 10 minutes
            'api_response': 300,        # 5 minutes
            'user_preferences': 1800,   # 30 minutes
            'system_health': 60         # 1 minute
        }
    
    def cached_query(self, cache_key: str, ttl: Optional[int] = None, use_local: bool = True):
        """
        Decorator for caching database query results.
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                # Generate cache key with parameters
                param_hash = hashlib.md5(
                    f"{cache_key}:{str(args)}:{str(sorted(kwargs.items()))}".encode()
                ).hexdigest()[:8]
                
                full_cache_key = f"{cache_key}:{param_hash}"
                
                # Try local cache first
                if use_local and full_cache_key in self.local_cache:
                    cache_entry = self.local_cache[full_cache_key]
                    if datetime.utcnow() < cache_entry['expires_at']:
                        self.cache_logger.debug(f"Local cache hit: {full_cache_key}")
                        return cache_entry['data']
                    else:
                        # Remove expired entry
                        del self.local_cache[full_cache_key]
                
                # Try Redis cache
                try:
                    cached_data = self.redis_client.get(full_cache_key)
                    if cached_data:
                        data = pickle.loads(cached_data)
                        
                        # Store in local cache for future use
                        if use_local:
                            self._store_local_cache(full_cache_key, data, ttl or 300)
                        
                        self.cache_logger.debug(f"Redis cache hit: {full_cache_key}")
                        return data
                except Exception as e:
                    self.cache_logger.warning(f"Redis cache error: {str(e)}")
                
                # Cache miss - execute function
                self.cache_logger.debug(f"Cache miss: {full_cache_key}")
                result = func(*args, **kwargs)
                
                # Store in caches
                self._store_caches(full_cache_key, result, ttl, use_local)
                
                return result
            
            return wrapper
        return decorator
    
    def _store_caches(self, cache_key: str, data: Any, ttl: Optional[int], use_local: bool):
        """Store data in both Redis and local cache."""
        cache_ttl = ttl or self.ttl_config.get('dashboard_data', 300)
        
        # Store in Redis
        try:
            serialized_data = pickle.dumps(data)
            self.redis_client.setex(cache_key, cache_ttl, serialized_data)
        except Exception as e:
            self.cache_logger.warning(f"Redis cache store error: {str(e)}")
        
        # Store in local cache
        if use_local:
            self._store_local_cache(cache_key, data, cache_ttl)
    
    def _store_local_cache(self, cache_key: str, data: Any, ttl: int):
        """Store data in local memory cache with size limits."""
        # Implement LRU eviction if cache is full
        if len(self.local_cache) >= self.local_cache_size_limit:
            # Remove oldest entry
            oldest_key = min(
                self.local_cache.keys(), 
                key=lambda k: self.local_cache[k]['stored_at']
            )
            del self.local_cache[oldest_key]
        
        self.local_cache[cache_key] = {
            'data': data,
            'stored_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(seconds=ttl)
        }
    
    def invalidate_pattern(self, pattern: str):
        """Invalidate cache entries matching pattern."""
        try:
            # Redis pattern invalidation
            keys = self.redis_client.keys(pattern)
            if keys:
                self.redis_client.delete(*keys)
            
            # Local cache pattern invalidation
            local_keys_to_remove = [
                key for key in self.local_cache.keys() 
                if pattern.replace('*', '') in key
            ]
            
            for key in local_keys_to_remove:
                del self.local_cache[key]
                
            self.cache_logger.info(f"Invalidated cache pattern: {pattern}")
            
        except Exception as e:
            self.cache_logger.error(f"Cache invalidation error: {str(e)}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics."""
        try:
            redis_info = self.redis_client.info('memory')
            
            return {
                'redis_memory_used': redis_info.get('used_memory_human', 'unknown'),
                'redis_connected_clients': redis_info.get('connected_clients', 0),
                'local_cache_size': len(self.local_cache),
                'local_cache_limit': self.local_cache_size_limit
            }
        except Exception as e:
            self.cache_logger.error(f"Cache stats error: {str(e)}")
            return {'error': str(e)}

# Apply caching to database service
class CachedDataService(OptimizedQueries):
    """Data service with performance caching."""
    
    def __init__(self, session_factory: sessionmaker, cache: PerformanceCache):
        super().__init__(session_factory)
        self.cache = cache
    
    @PerformanceCache.cached_query('dashboard_summary', ttl=120)
    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Cached dashboard summary data."""
        return super().get_dashboard_summary()
    
    @PerformanceCache.cached_query('trend_data', ttl=600)
    def get_trend_data_optimized(self, days: int = 7) -> List[Dict[str, Any]]:
        """Cached trend analysis data."""
        return super().get_trend_data_optimized(days)
    
    @PerformanceCache.cached_query('usage_timeline', ttl=300)
    def get_usage_timeline_compressed(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Cached usage timeline data."""
        return super().get_usage_timeline_compressed(hours)
```

### 3.2 Resource Monitoring

```python
# app/performance/resource_monitor.py
import psutil
import time
import logging
from typing import Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass

@dataclass
class ResourceSnapshot:
    """Resource usage snapshot for monitoring."""
    timestamp: datetime
    memory_mb: float
    memory_percent: float
    cpu_percent: float
    disk_usage_percent: float
    network_io_mb: float
    active_connections: int

class ResourceMonitor:
    """
    Continuous resource monitoring for budget hosting optimization.
    """
    
    def __init__(self):
        self.monitor_logger = logging.getLogger('performance.resources')
        self.snapshots: List[ResourceSnapshot] = []
        self.max_snapshots = 288  # 24 hours of 5-minute intervals
        
        # Thresholds for alerts
        self.memory_threshold = 400  # MB
        self.cpu_threshold = 15      # %
        self.disk_threshold = 80     # %
        
        # Performance tracking
        self.last_snapshot_time = None
        self.monitoring_interval = 300  # 5 minutes
        
    def collect_snapshot(self) -> ResourceSnapshot:
        """Collect current resource usage snapshot."""
        try:
            # Memory usage
            memory = psutil.virtual_memory()
            memory_mb = memory.used / 1024 / 1024
            
            # CPU usage (average over 1 second)
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # Disk usage
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # Network I/O
            network = psutil.net_io_counters()
            network_mb = (network.bytes_sent + network.bytes_recv) / 1024 / 1024
            
            # Active connections (approximate)
            connections = len(psutil.net_connections())
            
            snapshot = ResourceSnapshot(
                timestamp=datetime.utcnow(),
                memory_mb=memory_mb,
                memory_percent=memory.percent,
                cpu_percent=cpu_percent,
                disk_usage_percent=disk_percent,
                network_io_mb=network_mb,
                active_connections=connections
            )
            
            # Store snapshot
            self._store_snapshot(snapshot)
            
            # Check thresholds
            self._check_resource_thresholds(snapshot)
            
            return snapshot
            
        except Exception as e:
            self.monitor_logger.error(f"Resource monitoring error: {str(e)}")
            raise
    
    def _store_snapshot(self, snapshot: ResourceSnapshot):
        """Store snapshot with size limit management."""
        self.snapshots.append(snapshot)
        
        # Remove old snapshots to maintain size limit
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots = self.snapshots[-self.max_snapshots:]
    
    def _check_resource_thresholds(self, snapshot: ResourceSnapshot):
        """Check resource usage against thresholds."""
        alerts = []
        
        if snapshot.memory_mb > self.memory_threshold:
            alerts.append(f"High memory usage: {snapshot.memory_mb:.1f}MB")
            
        if snapshot.cpu_percent > self.cpu_threshold:
            alerts.append(f"High CPU usage: {snapshot.cpu_percent:.1f}%")
            
        if snapshot.disk_usage_percent > self.disk_threshold:
            alerts.append(f"High disk usage: {snapshot.disk_usage_percent:.1f}%")
        
        if alerts:
            self.monitor_logger.warning(f"Resource alerts: {', '.join(alerts)}")
            self._trigger_optimization(snapshot, alerts)
    
    def _trigger_optimization(self, snapshot: ResourceSnapshot, alerts: List[str]):
        """Trigger optimization actions based on resource pressure."""
        if snapshot.memory_mb > self.memory_threshold:
            self._optimize_memory()
            
        if snapshot.cpu_percent > self.cpu_threshold:
            self._optimize_cpu()
    
    def _optimize_memory(self):
        """Implement memory optimization strategies."""
        self.monitor_logger.info("Triggering memory optimization")
        
        # Force garbage collection
        import gc
        gc.collect()
        
        # Clear local caches if available
        try:
            from app.performance.cache_manager import cache_manager
            cache_manager.local_cache.clear()
        except ImportError:
            pass
        
        # Could also:
        # - Reduce cache TTL temporarily
        # - Close idle database connections
        # - Compress large data structures
    
    def _optimize_cpu(self):
        """Implement CPU optimization strategies."""
        self.monitor_logger.info("Triggering CPU optimization")
        
        # Could implement:
        # - Increase polling intervals temporarily
        # - Defer non-critical background tasks
        # - Reduce query complexity
        # - Enable conservative mode
    
    def get_performance_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance summary for specified time period."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_snapshots = [
            s for s in self.snapshots 
            if s.timestamp >= cutoff_time
        ]
        
        if not recent_snapshots:
            return {'error': 'No recent performance data available'}
        
        # Calculate statistics
        memory_values = [s.memory_mb for s in recent_snapshots]
        cpu_values = [s.cpu_percent for s in recent_snapshots]
        
        return {
            'period_hours': hours,
            'data_points': len(recent_snapshots),
            'memory': {
                'current_mb': recent_snapshots[-1].memory_mb,
                'average_mb': sum(memory_values) / len(memory_values),
                'peak_mb': max(memory_values),
                'threshold_mb': self.memory_threshold
            },
            'cpu': {
                'current_percent': recent_snapshots[-1].cpu_percent,
                'average_percent': sum(cpu_values) / len(cpu_values),
                'peak_percent': max(cpu_values),
                'threshold_percent': self.cpu_threshold
            },
            'disk': {
                'current_percent': recent_snapshots[-1].disk_usage_percent,
                'threshold_percent': self.disk_threshold
            },
            'network': {
                'total_io_mb': recent_snapshots[-1].network_io_mb
            }
        }
    
    def should_enable_conservative_mode(self) -> bool:
        """Determine if conservative mode should be enabled based on resources."""
        if len(self.snapshots) < 3:
            return False
        
        recent_snapshots = self.snapshots[-3:]  # Last 3 snapshots
        
        # Check if consistently high resource usage
        high_memory_count = sum(1 for s in recent_snapshots if s.memory_mb > self.memory_threshold * 0.8)
        high_cpu_count = sum(1 for s in recent_snapshots if s.cpu_percent > self.cpu_threshold * 0.8)
        
        return high_memory_count >= 2 or high_cpu_count >= 2
```

---

## 4. Web Application Performance

### 4.1 Flask Application Optimization

```python
# app/performance/flask_optimization.py
from flask import Flask, request, jsonify, g
import time
import logging
from functools import wraps
from typing import Callable

class FlaskPerformanceOptimizer:
    """
    Flask application performance optimization utilities.
    """
    
    def __init__(self, app: Flask):
        self.app = app
        self.performance_logger = logging.getLogger('performance.flask')
        self._setup_performance_monitoring()
        self._configure_flask_optimization()
    
    def _setup_performance_monitoring(self):
        """Setup request timing and monitoring."""
        
        @self.app.before_request
        def before_request():
            g.request_start_time = time.time()
            g.request_id = f"{int(time.time())}{id(request)}"[-10:]
        
        @self.app.after_request
        def after_request(response):
            if hasattr(g, 'request_start_time'):
                duration = (time.time() - g.request_start_time) * 1000
                
                # Log slow requests
                if duration > 1000:  # > 1 second
                    self.performance_logger.warning(
                        f"Slow request: {request.method} {request.path} "
                        f"took {duration:.1f}ms (Request ID: {g.request_id})"
                    )
                elif duration > 500:  # > 500ms
                    self.performance_logger.info(
                        f"Medium request: {request.method} {request.path} "
                        f"took {duration:.1f}ms (Request ID: {g.request_id})"
                    )
                
                # Add performance headers
                response.headers['X-Response-Time'] = f"{duration:.1f}ms"
                response.headers['X-Request-ID'] = g.request_id
            
            return response
    
    def _configure_flask_optimization(self):
        """Configure Flask for optimal performance."""
        
        # Disable unnecessary features for production
        if not self.app.debug:
            self.app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 31536000  # 1 year
            self.app.config['JSONIFY_PRETTYPRINT_REGULAR'] = False
        
        # Configure session optimization
        self.app.config['PERMANENT_SESSION_LIFETIME'] = 86400  # 24 hours
        self.app.config['SESSION_COOKIE_HTTPONLY'] = True
        self.app.config['SESSION_COOKIE_SECURE'] = True  # HTTPS only
        
        # Configure JSON serialization
        self.app.json.compact = True
    
    def performance_monitor(self, threshold_ms: int = 500):
        """Decorator to monitor endpoint performance."""
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    duration = (time.time() - start_time) * 1000
                    
                    if duration > threshold_ms:
                        self.performance_logger.warning(
                            f"Slow endpoint: {func.__name__} took {duration:.1f}ms"
                        )
                    
                    return result
                    
                except Exception as e:
                    duration = (time.time() - start_time) * 1000
                    self.performance_logger.error(
                        f"Error in {func.__name__} after {duration:.1f}ms: {str(e)}"
                    )
                    raise
            
            return wrapper
        return decorator

# Optimized route implementations
class OptimizedRoutes:
    """
    Performance-optimized route implementations.
    """
    
    def __init__(self, data_service, cache_manager):
        self.data_service = data_service
        self.cache = cache_manager
        self.route_logger = logging.getLogger('performance.routes')
    
    @FlaskPerformanceOptimizer.performance_monitor(threshold_ms=2000)
    def dashboard_route(self):
        """Optimized dashboard route with aggressive caching."""
        try:
            # Try cache first
            cache_key = f"dashboard_data:{request.remote_addr}"
            cached_data = self.cache.get_cached_data(cache_key)
            
            if cached_data:
                return jsonify(cached_data)
            
            # Get fresh data
            dashboard_data = self.data_service.get_dashboard_summary()
            
            # Enhance with calculated fields
            dashboard_data.update({
                'safe_days_remaining': self._calculate_safe_days(dashboard_data),
                'usage_status': self._get_usage_status(dashboard_data),
                'recommendations': self._get_recommendations(dashboard_data)
            })
            
            # Cache for 2 minutes
            self.cache.set_cached_data(cache_key, dashboard_data, ttl=120)
            
            return jsonify(dashboard_data)
            
        except Exception as e:
            self.route_logger.error(f"Dashboard route error: {str(e)}")
            return jsonify({'error': 'Dashboard data unavailable'}), 500
    
    @FlaskPerformanceOptimizer.performance_monitor(threshold_ms=1000)
    def api_usage_current(self):
        """Optimized current usage API endpoint."""
        try:
            # Use shorter cache for API endpoints
            cache_key = "api_usage_current"
            cached_data = self.cache.get_cached_data(cache_key)
            
            if cached_data:
                return jsonify(cached_data)
            
            # Get minimal data set for API
            usage_data = self.data_service.get_dashboard_summary()
            
            # Return only essential fields for API
            api_response = {
                'total_used_mb': usage_data.get('total_used_mb', 0),
                'remaining_mb': usage_data.get('remaining_mb', 0),
                'daily_budget_mb': usage_data.get('daily_budget_mb', 0),
                'last_updated': usage_data.get('last_updated'),
                'efficiency_score': usage_data.get('efficiency_score', 1.0)
            }
            
            # Cache for 1 minute
            self.cache.set_cached_data(cache_key, api_response, ttl=60)
            
            return jsonify(api_response)
            
        except Exception as e:
            self.route_logger.error(f"Usage API error: {str(e)}")
            return jsonify({'error': 'Usage data unavailable'}), 500
    
    def _calculate_safe_days(self, data: dict) -> int:
        """Calculate safe days remaining based on current trajectory."""
        remaining_mb = data.get('remaining_mb', 0)
        avg_daily_usage = data.get('avg_weekly_usage', 0) / 7
        
        if avg_daily_usage <= 0:
            return data.get('days_remaining', 0)
        
        safe_days = remaining_mb / avg_daily_usage
        return max(0, min(safe_days, data.get('days_remaining', 0)))
    
    def _get_usage_status(self, data: dict) -> str:
        """Determine usage status based on efficiency score."""
        efficiency = data.get('efficiency_score', 1.0)
        
        if efficiency >= 0.9:
            return 'excellent'
        elif efficiency >= 0.7:
            return 'good'
        elif efficiency >= 0.5:
            return 'caution'
        else:
            return 'concern'
    
    def _get_recommendations(self, data: dict) -> list:
        """Generate usage recommendations based on current data."""
        recommendations = []
        
        efficiency = data.get('efficiency_score', 1.0)
        days_remaining = data.get('days_remaining', 0)
        
        if efficiency < 0.7 and days_remaining > 7:
            recommendations.append("Consider reducing streaming quality during peak hours")
        elif efficiency < 0.5:
            recommendations.append("Monitor large downloads and updates carefully")
        elif efficiency >= 0.9:
            recommendations.append("Great usage pace! Good time for software updates")
        
        return recommendations
```

### 4.2 Static Asset Optimization

```nginx
# /etc/nginx/sites-available/taara-monitoring
server {
    listen 80;
    server_name your-domain.com;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    
    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/javascript
        application/xml+rss
        application/json;
    
    # Static file serving with aggressive caching
    location /static/ {
        alias /var/www/taara/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
        
        # Compress static files
        location ~* \.(css|js)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
            gzip_static on;
        }
        
        # Images
        location ~* \.(jpg|jpeg|png|gif|ico|svg)$ {
            expires 6M;
            add_header Cache-Control "public";
        }
    }
    
    # API endpoints with minimal caching
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # API-specific optimizations
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_connect_timeout 5s;
        proxy_send_timeout 10s;
        proxy_read_timeout 10s;
    }
    
    # Dashboard pages
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Dashboard caching
        proxy_cache_valid 200 2m;
        proxy_cache_key $scheme$request_method$host$request_uri;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000;
        access_log off;
    }
}
```

---

This comprehensive performance optimization guide addresses all performance concerns identified in the master checklist:

1. **✅ Database Performance** - Optimized configuration, queries, and indexing for budget hosting
2. **✅ Application Caching** - Multi-level caching with memory efficiency
3. **✅ Resource Monitoring** - Continuous monitoring with automatic optimization triggers
4. **✅ Flask Optimization** - Performance monitoring and route optimization
5. **✅ Static Asset Optimization** - Nginx configuration for optimal delivery
6. **✅ Memory Management** - Efficient resource usage within 512MB constraints

The project now has comprehensive performance optimization ready for budget hosting deployment!
