import ast
import uuid
from functools import wraps

import flask
from flask import Response
from werkzeug.datastructures import Headers

from redis_instance import r, redlock_factory


def detect_idempotent(idempotency_key):
    value = r.hgetall(idempotency_key)
    if value:
        headers = ast.literal_eval(value[b'headers'].decode())
        headers = Headers(headers)
        headers['Idempotent-Replayed'] = 'true'
        return Response(value[b'body'], status=value[b'status'].decode(), headers=headers)


def store_idempotent_result(response, idempotency_key, idempotency_entry_ttl=60):
    if idempotency_key is not None:
        headers = response.headers.to_wsgi_list()
        r.hmset(idempotency_key, {'body': response.data, 'headers': headers, 'status': response.status_code})
        r.expire(idempotency_key, idempotency_entry_ttl)


def idempotent_view_from_header_parametrize(idempotency_entry_ttl=60, lock_ttl=60_000, lock_retry_times=300):
    def wrap_func(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            request = flask.request
            idempotency_key = request.headers.get('Idempotency-Key')

            if request.method == "POST" and idempotency_key is not None:
                lock = redlock_factory.create_lock(f'lock_{idempotency_key}', ttl=lock_ttl, retry_times=lock_retry_times)

                with lock:
                    response = detect_idempotent(idempotency_key)
                    if response:
                        return response

                    response = f(*args, **kwargs)
                    store_idempotent_result(response, idempotency_key, idempotency_entry_ttl)
                    return response
            else:
                return f(*args, **kwargs)
        return decorated_function
    return wrap_func


def idempotent_view_from_header(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request = flask.request
        idempotency_key = request.headers.get('Idempotency-Key')

        if request.method == "POST" and idempotency_key is not None:
            lock = redlock_factory.create_lock(f'lock_{idempotency_key}', ttl=60_000, retry_times=300)

            with lock:
                response = detect_idempotent(idempotency_key)
                if response:
                    return response

                response = f(*args, **kwargs)
                store_idempotent_result(response, idempotency_key)
                return response
        else:
            return f(*args, **kwargs)
    return decorated_function


def idempotent_view_from_payload(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        request = flask.request

        is_idempotent = False
        idempotency_key = request.json.get('request', {}).get('idempotency_key')

        if request.method == "POST" and idempotency_key is not None:
            is_idempotent = True
            response = detect_idempotent(idempotency_key)

            if response:
                return response

        response = f(*args, **kwargs)

        if is_idempotent:
            store_idempotent_result(response, idempotency_key)
        return response
    return decorated_function