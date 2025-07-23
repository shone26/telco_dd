# Complete Datadog APM Setup and Error Testing Guide

## Problem Summary
You were experiencing "0 APM services across 0 applications" and "env:none" in Datadog, indicating that:
1. No APM traces were being collected
2. Environment tags were not properly set
3. Services were not appearing in the service map

## Root Cause Analysis
The main issues were:
1. **Environment Variables Not Loaded**: Backend and frontend services weren't loading `.env.datadog`
2. **Site Configuration Mismatch**: Different Datadog sites in different config files
3. **Missing Environment Tags**: Services weren't getting proper environment labels
4. **Incomplete APM Configuration**: Limited trace sampling and analytics

## Complete Fix Applied

### 1. Updated Docker Compose Configuration
**File**: `docker-compose.yml`

Added `env_file: - .env.datadog` to all services:
```yaml
# Datadog Agent
datadog-agent:
  env_file:
    - .env.datadog
  environment:
    - DD_SITE=${DD_SITE:-ap1.datadoghq.com}
    - DD_ENV=${DD_ENV:-production}
    - DD_VERSION=${DD_VERSION:-1.0.0}

# Backend Service  
backend:
  env_file:
    - .env.datadog
  environment:
    - DD_ENV=${DD_ENV:-production}
    - DD_VERSION=${DD_VERSION:-1.0.0}

# Frontend Service
frontend:
  env_file:
    - .env.datadog
  environment:
    - DD_ENV=${DD_ENV:-production}
    - DD_VERSION=${DD_VERSION:-1.0.0}
```

### 2. Fixed Datadog Agent Configuration
**File**: `datadog/datadog.yaml`

Updated site configuration and enhanced APM settings:
```yaml
site: ap1.datadoghq.com

apm_config:
  enabled: true
  env: production
  receiver_port: 8126
  apm_non_local_traffic: true
  max_traces_per_second: 50
  analyzed_rate_by_service:
    telecom-backend|*: 1.0
    telecom-frontend|*: 1.0
  max_events_per_second: 200
  max_memory: 500000000
  max_cpu_percent: 50
```

### 3. Enhanced Backend Tracing
**File**: `backend/datadog_config.py`

Added advanced tracing configuration:
```python
config.trace.enabled = True
config.trace.analytics_enabled = True
config.trace.analytics_sample_rate = 1.0

# Service-specific naming
config.sqlalchemy['service_name'] = f"{dd_service_name}-db"
config.requests['service_name'] = f"{dd_service_name}-http"
```

### 4. Enhanced Frontend Tracing
**File**: `frontend/datadog_config.js`

Added proper analytics and tags:
```javascript
tracer.init({
    service: ddServiceName,
    env: ddEnv,
    version: ddVersion,
    hostname: ddAgentHost,
    port: ddTraceAgentPort,
    logInjection: true,
    analytics: true,
    analyticsSampleRate: 1.0,
    runtimeMetrics: true,
    plugins: true,
    tags: {
        service: ddServiceName,
        env: ddEnv,
        version: ddVersion
    }
});
```

## How to Apply the Fix

### Step 1: Restart Services with Fixed Configuration
```bash
cd TC/telecomTemp
./restart_and_test_datadog.sh
```

This script will:
- ✅ Validate your Datadog configuration
- ✅ Stop and clean up existing containers
- ✅ Rebuild services with updated configuration
- ✅ Start services and wait for them to be healthy
- ✅ Test APM and DogStatsD connectivity
- ✅ Generate initial traffic to create traces
- ✅ Check environment variables in containers
- ✅ Provide diagnostic information

### Step 2: Generate Errors for Testing (Optional)
```bash
cd TC/telecomTemp
python3 generate_errors_for_datadog.py
```

This script will generate:
- 🔐 Authentication errors (401, 403)
- 🗄️ Database errors (404 for non-existent resources)
- ✅ Validation errors (400 for invalid data)
- 🌐 Network errors (404 for non-existent endpoints)
- 🖥️ Frontend errors (404 pages)
- ⚡ Load-related errors (timeouts)

## Expected Results

### In Datadog APM (5-10 minutes after restart)

**Services List**: https://app.datadoghq.com/apm/services
- ✅ `telecom-backend` (env: production)
- ✅ `telecom-frontend` (env: production)
- ✅ `telecom-backend-db` (database operations)
- ✅ `telecom-backend-http` (HTTP requests)

