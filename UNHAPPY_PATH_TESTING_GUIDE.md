# Advanced Unhappy Path Testing with Datadog Integration

## Overview

This comprehensive unhappy path testing framework is designed to test the resilience, security, and reliability of the telecom application under various failure conditions. The framework integrates with Datadog for real-time monitoring and observability of test results.

## 🎯 What Are Unhappy Paths?

Unhappy paths are scenarios where things go wrong in your application:
- **System failures** (services down, network issues)
- **Security attacks** (brute force, injection attempts)
- **Resource exhaustion** (memory, CPU, database connections)
- **Data corruption** (malformed inputs, invalid data)
- **Business logic edge cases** (race conditions, timing issues)
- **Chaos scenarios** (random failures, performance degradation)

## 🚀 Features

### Test Categories

1. **💳 Payment Cascade Failures**
   - Payment gateway timeouts
   - Validation service failures
   - Fraud detection overload
   - Retry storm scenarios

2. **🔐 Authentication Attack Scenarios**
   - Brute force attacks
   - Credential stuffing
   - Session hijacking attempts
   - Rate limiting validation

3. **🗄️ Data Corruption Scenarios**
   - Malformed JSON payloads
   - SQL injection attempts
   - XSS injection attempts
   - Input validation testing

4. **⚡ Resource Exhaustion Scenarios**
   - Memory pressure testing
   - Database connection pool exhaustion
   - CPU intensive operations
   - Concurrent request handling

5. **📱 Business Logic Edge Cases**
   - Rapid plan switching conflicts
   - Payment timing issues
   - Quota boundary conditions
   - Concurrent user operations

6. **🌪️ Chaos Engineering Scenarios**
   - Random service failures
   - Network partitions
   - Gradual performance degradation
   - System resilience testing

### Datadog Integration

- **Real-time metrics** tracking test execution and results
- **Custom dashboards** for monitoring unhappy path scenarios
- **Alerting** on test failures and system issues
- **Trace analysis** for understanding failure patterns
- **Performance monitoring** during stress conditions

## 📋 Prerequisites

### System Requirements
- Python 3.7+
- Docker and Docker Compose
- Datadog Agent running
- Backend and Frontend services running

### Python Dependencies
```bash
pip install datadog requests
```

### Environment Setup
Ensure your `.env.datadog` file contains:
```bash
DD_API_KEY=your_datadog_api_key
DD_APP_KEY=your_datadog_app_key
DD_SITE=ap1.datadoghq.com
DD_ENV=production
DD_VERSION=1.0.0
```

## 🛠️ Installation and Setup

### 1. Quick Setup
```bash
# Navigate to project directory
cd TC/telecomTemp

# Setup test environment
./run_unhappy_path_tests.sh --setup-only

# Show dashboard instructions
./run_unhappy_path_tests.sh --dashboard-only
```

### 2. Start Services
```bash
# Start all services with Datadog
docker-compose -f docker-compose.yml -f docker-compose.datadog.yml up -d

# Verify services are running
curl http://localhost:5000/api/health/
curl http://localhost:3002/
curl http://localhost:8126/info
```

### 3. Import Datadog Dashboard
```bash
# Option 1: Manual import via Datadog UI
# - Go to Datadog > Dashboards > New Dashboard
# - Import JSON file: datadog_unhappy_path_dashboard.json

# Option 2: API import
curl -X POST "https://api.datadoghq.com/api/v1/dashboard" \
  -H "Content-Type: application/json" \
  -H "DD-API-KEY: ${DD_API_KEY}" \
  -H "DD-APPLICATION-KEY: ${DD_APP_KEY}" \
  -d @datadog_unhappy_path_dashboard.json
```

## 🏃 Running Tests

### Basic Usage

```bash
# Run all unhappy path tests
./run_unhappy_path_tests.sh

# Run specific test category
./run_unhappy_path_tests.sh --category payment

# Run with custom settings
./run_unhappy_path_tests.sh --category all --duration 600 --concurrent-users 20
```

### Advanced Usage

```bash
# Run payment cascade failure tests
./run_unhappy_path_tests.sh --category payment --duration 300

# Run authentication attack scenarios
./run_unhappy_path_tests.sh --category auth --concurrent-users 15

# Run data corruption tests
./run_unhappy_path_tests.sh --category corruption

# Run resource exhaustion tests
./run_unhappy_path_tests.sh --category exhaustion --duration 180

# Run business logic edge cases
./run_unhappy_path_tests.sh --category business

# Run chaos engineering scenarios
./run_unhappy_path_tests.sh --category chaos --duration 900
```

### Command Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--category` | Test category (payment, auth, corruption, exhaustion, business, chaos, all) | all |
| `--backend-url` | Backend service URL | http://127.0.0.1:5000 |
| `--frontend-url` | Frontend service URL | http://127.0.0.1:3002 |
| `--duration` | Test duration in seconds | 300 |
| `--concurrent-users` | Number of concurrent users | 10 |
| `--setup-only` | Only setup environment, don't run tests | false |
| `--dashboard-only` | Show dashboard instructions only | false |
| `--help` | Show help message | false |

## 📊 Monitoring and Observability

