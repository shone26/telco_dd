#!/bin/bash

# Advanced Unhappy Path Testing Script with Datadog Integration
# This script runs comprehensive unhappy path tests and monitors results in Datadog

set -e

# Configuration
BACKEND_URL="http://127.0.0.1:5000"
FRONTEND_URL="http://127.0.0.1:3002"
TEST_DURATION=300
CONCURRENT_USERS=10
REPORT_DIR="test_reports"
LOG_FILE="unhappy_path_tests.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] ✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] ⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ❌ $1${NC}"
}

print_header() {
    echo -e "${PURPLE}$1${NC}"
}

# Function to check if services are running
check_services() {
    print_status "Checking if services are running..."
    
    # Check backend
    if curl -s "$BACKEND_URL/api/health/" > /dev/null 2>&1; then
        print_success "Backend service is running at $BACKEND_URL"
    else
        print_error "Backend service is not accessible at $BACKEND_URL"
        print_status "Please start the backend service first"
        exit 1
    fi
    
    # Check frontend
    if curl -s "$FRONTEND_URL" > /dev/null 2>&1; then
        print_success "Frontend service is running at $FRONTEND_URL"
    else
        print_warning "Frontend service is not accessible at $FRONTEND_URL (continuing anyway)"
    fi
    
    # Check Datadog agent
    if curl -s "http://localhost:8126/info" > /dev/null 2>&1; then
        print_success "Datadog agent is running and accepting traces"
    else
        print_warning "Datadog agent may not be running - metrics may not be collected"
    fi
}

# Function to setup test environment
setup_test_environment() {
    print_status "Setting up test environment..."
    
    # Create report directory
    mkdir -p "$REPORT_DIR"
    
    # Clear previous logs
    > "$LOG_FILE"
    
    # Install required Python packages if not already installed
    if ! python3 -c "import datadog" 2>/dev/null; then
        print_status "Installing required Python packages..."
        pip3 install datadog requests
    fi
    
    print_success "Test environment setup complete"
}

# Function to run specific test category
run_test_category() {
    local category=$1
    local description=$2
    
    print_header "🎯 Running $description Tests"
    print_status "Category: $category"
    print_status "Duration: $TEST_DURATION seconds"
    print_status "Concurrent Users: $CONCURRENT_USERS"
    
    cd tests
    
    if python3 test_advanced_unhappy_paths.py \
        --backend-url "$BACKEND_URL" \
        --frontend-url "$FRONTEND_URL" \
        --test-category "$category" \
        --duration "$TEST_DURATION" \
        --concurrent-users "$CONCURRENT_USERS" \
        2>&1 | tee -a "../$LOG_FILE"; then
        print_success "$description tests completed successfully"
        return 0
    else
        print_error "$description tests failed"
        return 1
    fi
    
    cd ..
}

# Function to run all tests
run_all_tests() {
    print_header "🚀 Running All Advanced Unhappy Path Tests"
    
    cd tests
    
    if python3 test_advanced_unhappy_paths.py \
        --backend-url "$BACKEND_URL" \
        --frontend-url "$FRONTEND_URL" \
        --test-category "all" \
        --duration "$TEST_DURATION" \
        --concurrent-users "$CONCURRENT_USERS" \
        2>&1 | tee -a "../$LOG_FILE"; then
        print_success "All unhappy path tests completed successfully"
        return 0
    else
        print_error "Some unhappy path tests failed"
        return 1
    fi
    
    cd ..
}

