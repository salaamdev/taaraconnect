# Infrastructure Foundation Setup Guide

**CRITICAL:** This guide MUST be followed before any feature development begins.
It addresses all infrastructure sequencing issues identified in the PO Master Checklist.

## Prerequisites Validation Checklist

Before starting ANY development work, verify these prerequisites:

### ✅ System Requirements
- [ ] Ubuntu 20.04+ or compatible Linux distribution
- [ ] Python 3.11.5 installed
- [ ] PostgreSQL 15.4+ installed and running
- [ ] Git installed and configured
- [ ] Digital Ocean account setup (for staging/production)
- [ ] GitHub repository access configured

### ✅ Environment Setup
- [ ] Development machine with 4GB+ RAM
- [ ] Stable internet connection for ISP API testing
- [ ] Text editor/IDE configured for Python development
- [ ] Terminal access with sudo privileges

## Step-by-Step Infrastructure Setup

### Phase 1: Local Development Environment (MUST BE FIRST)

#### 1.1 Clone Repository and Setup Python Environment
```bash
# Clone the repository
git clone https://github.com/salaamdev/taaraconnect.git
cd taaraconnect

# Create Python virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Upgrade pip and install wheel
pip install --upgrade pip wheel
```

#### 1.2 Install Development Dependencies
```bash
# Install all development dependencies
pip install -r requirements/dev.txt
pip install -r requirements/test.txt

# Verify installation
python -c "import flask, sqlalchemy, pytest; print('Dependencies OK')"
```

#### 1.3 Setup Development Database
```bash
# Copy environment configuration
cp .env.example .env.dev

# Edit .env.dev with your local settings
# Set DATABASE_URL=sqlite:///dev.db for development
# Set SECRET_KEY to a random string

# Run database setup script
python scripts/setup_database.py --environment=dev
```

**✅ Checkpoint 1:** Verify database setup completed without errors

### Phase 2: Security Framework Setup (DEPENDS ON PHASE 1)

#### 2.1 Configure Encryption System
```bash
# Test encryption functionality
python -c "
from app.utils.encryption import encrypt_credential, decrypt_credential
test_data = 'test_credential'
encrypted = encrypt_credential(test_data)
decrypted = decrypt_credential(encrypted)
assert test_data == decrypted
print('Encryption system operational')
"
```

#### 2.2 Setup Authentication Framework
```bash
# Test authentication system
python -c "
from app.services.configuration_manager import ConfigurationManager
from app.models.user_preferences import UserPreferences
print('Authentication framework loaded successfully')
"
```

**✅ Checkpoint 2:** Verify security framework operational

### Phase 3: Testing Infrastructure Setup (DEPENDS ON PHASE 2)

#### 3.1 Start ISP API Mock Server
```bash
# In a separate terminal, start the mock server
python scripts/mock_isp_api.py --port=8080 --scenario=normal

# Verify mock server is running
curl http://localhost:8080/mock/health
```

#### 3.2 Run Infrastructure Tests
```bash
# Run unit tests to verify infrastructure
pytest tests/unit/test_infrastructure.py -v

# Run integration tests with mock API
pytest tests/integration/test_isp_integration.py -v

# Run security tests
pytest tests/security/ -v
```

**✅ Checkpoint 3:** Verify all infrastructure tests pass

### Phase 4: CI/CD Pipeline Setup (DEPENDS ON PHASE 3)

#### 4.1 Configure GitHub Actions
```bash
# Verify GitHub Actions configuration
# The .github/workflows/deploy.yml should be present
ls -la .github/workflows/deploy.yml

# Configure GitHub secrets (manual step):
# - Go to GitHub repository settings
# - Add secrets for:
#   - STAGING_SSH_KEY
#   - STAGING_HOST  
#   - STAGING_DATABASE_URL
#   - STAGING_SECRET_KEY
#   - PRODUCTION_SSH_KEY
#   - PRODUCTION_HOST
#   - PRODUCTION_DATABASE_URL
#   - PRODUCTION_SECRET_KEY
```

