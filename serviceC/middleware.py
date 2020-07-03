from flask import Flask
from werkzeug.wrappers import Request, Response, ResponseStream
from redis_instance import r


class middleware():
    '''
    Simple WSGI middleware
    '''

    def __init__(self, app: Flask):
        self.app = app
        # self.userName = 'Tony'
        # self.password = 'IamIronMan'

    def __call__(self, environ, start_response):
        request = Request(environ)

        idempotency_key = None

        if request.method == "POST":

            idempotency_key = request.headers.get('Idempotency-Key')
            value = r.get(idempotency_key)
            print("POST with Idempotency-Key =", idempotency_key, "value =", value)

            if value:
                headers = value['headers']
                headers['Idempotent-Replayed'] = True
                return Response(value['body'], status=value['status'], headers=headers)

        # these are hardcoded for demonstration
        # verify the username and password from some database or env config variable
        # if userName == self.userName and password == self.password:
        #     environ['user'] = {'name': 'Tony'}
        # print('middleware.__call__', request, request.method)
        response = self.app(environ, start_response)

        if idempotency_key:
            # print(list(response))
            # print(response())
            print(response, type(response), dir(response))
            # import pdb; pdb.set_trace()
            # r.set(idempotency_key, {'body': response.body}, ex=60 * 60 * 24)
            pass

        return response

        # res = Response(u'Authorization failed', mimetype='text/plain', status=401)
        # return res(environ, start_response)