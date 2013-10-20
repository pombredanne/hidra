import re
import requests

from flask import Flask
from flask import request
from flask import Response

from ws4py.client.geventclient import WebSocketClient

from sockets import websocket

app = Flask(__name__)
app.debug = True

PROXY_DOMAIN = "127.0.0.1:8888"
PROXY_FORMAT = u"http://%s/%s" % (PROXY_DOMAIN, u"%s")
PROXY_REWRITE_REGEX = re.compile(
    r'((?:src|action|[^_]href|project-url|kernel-url|baseurl)'
    '\s*[=:]\s*["\']?)/',
    re.IGNORECASE
)
websockets = {}


@app.route('/proxy/', defaults={'url': ''}, methods=[
    "GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"
])
@app.route('/proxy/<path:url>', methods=[
    "GET", "POST", "PUT", "DELETE", "HEAD", "OPTIONS", "PATCH"
])
def proxy(url):
    if websocket:
        data = websocket.receive()
        websocket_url = 'ws://{}/{}'.format(PROXY_DOMAIN, url)
        if websocket_url in websockets:
            client = websockets[websocket_url]
        else:
            client = WebSocketClient(websocket_url,
                                     protocols=['http-only', 'chat'])
            websockets[websocket_url] = client
        client.connect()
        client.send(data)
        client_data = client.receive()
        websocket.send(client_data)
    if request.method == "GET":
        url_ending = "%s?%s" % (url, request.query_string)
        url = PROXY_FORMAT % url_ending
        resp = requests.get(url)
    elif request.method == "POST":
        if url == 'kernels':
            url_ending = "%s?%s" % (url, request.query_string)
            url = PROXY_FORMAT % url_ending
        else:
            url = PROXY_FORMAT % url
        resp = requests.post(url, request.data)
    else:
        url = PROXY_FORMAT % url
        resp = requests.request(url, request.method, request.data)
    content = resp.content
    if content:
        content = PROXY_REWRITE_REGEX.sub(r'\1/proxy/', content)
    headers = resp.headers
    if "content-type" in headers:
        mimetype = headers["content-type"].split(";")[0].split(",")[0]
    else:
        mimetype = None
    response = Response(
        content,
        headers=dict(headers),
        mimetype=mimetype,
        status=resp.status_code
    )
    return response
proxy.provide_automatic_options = False


if __name__ == '__main__':
    app.run()
