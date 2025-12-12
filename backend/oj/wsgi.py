"""
WSGI config for qduoj project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/1.8/howto/deployment/wsgi/
"""

import os
import json
import time
from django.core.wsgi import get_wsgi_application

# #region agent log
def debug_log(location, message, hypothesis_id="", data=None):
    """Write debug log in NDJSON format"""
    try:
        data_dir = os.environ.get('DATA_DIR', '/data')
        debug_log_path = os.path.join(data_dir, 'log', 'debug.log')
        timestamp = int(time.time() * 1000)
        log_entry = {
            "id": f"log_{timestamp}_{os.getpid()}",
            "timestamp": timestamp,
            "location": location,
            "message": message,
            "data": data or {},
            "sessionId": "debug-session",
            "runId": "run1",
            "hypothesisId": hypothesis_id
        }
        with open(debug_log_path, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception:
        pass  # Silently fail if logging fails
# #endregion

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "oj.settings")

# #region agent log
debug_log("wsgi.py:29", "WSGI application loading started", "A", {"settings_module": "oj.settings"})
# #endregion

try:
    application = get_wsgi_application()
    # #region agent log
    debug_log("wsgi.py:32", "WSGI application loaded successfully", "A", {})
    
    # Test database connection
    try:
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        debug_log("wsgi.py:38", "Database connection test successful", "B", {})
    except Exception as e:
        debug_log("wsgi.py:38", "Database connection test failed", "B", {"error": str(e)})
    
    # Test Redis connection
    try:
        from django.core.cache import cache
        cache.set('wsgi_test', 'ok', 1)
        result = cache.get('wsgi_test')
        debug_log("wsgi.py:46", "Redis connection test successful", "B", {"test_result": result})
    except Exception as e:
        debug_log("wsgi.py:46", "Redis connection test failed", "B", {"error": str(e)})
    # #endregion
except Exception as e:
    # #region agent log
    debug_log("wsgi.py:32", "WSGI application loading failed", "A", {"error": str(e), "error_type": type(e).__name__})
    # #endregion
    raise
