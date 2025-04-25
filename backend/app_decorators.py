"""
Decorators for Flask routes authentication and authorization.
"""
import logging
from functools import wraps

from flask import abort, redirect, url_for, flash, request
from flask_login import current_user


def admin_required(f):
    """
    Decorator to ensure that the current user is authenticated and has admin privileges.
    If not, the request is aborted with a 403 Forbidden status.
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            if request.is_json:
                # For API requests, return 403 Forbidden with a JSON response
                abort(403, description="Admin access required")
            else:
                # For web requests, flash a message and redirect to login
                flash("Необходимы права администратора", "error")
                logging.getLogger(__name__).warning("Необходимы права администратора")
                return redirect(url_for('admin.index'))
        return f(*args, **kwargs)

    return decorated_function