#### 4.2 Test Deployment Pipeline
```bash
# Create a test commit to trigger CI/CD
git add .
git commit -m "Test infrastructure setup"
git push origin main

# Monitor GitHub Actions for successful build
```

**✅ Checkpoint 4:** Verify CI/CD pipeline runs successfully

### Phase 5: Staging Environment Setup (DEPENDS ON PHASE 4)

#### 5.1 Provision Staging Infrastructure
```bash
# Install Ansible
pip install ansible==2.15.0

# Configure staging environment
cd deployment/ansible
ansible-playbook -i inventories/staging provision.yml

# Deploy application to staging
ansible-playbook -i inventories/staging deploy.yml
```

#### 5.2 Verify Staging Environment
```bash
# Test staging deployment
curl https://staging.taara-monitor.com/health
curl https://staging.taara-monitor.com/api/v1/system/health

# Run smoke tests against staging
pytest tests/smoke/ --staging-url=https://staging.taara-monitor.com
```

**✅ Checkpoint 5:** Verify staging environment operational

## Infrastructure Validation Checklist

Before declaring infrastructure foundation complete, verify:

### ✅ Database Foundation
- [ ] PostgreSQL database operational with schema created
- [ ] Migration system (Alembic) functional
- [ ] All tables created with proper constraints and indexes
- [ ] Database health checks pass
- [ ] Connection pooling configured

### ✅ Security Foundation
- [ ] AES-256 encryption system operational
- [ ] Credential management system functional
- [ ] Session management configured
- [ ] Security tests pass
- [ ] No hardcoded secrets in code

### ✅ Testing Infrastructure
- [ ] ISP API mock server operational
- [ ] Unit test framework functional
- [ ] Integration tests pass with mocked ISP API
- [ ] Security tests validate encryption
- [ ] Performance tests validate resource constraints

### ✅ CI/CD Pipeline
- [ ] GitHub Actions workflow operational
- [ ] Automated testing on pull requests
- [ ] Automated deployment to staging
- [ ] Health checks in deployment pipeline
- [ ] Rollback procedures tested

### ✅ Development Environment
- [ ] Local development setup documented
- [ ] New developer can setup in <15 minutes
- [ ] All dependencies properly specified
- [ ] Environment configuration isolated
- [ ] Debug logging functional

## Common Issues and Troubleshooting

### Database Connection Issues
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Verify database exists
psql -l | grep taara

# Test connection
python -c "from app import create_app; app = create_app(); print('DB OK')"
```

### Mock API Issues
```bash
# Check if mock server is running
ps aux | grep mock_isp_api

# Test mock API endpoints
curl -X POST http://localhost:8080/login \
  -H "Content-Type: application/json" \
  -d '{"username": "test_user", "password": "test_password"}'
```

### CI/CD Pipeline Issues
```bash
# Check GitHub Actions logs
# Go to GitHub repository → Actions tab
# Review failed workflows for specific errors

# Test Ansible playbooks locally
ansible-playbook deployment/ansible/deploy.yml --check
```

## Success Criteria

Infrastructure foundation is complete when:

1. **All checkpoints pass** without errors
2. **New developer setup time** < 15 minutes from clone to running
3. **Test suite passes** 100% on infrastructure components
4. **CI/CD pipeline** successfully deploys to staging
5. **Security validation** confirms encryption and credential management
6. **Performance tests** validate budget hosting constraints

## Next Steps

Once infrastructure foundation is complete:

1. **Epic-001 can begin** with confidence that all dependencies are met
2. **Feature development** can proceed without infrastructure blockers
3. **Database operations** can use existing schema and migration system
4. **Authentication** can use existing encryption and session management
5. **Testing** can use existing mock infrastructure and frameworks

---

**CRITICAL REMINDER:** Do NOT start Epic-001 or any feature development until ALL infrastructure foundation checkpoints pass. This prevents the sequencing issues identified in the PO Master Checklist and ensures secure, reliable development.
