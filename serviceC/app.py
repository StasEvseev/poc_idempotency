import time
from flask import Flask, Response

from helpers import idempotent_view_from_header, idempotent_view_from_payload, idempotent_view_from_header_parametrize

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///example.sqlite"


@app.route('/')
def hello_world():
    return 'Hello World!'


@app.route('/post', methods=['POST'])
@idempotent_view_from_header_parametrize(idempotency_entry_ttl=60 * 5)
def create_post():
    with open(f'database/{time.time()}', 'w') as f:
        f.write('new file')
        time.sleep(5)
    return Response()


@app.route('/post_from_params', methods=['POST'])
@idempotent_view_from_payload
def create_post_from_params():
    with open(f'database_params/{time.time()}', 'w') as f:
        f.write('new file')
    return Response()


if __name__ == '__main__':
    app.run()
