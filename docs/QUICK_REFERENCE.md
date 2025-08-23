# Taara Internet Monitor - Quick Reference

## 🚀 Quick Start

### For End Users
1. **Access Dashboard**: http://localhost:8000
2. **Check Current Balance**: Look at the top-left number
3. **Check Days Remaining**: Top-right number
4. **Monitor Usage**: Review the charts below

### For Administrators
```bash
# Check system status
docker-compose ps
curl http://localhost:8000/api/data

# View logs
docker-compose logs -f app
docker-compose logs -f scheduler

# Restart services
docker-compose restart
```

---

## 📊 Dashboard Interpretation

### Status Indicators
| Display | Meaning | Action |
|---------|---------|--------|
| 900+ GB remaining | 🟢 Excellent | Normal usage |
| 500-900 GB remaining | 🟡 Good | Monitor usage |
| 100-500 GB remaining | 🟠 Caution | Reduce heavy usage |
| <100 GB remaining | 🔴 Critical | Minimize usage |

### Daily Usage Rates
| Usage Rate | Assessment | Recommendation |
|------------|------------|----------------|
| 0-5 GB/day | Very light | Safe to increase |
| 5-15 GB/day | Light | Good pace |
| 15-25 GB/day | Moderate | Monitor closely |
| 25+ GB/day | Heavy | Consider reducing |

---

## 🔧 Common Tasks

### User Tasks
- **Check current usage**: Refresh dashboard
- **Plan downloads**: Check balance and daily rate
- **Monitor trends**: Review usage charts
- **Report issues**: Contact system administrator

### Administrator Tasks

#### Daily Maintenance
```bash
# Health check
curl http://localhost:8000/api/data
docker-compose ps

# Check logs for errors
docker-compose logs --tail 50 app | grep -i error

# Verify data collection
sqlite3 taara_monitoring.db "SELECT timestamp FROM data_usage_records ORDER BY timestamp DESC LIMIT 1;"
```

#### Weekly Maintenance
```bash
# Backup database
cp taara_monitoring.db backups/taara_$(date +%Y%m%d).db

# Update system
git pull
docker-compose down
docker-compose up -d --build

# Clean old logs
find logs/ -name "*.log" -mtime +30 -delete
```

#### Monthly Maintenance
```bash
# Database optimization
sqlite3 taara_monitoring.db "VACUUM;"

# System update
sudo apt update && sudo apt upgrade

# Security audit
sudo ss -tulpn | grep :8000  # Should show no external access
```

---

## 🆘 Emergency Procedures

### System Down
1. **Check if services are running**:
   ```bash
   docker-compose ps
   # or
   sudo systemctl status taara-web taara-scheduler
   ```

2. **Restart services**:
   ```bash
   docker-compose restart
   # or
   sudo systemctl restart taara-web taara-scheduler
   ```

3. **Check for errors**:
   ```bash
   docker-compose logs --tail 100
   ```

### Database Issues
1. **Backup current database**:
   ```bash
   cp taara_monitoring.db taara_monitoring_backup_$(date +%Y%m%d).db
   ```

2. **Test database integrity**:
   ```bash
   sqlite3 taara_monitoring.db "PRAGMA integrity_check;"
   ```

3. **Restore from backup if needed**:
   ```bash
   cp backups/taara_YYYYMMDD.db taara_monitoring.db
   docker-compose restart
   ```

### API Connection Issues
1. **Test API manually**:
   ```bash
   python test_api.py
   ```

2. **Check credentials**:
   ```bash
   cat .env | grep TAARA
   ```

3. **Verify network connectivity**:
   ```bash
   ping api.taara.co.ke
   curl -I https://api.taara.co.ke/
   ```

---

## 📞 Support Contacts

### Internal Support
- **System Administrator**: [Your admin contact]
- **Technical Issues**: Check logs first, then contact admin
- **User Questions**: Refer to User Guide

### External Support
- **Taara ISP Support**: [Taara contact information]
- **Account Issues**: Contact Taara directly
- **Service Outages**: Check Taara status page

---

## 📋 System Information

### Current System Status
```bash
# Quick system check script
#!/bin/bash
echo "=== Taara Monitor Status ==="
echo "Time: $(date)"
echo "Services: $(docker-compose ps --services)"
echo "Web Status: $(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/data)"
echo "Database Records: $(sqlite3 taara_monitoring.db "SELECT COUNT(*) FROM data_usage_records;")"
echo "Last Update: $(sqlite3 taara_monitoring.db "SELECT timestamp FROM data_usage_records ORDER BY timestamp DESC LIMIT 1;")"
echo "Disk Usage: $(df -h / | tail -1 | awk '{print $5}')"
echo "============================"
```

### Performance Benchmarks
- **Dashboard Load Time**: <1 second
- **API Response Time**: <0.1 seconds
- **Data Collection Interval**: 10-15 minutes
- **Database Query Time**: <0.01 seconds

### Resource Requirements
- **RAM Usage**: ~100MB
- **Disk Space**: ~50MB (grows with historical data)
- **CPU Usage**: <5% during normal operation
- **Network**: Minimal (API calls only)

---

## 🔗 Quick Links

### Documentation
- [User Guide](USER_GUIDE.md) - For end users
- [Developer Guide](DEVELOPER_GUIDE.md) - For developers
- [Admin Guide](SYSTEM_ADMIN_GUIDE.md) - For administrators
- [Testing Report](TESTING_REPORT.md) - Test results

### System URLs
- **Dashboard**: http://localhost:8000
- **API Data**: http://localhost:8000/api/data
- **API Stats**: http://localhost:8000/api/stats
- **API History**: http://localhost:8000/api/history

### Important Files
- **Configuration**: `.env`
- **Database**: `taara_monitoring.db`
- **Logs**: `taara_scheduler.log`
- **Backup Location**: `backups/`

---

## 🎯 Best Practices

### For Users
- ✅ Check dashboard daily
- ✅ Plan heavy downloads when balance is high
- ✅ Monitor trends, not just current numbers
- ✅ Bookmark the dashboard for easy access

### For Administrators
- ✅ Run health checks daily
- ✅ Backup database weekly
- ✅ Monitor logs for errors
- ✅ Keep system updated
- ✅ Document any configuration changes

### Security
- ✅ Secure .env file permissions (600)
- ✅ Use HTTPS in production
- ✅ Regular security updates
- ✅ Monitor access logs
- ✅ Backup encryption for sensitive data

---

**Need more help?** Refer to the comprehensive documentation or contact your system administrator.
