# Datadog Monitoring Setup Guide

This guide explains how to set up Datadog monitoring for the Telecom application to track traces, metrics, and logs.

## Overview

The Datadog integration includes:
- **APM (Application Performance Monitoring)** for both backend (Python/Flask) and frontend (Node.js/Express)
- **Custom metrics** collection via StatsD
- **Log aggregation** from all containers
- **Infrastructure monitoring** for PostgreSQL, Redis, and Nginx
- **Container monitoring** for Docker services

## Prerequisites

1. **Datadog Account**: Sign up at [https://www.datadoghq.com/](https://www.datadoghq.com/)
2. **API Key**: Get your API key from [Datadog Organization Settings](https://app.datadoghq.com/organization-settings/api-keys)
3. **Application Key** (optional): Get from [Application Keys](https://app.datadoghq.com/organization-settings/application-keys)

## Setup Instructions

### 1. Configure Environment Variables

Copy the Datadog environment template:
```bash
cp .env.datadog .env.local
```

Edit `.env.local` and add your Datadog credentials:
```bash
# Required
DD_API_KEY=your_actual_datadog_api_key_here

# Optional but recommended
DD_APP_KEY=your_actual_datadog_app_key_here

# Site configuration (default: datadoghq.com)
DD_SITE=datadoghq.com  # or datadoghq.eu for EU

# Environment
DD_ENV=production  # or staging, development
```

### 2. Start the Application with Datadog

Start all services including the Datadog agent:
```bash
# Load environment variables and start services
export $(cat .env.local | xargs) && docker-compose up -d
```

Or create a `.env` file in the project root with your Datadog configuration and run:
```bash
docker-compose up -d
```

### 3. Verify Datadog Integration

Check that the Datadog agent is running:
```bash
docker-compose logs datadog-agent
```

Check backend Datadog initialization:
```bash
docker-compose logs backend | grep -i datadog
```

Check frontend Datadog initialization:
```bash
docker-compose logs frontend | grep -i datadog
```

## What Gets Monitored

### Application Performance Monitoring (APM)

**Backend (telecom-backend service):**
- Flask request/response traces
- Database query performance
- API endpoint performance
- Error tracking and stack traces

**Frontend (telecom-frontend service):**
- Express.js request/response traces
- Route performance
- External API call traces (to backend)
- Error tracking

### Custom Metrics

**Backend metrics:**
- Request counts by endpoint
- Response times
- Database connection pool stats
- Custom business metrics

**Frontend metrics:**
- Page load times
- User session metrics
- API call success/failure rates
- Custom user interaction metrics

### Infrastructure Monitoring

**Database (PostgreSQL):**
- Connection counts
- Query performance
- Lock statistics
- Database size and growth

**Cache (Redis):**
- Memory usage
- Hit/miss ratios
- Connection counts
- Command statistics

**Reverse Proxy (Nginx):**
- Request rates
- Response codes
- Upstream server health
- Connection statistics

### Log Aggregation

All container logs are automatically collected and sent to Datadog with:
- Structured log parsing
- Automatic service tagging
- Error log highlighting
- Log correlation with traces

## Datadog Dashboard Access

Once configured, you can access your monitoring data at:

1. **APM Dashboard**: [https://app.datadoghq.com/apm/services](https://app.datadoghq.com/apm/services)
2. **Infrastructure**: [https://app.datadoghq.com/infrastructure](https://app.datadoghq.com/infrastructure)
3. **Logs**: [https://app.datadoghq.com/logs](https://app.datadoghq.com/logs)
4. **Metrics**: [https://app.datadoghq.com/metric/explorer](https://app.datadoghq.com/metric/explorer)

## Service Names in Datadog

The following service names will appear in your Datadog dashboard:
- `telecom-backend` - Python Flask backend
- `telecom-frontend` - Node.js Express frontend
- `telecom-app` - Overall application (agent level)

## Custom Metrics Examples

### Backend (Python)
```python
from datadog_config import increment_counter, send_custom_metric, record_histogram

# Count user logins
increment_counter('user.login.count', tags=['method:password'])

# Track plan subscription revenue
send_custom_metric('business.revenue', plan_price, tags=['plan:premium'])

# Monitor API response times
record_histogram('api.response_time', response_time_ms, tags=['endpoint:/api/plans'])
```

### Frontend (Node.js)
```javascript
const { incrementCounter, sendCustomMetric, recordTiming } = require('./datadog_config');

// Track page views
incrementCounter(statsClient, 'page.views', { page: 'dashboard' });

// Monitor external API calls
recordTiming(statsClient, 'api.call.duration', duration, { 
    endpoint: '/api/users/dashboard' 
});
```

## Troubleshooting

### Common Issues

1. **Agent not starting:**
   ```bash
   # Check agent logs
   docker-compose logs datadog-agent
   
   # Verify API key is set
   docker-compose exec datadog-agent agent status
   ```

2. **No traces appearing:**
   - Verify services are configured with correct DD_AGENT_HOST
   - Check that port 8126 is accessible between containers
   - Ensure ddtrace/dd-trace packages are installed

3. **Missing metrics:**
   - Verify DogStatsD port 8125 is accessible
   - Check StatsD client configuration
   - Look for metric sending errors in application logs

4. **Log collection issues:**
   - Ensure DD_LOGS_ENABLED=true in agent configuration
   - Check container log driver compatibility
   - Verify log processing rules in datadog.yaml

### Debug Commands

```bash
# Check Datadog agent status
docker-compose exec datadog-agent agent status

# View agent configuration
docker-compose exec datadog-agent agent config

# Test connectivity
docker-compose exec datadog-agent agent check connectivity

# View trace agent status
docker-compose exec datadog-agent agent status | grep -A 10 "Trace Agent"
```

## Configuration Files

- `datadog/datadog.yaml` - Main Datadog agent configuration
- `backend/datadog_config.py` - Python/Flask APM configuration
- `frontend/datadog_config.js` - Node.js/Express APM configuration
- `.env.datadog` - Environment variables template
- `docker-compose.yml` - Service configuration with Datadog integration

## Security Notes

- Never commit your actual API keys to version control
- Use environment variables or Docker secrets for production
- Consider using IAM roles in cloud environments
- Regularly rotate your API keys

## Performance Impact

The Datadog integration has minimal performance impact:
- APM tracing: ~1-3% CPU overhead
- Metrics collection: ~1% CPU overhead
- Log shipping: Depends on log volume
- Agent: ~50-100MB memory usage

## Support

For issues with this integration:
1. Check the troubleshooting section above
2. Review Datadog documentation: [https://docs.datadoghq.com/](https://docs.datadoghq.com/)
3. Contact Datadog support if you have a paid plan