**Service Map**: https://app.datadoghq.com/apm/map
- ✅ Visual representation of service dependencies
- ✅ Request flow between frontend ↔ backend
- ✅ Database connections
- ✅ Environment should show "production" (not "none")

**Error Tracking**: https://app.datadoghq.com/apm/error-tracking
- ✅ Authentication errors
- ✅ Database lookup errors
- ✅ Validation errors
- ✅ Network/routing errors
- ✅ Load-related errors

## Verification Commands

### Check Service Status
```bash
# Check all containers
docker-compose -f docker-compose.yml -f docker-compose.datadog.yml ps

# Check Datadog agent status
docker exec telecom_datadog_agent datadog-agent status

# Check APM specifically
docker exec telecom_datadog_agent datadog-agent status apm
```

### Check Environment Variables
```bash
# Backend environment
docker exec telecom_backend printenv | grep DD_

# Frontend environment  
docker exec telecom_frontend printenv | grep DD_

# Agent environment
docker exec telecom_datadog_agent printenv | grep DD_
```

### Check Logs
```bash
# Agent logs
docker logs telecom_datadog_agent | grep -i apm

# Backend Datadog initialization
docker logs telecom_backend | grep -i datadog

# Frontend Datadog initialization
docker logs telecom_frontend | grep -i datadog
```

### Test Connectivity
```bash
# Test APM endpoint
curl -X POST http://localhost:8127/v0.4/traces \
  -H "Content-Type: application/msgpack" -d '[]'

# Test DogStatsD
echo "custom.test.metric:1|c" | nc -u localhost 8124

# Test application endpoints
curl http://localhost:5003/api/health/
curl http://localhost:3002/
```

## Troubleshooting

### Issue: Services Still Not Appearing
**Solutions:**
1. Check agent logs: `docker logs telecom_datadog_agent`
2. Verify API key in `.env.datadog`
3. Ensure site matches your Datadog account region
4. Generate more traffic: `python3 generate_errors_for_datadog.py`
5. Wait longer (up to 15 minutes for first traces)

### Issue: Environment Shows "none"
**Solutions:**
1. Verify `.env.datadog` has `DD_ENV=production`
2. Check environment variables in containers
3. Restart services: `./restart_and_test_datadog.sh`

### Issue: Partial Traces
**Solutions:**
1. Check both backend and frontend are instrumented
2. Verify `patch_all()` is called in backend
3. Confirm tracer initialization in frontend

### Issue: No Errors in Error Tracking
**Solutions:**
1. Run error generation: `python3 generate_errors_for_datadog.py`
2. Check application logs for actual errors
3. Verify error tracking is enabled in Datadog

## Files Created/Modified

### New Scripts
- `restart_and_test_datadog.sh` - Complete restart and testing script
- `generate_errors_for_datadog.py` - Error generation for testing
- `DATADOG_COMPLETE_GUIDE.md` - This comprehensive guide

### Modified Configuration Files
- `docker-compose.yml` - Added env_file loading
- `datadog/datadog.yaml` - Fixed site and enhanced APM config
- `backend/datadog_config.py` - Enhanced tracing configuration
- `frontend/datadog_config.js` - Improved tracer initialization

## Quick Start Commands

```bash
# Navigate to project directory
cd TC/telecomTemp

# Fix and restart everything
./restart_and_test_datadog.sh

# Wait 5-10 minutes, then check Datadog APM dashboard

# Generate test errors (optional)
python3 generate_errors_for_datadog.py

# Manual verification
docker exec telecom_datadog_agent datadog-agent status apm
```

## Support Resources

- **Datadog APM Documentation**: https://docs.datadoghq.com/tracing/
- **Python APM Setup**: https://docs.datadoghq.com/tracing/setup/python/
- **Node.js APM Setup**: https://docs.datadoghq.com/tracing/setup/nodejs/
- **Error Tracking**: https://docs.datadoghq.com/tracing/error_tracking/
- **Service Map**: https://docs.datadoghq.com/tracing/visualization/services_map/

## Success Indicators

After following this guide, you should see:
- ✅ Services appearing in APM with correct environment tags
- ✅ Traces flowing between frontend and backend
- ✅ Database operations being tracked
- ✅ Errors being captured and categorized
- ✅ Service map showing application architecture
- ✅ Performance metrics and alerts working

The key fix was ensuring environment variables are properly loaded from `.env.datadog` into all services, which resolves both the "0 APM services" and "env:none" issues.