### Datadog Metrics

The framework sends the following metrics to Datadog:

#### Test Suite Metrics
- `telecom.unhappy_path.test_suite.started` - Test suite executions
- `telecom.unhappy_path.test_suite.completed` - Completed test suites
- `telecom.unhappy_path.test_suite.success_rate` - Overall success rate
- `telecom.unhappy_path.test_suite.duration` - Test suite duration
- `telecom.unhappy_path.test_suite.total_tests` - Total number of tests

#### Payment Metrics
- `telecom.unhappy_path.payment_attempt` - Payment attempts by scenario
- `telecom.unhappy_path.payment_timeout` - Payment timeouts
- `telecom.unhappy_path.payment_success_rate` - Payment success rate
- `telecom.unhappy_path.payment_response_time` - Payment response times

#### Authentication Metrics
- `telecom.unhappy_path.auth_attempt` - Authentication attempts by attack type
- `telecom.unhappy_path.auth_block_rate` - Attack blocking rate
- `telecom.unhappy_path.auth_success_rate` - Authentication success rate
- `telecom.unhappy_path.auth_response_time` - Authentication response times

#### Data Corruption Metrics
- `telecom.unhappy_path.corruption_attempt` - Corruption attempts
- `telecom.unhappy_path.corruption_blocked` - Blocked corruption attempts
- `telecom.unhappy_path.corruption_protection_rate` - Protection effectiveness

#### Resource Exhaustion Metrics
- `telecom.unhappy_path.resource_pressure` - Resource pressure events
- `telecom.unhappy_path.exhaustion_success_rate` - Success rate under pressure
- `telecom.unhappy_path.exhaustion_avg_response_time` - Average response time
- `telecom.unhappy_path.resource_response_time` - Resource response times

#### Business Logic Metrics
- `telecom.unhappy_path.business_logic.started` - Business logic tests started
- `telecom.unhappy_path.business_logic.completed` - Business logic tests completed
- `telecom.unhappy_path.business_logic.error` - Business logic errors

#### Chaos Engineering Metrics
- `telecom.unhappy_path.chaos_operation` - Chaos operations
- `telecom.unhappy_path.chaos_success_rate` - Success rate during chaos
- `telecom.unhappy_path.chaos_engineering.started` - Chaos scenarios started
- `telecom.unhappy_path.chaos_engineering.error` - Chaos scenario errors

### Dashboard Widgets

The Datadog dashboard includes:

1. **Test Suite Overview**
   - Test executions over time
   - Overall success rate
   - Total tests run

2. **Payment Failures**
   - Payment attempts by scenario and status
   - Payment response time trends

3. **Authentication Security**
   - Attack attempts by type
   - Blocking effectiveness
   - Response time heatmap

4. **Data Protection**
   - Corruption attempts and handling
   - Protection rate metrics

5. **Resource Management**
   - Resource pressure events
   - Response time under load
   - Success rate during exhaustion

6. **Business Logic**
   - Edge case test results
   - Business rule violations

7. **Chaos Engineering**
   - Operations during chaos
   - System resilience metrics

8. **Error Logs**
   - Real-time error log stream
   - Service-specific error tracking

## 🔍 Test Results and Reporting

### Automated Reports

After each test run, the framework generates:

1. **JSON Report** (`tests/advanced_unhappy_path_report.json`)
   - Detailed test results
   - Performance metrics
   - Error details
   - Timing information

2. **Summary Report** (`test_reports/unhappy_path_summary_YYYYMMDD_HHMMSS.md`)
   - Executive summary
   - Test category results
   - Datadog metrics overview
   - Recommendations

3. **Log Files** (`unhappy_path_tests.log`)
   - Complete test execution logs
   - Debug information
   - Error traces

### Interpreting Results

#### Success Criteria
- **Overall Success Rate**: ≥70% (allows for expected failures in unhappy path testing)
- **Payment Tests**: Some failures expected (testing failure scenarios)
- **Auth Tests**: High blocking rate for attacks (≥80%)
- **Corruption Tests**: 100% protection rate expected
- **Resource Tests**: Graceful degradation under pressure
- **Business Logic**: Consistent rule enforcement
- **Chaos Tests**: System continues functioning (≥50% success)

#### Key Metrics to Monitor
- Response time degradation under stress
- Error rate patterns
- Resource utilization during tests
- Recovery time after failures
- Security blocking effectiveness

## 🚨 Alerting and Monitoring

### Recommended Alerts

1. **Critical Alerts**
   ```
   Alert: Unhappy Path Success Rate < 50%
   Metric: avg:telecom.unhappy_path.test_suite.success_rate{*}
   Threshold: < 50
   ```

2. **Security Alerts**
   ```
   Alert: Authentication Attack Block Rate < 80%
   Metric: avg:telecom.unhappy_path.auth_block_rate{*}
   Threshold: < 80
   ```

3. **Performance Alerts**
   ```
   Alert: Resource Exhaustion Response Time > 5000ms
   Metric: avg:telecom.unhappy_path.exhaustion_avg_response_time{*}
   Threshold: > 5000
   ```