# Function to generate summary report
generate_summary_report() {
    print_status "Generating summary report..."
    
    local report_file="$REPORT_DIR/unhappy_path_summary_$(date +%Y%m%d_%H%M%S).md"
    
    cat > "$report_file" << EOF
# Unhappy Path Testing Summary Report

**Generated:** $(date)
**Backend URL:** $BACKEND_URL
**Frontend URL:** $FRONTEND_URL
**Test Duration:** $TEST_DURATION seconds
**Concurrent Users:** $CONCURRENT_USERS

## Test Categories Executed

### 1. Payment Cascade Failures 💳
- **Purpose:** Test payment system resilience under various failure conditions
- **Scenarios:** Gateway timeouts, validation failures, fraud detection overload
- **Expected:** Graceful degradation with user notifications

### 2. Authentication Attack Scenarios 🔐
- **Purpose:** Test authentication system security under attack
- **Scenarios:** Brute force, credential stuffing, session hijacking
- **Expected:** Rate limiting and attack detection

### 3. Data Corruption Scenarios 🗄️
- **Purpose:** Test system behavior with malformed/malicious data
- **Scenarios:** Malformed JSON, SQL injection, XSS attempts
- **Expected:** Proper input validation and sanitization

### 4. Resource Exhaustion Scenarios ⚡
- **Purpose:** Test system behavior under resource pressure
- **Scenarios:** Memory pressure, connection pool exhaustion, CPU intensive operations
- **Expected:** Graceful degradation and resource management

### 5. Business Logic Edge Cases 📱
- **Purpose:** Test telecom-specific business logic edge cases
- **Scenarios:** Plan switching conflicts, payment timing issues, quota boundaries
- **Expected:** Consistent business rule enforcement

### 6. Chaos Engineering Scenarios 🌪️
- **Purpose:** Test system resilience under random failures
- **Scenarios:** Random service failures, network partitions, performance degradation
- **Expected:** System continues to function with degraded performance

## Datadog Monitoring

The following metrics are being tracked in Datadog:

- \`telecom.unhappy_path.test_suite.*\` - Overall test suite metrics
- \`telecom.unhappy_path.payment_*\` - Payment failure metrics
- \`telecom.unhappy_path.auth_*\` - Authentication attack metrics
- \`telecom.unhappy_path.corruption_*\` - Data corruption protection metrics
- \`telecom.unhappy_path.resource_*\` - Resource exhaustion metrics
- \`telecom.unhappy_path.business_logic.*\` - Business logic edge case metrics
- \`telecom.unhappy_path.chaos_*\` - Chaos engineering metrics

## Dashboard

A comprehensive Datadog dashboard has been created to monitor these tests:
- **File:** \`datadog_unhappy_path_dashboard.json\`
- **Import:** Use Datadog API or UI to import this dashboard configuration

## Test Results

EOF

    # Add test results if available
    if [ -f "tests/advanced_unhappy_path_report.json" ]; then
        echo "### Detailed Results" >> "$report_file"
        echo "" >> "$report_file"
        echo "Detailed test results are available in:" >> "$report_file"
        echo "- \`tests/advanced_unhappy_path_report.json\`" >> "$report_file"
        echo "" >> "$report_file"
    fi
    
    # Add log information
    echo "### Logs" >> "$report_file"
    echo "" >> "$report_file"
    echo "Full test execution logs are available in:" >> "$report_file"
    echo "- \`$LOG_FILE\`" >> "$report_file"
    echo "" >> "$report_file"
    
    print_success "Summary report generated: $report_file"
}

# Function to show Datadog dashboard instructions
show_datadog_instructions() {
    print_header "📈 Datadog Dashboard Setup Instructions"
    
    cat << EOF

To set up the Datadog dashboard for monitoring unhappy path tests:

1. **Import Dashboard:**
   - Go to Datadog UI > Dashboards > New Dashboard
   - Click "Import Dashboard JSON"
   - Upload the file: datadog_unhappy_path_dashboard.json

2. **API Import (Alternative):**
   curl -X POST "https://api.datadoghq.com/api/v1/dashboard" \\
     -H "Content-Type: application/json" \\
     -H "DD-API-KEY: \${DD_API_KEY}" \\
     -H "DD-APPLICATION-KEY: \${DD_APP_KEY}" \\
     -d @datadog_unhappy_path_dashboard.json

3. **Key Metrics to Monitor:**
   - Overall test success rate
   - Payment failure patterns
   - Authentication attack detection
   - Data corruption protection effectiveness
   - Resource exhaustion handling
   - Business logic edge case coverage
   - Chaos engineering resilience

4. **Alerts (Recommended):**
   - Alert when success rate drops below 70%
   - Alert on high authentication attack rates
   - Alert on resource exhaustion scenarios
   - Alert on business logic failures

5. **Dashboard URL:**
   After import, the dashboard will be available at:
   https://app.datadoghq.com/dashboard/[dashboard-id]

EOF
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up..."
    # Add any cleanup tasks here
    print_success "Cleanup completed"
}

# Main execution
main() {
    print_header "🔥 Advanced Unhappy Path Testing with Datadog Integration"
    print_header "================================================================"
    
    # Parse command line arguments
    TEST_CATEGORY="all"
    SHOW_HELP=false
    SETUP_ONLY=false
    DASHBOARD_ONLY=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --category)
                TEST_CATEGORY="$2"
                shift 2
                ;;
            --backend-url)
                BACKEND_URL="$2"
                shift 2
                ;;
            --frontend-url)
                FRONTEND_URL="$2"
                shift 2
                ;;
            --duration)
                TEST_DURATION="$2"
                shift 2
                ;;
            --concurrent-users)
                CONCURRENT_USERS="$2"
                shift 2
                ;;
            --setup-only)
                SETUP_ONLY=true
                shift
                ;;
            --dashboard-only)
                DASHBOARD_ONLY=true
                shift
                ;;
            --help|-h)
                SHOW_HELP=true
                shift
                ;;
            *)
                print_error "Unknown option: $1"
                SHOW_HELP=true
                shift
                ;;
        esac
    done
    
    if [ "$SHOW_HELP" = true ]; then
        cat << EOF
Usage: $0 [OPTIONS]

Advanced Unhappy Path Testing Script with Datadog Integration

OPTIONS:
    --category CATEGORY         Test category to run (payment, auth, corruption, exhaustion, business, chaos, all)
    --backend-url URL          Backend service URL (default: http://127.0.0.1:5000)
    --frontend-url URL         Frontend service URL (default: http://127.0.0.1:3002)
    --duration SECONDS         Test duration in seconds (default: 300)
    --concurrent-users COUNT   Number of concurrent users (default: 10)
    --setup-only              Only setup test environment, don't run tests
    --dashboard-only           Only show Datadog dashboard instructions
    --help, -h                 Show this help message

EXAMPLES:
    # Run all tests
    $0

    # Run only payment tests
    $0 --category payment

    # Run tests with custom settings
    $0 --category all --duration 600 --concurrent-users 20

    # Setup environment only
    $0 --setup-only

    # Show dashboard instructions
    $0 --dashboard-only

TEST CATEGORIES:
    payment     - Payment cascade failure scenarios
    auth        - Authentication attack scenarios  
    corruption  - Data corruption and injection tests
    exhaustion  - Resource exhaustion scenarios
    business    - Business logic edge cases
    chaos       - Chaos engineering scenarios
    all         - All test categories (default)

EOF
        exit 0
    fi
    
    if [ "$DASHBOARD_ONLY" = true ]; then
        show_datadog_instructions
        exit 0
    fi
    
    # Setup test environment
    setup_test_environment
    
    if [ "$SETUP_ONLY" = true ]; then
        print_success "Test environment setup completed"
        exit 0
    fi
    
    # Check services
    check_services
    
    # Run tests based on category
    test_success=true
    
    case $TEST_CATEGORY in
        "payment")
            run_test_category "payment" "Payment Cascade Failure" || test_success=false
            ;;
        "auth")
            run_test_category "auth" "Authentication Attack" || test_success=false
            ;;
        "corruption")
            run_test_category "corruption" "Data Corruption" || test_success=false
            ;;
        "exhaustion")
            run_test_category "exhaustion" "Resource Exhaustion" || test_success=false
            ;;
        "business")
            run_test_category "business" "Business Logic Edge Case" || test_success=false
            ;;
        "chaos")
            run_test_category "chaos" "Chaos Engineering" || test_success=false
            ;;
        "all")
            run_all_tests || test_success=false
            ;;
        *)
            print_error "Invalid test category: $TEST_CATEGORY"
            print_status "Valid categories: payment, auth, corruption, exhaustion, business, chaos, all"
            exit 1
            ;;
    esac
    
    # Generate summary report
    generate_summary_report
    
    # Show Datadog instructions
    show_datadog_instructions
    
    # Final status
    if [ "$test_success" = true ]; then
        print_success "🎉 Unhappy path testing completed successfully!"
        print_status "📊 Check Datadog dashboard for detailed metrics and insights"
        print_status "📄 Summary report available in: $REPORT_DIR/"
        exit 0
    else
        print_error "⚠️  Some unhappy path tests failed"
        print_status "📊 Check Datadog dashboard and logs for details"
        print_status "📄 Summary report available in: $REPORT_DIR/"
        exit 1
    fi
}

# Trap cleanup on exit
trap cleanup EXIT

# Run main function
main "$@"
