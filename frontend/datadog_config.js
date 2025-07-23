/**
 * Datadog configuration for the telecom frontend application
 */

const tracer = require('dd-trace');
const StatsD = require('hot-shots');

// Initialize Datadog tracer
function configureDatadog() {
    // Get Datadog configuration from environment variables
    const ddServiceName = process.env.DD_SERVICE || 'telecom-frontend';
    const ddEnv = process.env.DD_ENV || 'production';
    const ddVersion = process.env.DD_VERSION || '1.0.0';
    const ddAgentHost = process.env.DD_AGENT_HOST || 'datadog-agent';
    const ddTraceAgentPort = parseInt(process.env.DD_TRACE_AGENT_PORT || '8126');
    const ddDogstatsdPort = parseInt(process.env.DD_DOGSTATSD_PORT || '8125');

    // Set environment variables for dd-trace (critical for proper env detection)
    process.env.DD_SERVICE = ddServiceName;
    process.env.DD_ENV = ddEnv;
    process.env.DD_VERSION = ddVersion;
    process.env.DD_AGENT_HOST = ddAgentHost;
    process.env.DD_TRACE_AGENT_PORT = ddTraceAgentPort.toString();

    // Initialize the tracer with explicit configuration
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
            version: ddVersion,
            component: 'frontend',
            team: 'telecom',
            // Additional explicit tags to ensure environment detection
            'dd.env': ddEnv,
            'dd.service': ddServiceName,
            'dd.version': ddVersion
        }
    });

    console.log(`Datadog configured for service: ${ddServiceName}, env: ${ddEnv}, version: ${ddVersion}`);

    return tracer;
}

// Initialize StatsD client for custom metrics
function createStatsClient() {
    const ddAgentHost = process.env.DD_AGENT_HOST || 'datadog-agent';
    const ddDogstatsdPort = parseInt(process.env.DD_DOGSTATSD_PORT || '8125');

    return new StatsD({
        host: ddAgentHost,
        port: ddDogstatsdPort,
        prefix: 'telecom.frontend.',
        globalTags: {
            service: process.env.DD_SERVICE || 'telecom-frontend',
            env: process.env.DD_ENV || 'production',
            version: process.env.DD_VERSION || '1.0.0'
        }
    });
}

// Custom metrics helpers
function sendCustomMetric(statsClient, metricName, value, tags = {}) {
    try {
        statsClient.gauge(metricName, value, tags);
    } catch (error) {
        console.error(`Error sending metric ${metricName}:`, error);
    }
}

function incrementCounter(statsClient, metricName, tags = {}) {
    try {
        statsClient.increment(metricName, 1, tags);
    } catch (error) {
        console.error(`Error incrementing counter ${metricName}:`, error);
    }
}

function recordHistogram(statsClient, metricName, value, tags = {}) {
    try {
        statsClient.histogram(metricName, value, tags);
    } catch (error) {
        console.error(`Error recording histogram ${metricName}:`, error);
    }
}

function recordTiming(statsClient, metricName, duration, tags = {}) {
    try {
        statsClient.timing(metricName, duration, tags);
    } catch (error) {
        console.error(`Error recording timing ${metricName}:`, error);
    }
}

// Express middleware for request tracking
function createRequestTrackingMiddleware(statsClient) {
    return (req, res, next) => {
        const startTime = Date.now();
        
        // Track request count
        incrementCounter(statsClient, 'requests.count', {
            method: req.method,
            route: req.route ? req.route.path : req.path
        });

        // Override res.end to capture response metrics
        const originalEnd = res.end;
        res.end = function(...args) {
            const duration = Date.now() - startTime;
            
            // Track response time
            recordTiming(statsClient, 'requests.duration', duration, {
                method: req.method,
                status_code: res.statusCode,
                route: req.route ? req.route.path : req.path
            });

            // Track status codes
            incrementCounter(statsClient, 'requests.status', {
                status_code: res.statusCode,
                method: req.method
            });

            originalEnd.apply(this, args);
        };

        next();
    };
}

module.exports = {
    configureDatadog,
    createStatsClient,
    sendCustomMetric,
    incrementCounter,
    recordHistogram,
    recordTiming,
    createRequestTrackingMiddleware
};
