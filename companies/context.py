"""Thread/async-safe holder for "which company is this request for".

Using contextvars (not a plain module global) so each request's value is
isolated even under async views or thread-pool workers.
"""
import contextvars

_current_company = contextvars.ContextVar('current_company', default=None)


def set_current_company(company):
    _current_company.set(company)


def get_current_company():
    return _current_company.get()
