"""
Datadog configuration for the telecom backend application
"""
import os
from ddtrace import config, patch_all
from datadog import initialize, statsd

def configure_datadog():
    """Configure Datadog APM and metrics for the Flask application"""
    
    # Get Datadog configuration from environment variables
    dd_api_key = os.getenv('DD_API_KEY')
    dd_app_key = os.getenv('DD_APP_KEY')
    dd_service_name = os.getenv('DD_SERVICE', 'telecom-backend')
    dd_env = os.getenv('DD_ENV', 'production')
    dd_version = os.getenv('DD_VERSION', '1.0.0')
    dd_agent_host = os.getenv('DD_AGENT_HOST', 'datadog-agent')
    dd_trace_agent_port = int(os.getenv('DD_TRACE_AGENT_PORT', '8126'))
    dd_dogstatsd_port = int(os.getenv('DD_DOGSTATSD_PORT', '8125'))
    
    # Set environment variables for ddtrace (critical for proper env detection)
    os.environ['DD_SERVICE'] = dd_service_name
    os.environ['DD_ENV'] = dd_env
    os.environ['DD_VERSION'] = dd_version
    os.environ['DD_AGENT_HOST'] = dd_agent_host
    os.environ['DD_TRACE_AGENT_PORT'] = str(dd_trace_agent_port)
    
    # Configure APM
    config.flask['service_name'] = dd_service_name
    config.flask['collect_request_headers'] = True
    config.flask['collect_response_headers'] = True
    config.flask['trace_query_string'] = True
    
    # Configure service tags - CRITICAL: Set these explicitly
    config.env = dd_env
    config.service = dd_service_name
    config.version = dd_version
    
    # Set global tags to ensure environment is properly tagged
    config.tags = {
        'env': dd_env,
        'service': dd_service_name,
        'version': dd_version,
        'component': 'backend',
        'team': 'telecom'
    }
    
    # Ensure proper service mapping for APM
    config.flask['service_name'] = dd_service_name
    config.flask['distributed_tracing'] = True
    config.flask['analytics_enabled'] = True
    config.flask['analytics_sample_rate'] = 1.0
    
    # Configure trace agent
    config.trace.agent_hostname = dd_agent_host
    config.trace.agent_port = dd_trace_agent_port
    config.trace.enabled = True
    config.trace.analytics_enabled = True
    config.trace.analytics_sample_rate = 1.0
    
    # Configure specific integrations
    config.sqlalchemy['service_name'] = f"{dd_service_name}-db"
    config.requests['service_name'] = f"{dd_service_name}-http"
    
    # Patch all supported libraries
    patch_all()
    
    # Initialize Datadog metrics (optional)
    if dd_api_key and dd_app_key:
        initialize(
            api_key=dd_api_key,
            app_key=dd_app_key,
            host_name=dd_agent_host
        )
    
    # Configure StatsD for custom metrics
    statsd.host = dd_agent_host
    statsd.port = dd_dogstatsd_port
    
    print(f"Datadog configured for service: {dd_service_name}, env: {dd_env}, version: {dd_version}")

def send_custom_metric(metric_name, value, tags=None):
    """Send custom metrics to Datadog"""
    if tags is None:
        tags = []
    
    try:
        statsd.gauge(metric_name, value, tags=tags)
    except Exception as e:
        print(f"Error sending metric {metric_name}: {e}")

def increment_counter(metric_name, tags=None):
    """Increment a counter metric in Datadog"""
    if tags is None:
        tags = []
    
    try:
        statsd.increment(metric_name, tags=tags)
    except Exception as e:
        print(f"Error incrementing counter {metric_name}: {e}")

def record_histogram(metric_name, value, tags=None):
    """Record a histogram metric in Datadog"""
    if tags is None:
        tags = []
    
    try:
        statsd.histogram(metric_name, value, tags=tags)
    except Exception as e:
        print(f"Error recording histogram {metric_name}: {e}")
