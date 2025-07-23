import time
import functools
from flask import request, g

def monitor_database_performance():
    """Monitor database query performance"""
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = f(*args, **kwargs)
                # Record successful database operation
                try:
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from datadog_config import increment_counter
                    increment_counter('telecom.database.query.success')
                except:
                    pass
                return result
            except Exception as e:
                # Record database error
                try:
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from datadog_config import increment_counter
                    increment_counter('telecom.database.query.error')
                except:
                    pass
                raise
            finally:
                # Record query duration
                duration = (time.time() - start_time) * 1000
                try:
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from datadog_config import record_histogram
                    record_histogram('telecom.database.query.duration', duration)
                except:
                    pass
        return wrapper
    return decorator

def monitor_route_performance():
    """Monitor route performance"""
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            route_name = f.__name__
            
            try:
                result = f(*args, **kwargs)
                # Record successful request
                try:
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from datadog_config import increment_counter
                    increment_counter('telecom.route.success', tags=[f'route:{route_name}'])
                except:
                    pass
                return result
            except Exception as e:
                # Record route error
                try:
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from datadog_config import increment_counter
                    increment_counter('telecom.route.error', tags=[f'route:{route_name}'])
                except:
                    pass
                raise
            finally:
                # Record route duration
                duration = (time.time() - start_time) * 1000
                try:
                    import sys
                    import os
                    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                    from datadog_config import record_histogram
                    record_histogram('telecom.route.duration', duration, 
                                   tags=[f'route:{route_name}'])
                except:
                    pass
        return wrapper
    return decorator

class PerformanceMiddleware:
    """Middleware to monitor overall request performance"""
    
    def __init__(self, app):
        self.app = app
        self.app.before_request(self.before_request)
        self.app.after_request(self.after_request)
    
    def before_request(self):
        g.start_time = time.time()
    
    def after_request(self, response):
        if hasattr(g, 'start_time'):
            duration = (time.time() - g.start_time) * 1000
            
            # Record request metrics
            try:
                import sys
                import os
                sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                from datadog_config import record_histogram, increment_counter
                record_histogram('telecom.request.duration', duration, 
                               tags=[f'method:{request.method}', f'status:{response.status_code}'])
                
                if response.status_code >= 400:
                    increment_counter('telecom.request.error', 
                                    tags=[f'status:{response.status_code}'])
                else:
                    increment_counter('telecom.request.success')
            except:
                pass
        
        return response