4. **Business Logic Alerts**
   ```
   Alert: Business Logic Test Failures
   Metric: sum:telecom.unhappy_path.business_logic.error{*}
   Threshold: > 0
   ```

### Monitoring Best Practices

1. **Regular Testing**
   - Run unhappy path tests daily
   - Include in CI/CD pipeline
   - Monitor trends over time

2. **Baseline Establishment**
   - Establish performance baselines
   - Track degradation over time
   - Set appropriate thresholds

3. **Incident Response**
   - Define escalation procedures
   - Create runbooks for common failures
   - Integrate with incident management

## 🔧 Customization and Extension

### Adding New Test Scenarios

1. **Create New Test Method**
   ```python
   def test_new_scenario(self):
       """Test new unhappy path scenario"""
       print("\n🎯 Testing New Scenario...")
       
       # Send start metric
       statsd.increment(
           f'{self.dd_prefix}.new_scenario.started',
           tags=self.dd_tags
       )
       
       # Implement test logic
       # ...
       
       # Send results
       statsd.gauge(
           f'{self.dd_prefix}.new_scenario.success_rate',
           success_rate,
           tags=self.dd_tags
       )
   ```

2. **Add to Test Runner**
   ```python
   def run_all_advanced_tests(self):
       # ... existing tests ...
       self.test_new_scenario()
   ```

3. **Update Dashboard**
   - Add new widgets for the scenario
   - Include relevant metrics
   - Update dashboard JSON

### Custom Metrics

```python
# Counter metric
statsd.increment('telecom.unhappy_path.custom.counter', tags=['custom:tag'])

# Gauge metric
statsd.gauge('telecom.unhappy_path.custom.gauge', value, tags=['custom:tag'])

# Histogram metric
statsd.histogram('telecom.unhappy_path.custom.histogram', value, tags=['custom:tag'])

# Timing metric
statsd.timing('telecom.unhappy_path.custom.timing', duration_ms, tags=['custom:tag'])
```

## 🐛 Troubleshooting

### Common Issues

1. **Services Not Running**
   ```bash
   # Check service status
   docker-compose ps
   
   # Restart services
   docker-compose restart
   
   # Check logs
   docker-compose logs backend
   docker-compose logs frontend
   ```

2. **Datadog Agent Issues**
   ```bash
   # Check agent status
   docker exec telecom_datadog_agent datadog-agent status
   
   # Check APM status
   docker exec telecom_datadog_agent datadog-agent status apm
   
   # Restart agent
   docker-compose restart datadog-agent
   ```

3. **Test Failures**
   ```bash
   # Check test logs
   cat unhappy_path_tests.log
   
   # Run specific category
   ./run_unhappy_path_tests.sh --category payment
   
   # Check service health
   curl http://localhost:5000/api/health/detailed
   ```

4. **Missing Metrics in Datadog**
   ```bash
   # Verify environment variables
   docker exec telecom_backend printenv | grep DD_
   
   # Check agent connectivity
   curl -X POST http://localhost:8125 -d "test.metric:1|c"
   
   # Verify API key
   echo $DD_API_KEY
   ```

### Debug Mode

Enable debug logging by setting environment variable:
```bash
export DEBUG=1
./run_unhappy_path_tests.sh --category payment
```

## 📚 Best Practices

### Test Design
1. **Realistic Scenarios** - Base tests on real-world failure patterns
2. **Gradual Escalation** - Start with simple failures, escalate to complex
3. **Measurable Outcomes** - Define clear success/failure criteria
4. **Repeatable Tests** - Ensure tests can be run consistently

### Monitoring
1. **Baseline First** - Establish normal behavior baselines
2. **Trend Analysis** - Monitor trends over time, not just point-in-time
3. **Context Matters** - Consider business context when setting thresholds
4. **Actionable Alerts** - Only alert on actionable conditions

### Maintenance
1. **Regular Updates** - Keep test scenarios current with system changes
2. **Metric Cleanup** - Remove obsolete metrics and dashboards
3. **Documentation** - Keep documentation updated with changes
4. **Review Results** - Regularly review and act on test results

## 🤝 Contributing

To contribute new test scenarios or improvements:

1. **Fork the repository**
2. **Create feature branch**
3. **Add new test scenarios** following existing patterns
4. **Update documentation**
5. **Test thoroughly**
6. **Submit pull request**

### Code Style
- Follow existing Python code style
- Add comprehensive docstrings
- Include error handling
- Add appropriate Datadog metrics
- Update dashboard configuration

## 📞 Support

For issues or questions:

1. **Check logs** first (`unhappy_path_tests.log`)
2. **Review Datadog dashboard** for system health
3. **Check existing documentation**
4. **Create issue** with detailed information

## 🔗 Related Documentation

- [DATADOG_COMPLETE_GUIDE.md](./DATADOG_COMPLETE_GUIDE.md) - Datadog setup and configuration
- [README.md](./README.md) - General project documentation
- [ARCHITECTURE.md](./ARCHITECTURE.md) - System architecture overview

---

**Happy Testing! 🚀**

Remember: The goal of unhappy path testing is not to break your system, but to understand how it behaves under stress and ensure it fails gracefully when things go wrong.
