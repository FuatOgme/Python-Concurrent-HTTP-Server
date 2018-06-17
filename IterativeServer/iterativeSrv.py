#Iterative server (python 3.6)#
from io import StringIO # Python 3
import time
import socket
import sys

class WSGIServer(object):

    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 1

    def __init__(self, server_address):
        # Create a listening socket
        self.listen_socket = listen_socket = socket.socket(
            self.address_family,
            self.socket_type
        )
        # Allow to reuse the same address
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind
        listen_socket.bind(server_address)
        # Activate
        listen_socket.listen(self.request_queue_size)
        # Get server host name and port
        host, port = self.listen_socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port
        # Return headers set by Web framework/Web application
        self.headers_set = []
        print('WSGIServer: Serving on port {port} ...\n'.format(port=self.server_port))

    def set_app(self, application):
        self.application = application

    def serve_forever(self):
        listen_socket = self.listen_socket
        while True:
            self.client_connection, client_address = listen_socket.accept()
            self.handle_one_request()

    def handle_one_request(self):
        self.request_data = request_data = self.client_connection.recv(1024)
        print(''.join(
            '< {line}\n'.format(line=line)
            for line in request_data.splitlines()
        ))

        self.parse_request(request_data)

        env = self.get_environ()

        result = self.application(env, self.start_response)

        self.finish_response(result)

    def parse_request(self, text):
        request_line = text.splitlines()[0].decode('utf-8')
        request_line = request_line.rstrip('\r\n')
        (self.request_method,  # GET
         self.path,            # /hello
         self.request_version  # HTTP/1.1
         ) = request_line.split()

    def get_environ(self):
        env = {}
        env['wsgi.version']      = (1, 0)
        env['wsgi.url_scheme']   = 'http'
        env['wsgi.input']        = StringIO(self.request_data.decode('utf-8'))
        env['wsgi.errors']       = sys.stderr
        env['wsgi.multithread']  = False
        env['wsgi.multiprocess'] = False
        env['wsgi.run_once']     = False
        # Required CGI variables
        env['REQUEST_METHOD']    = self.request_method    # GET
        env['PATH_INFO']         = self.path              # /hello
        env['SERVER_NAME']       = self.server_name       # localhost
        env['SERVER_PORT']       = str(self.server_port)  # 8888
        return env

    def start_response(self, status, response_headers, exc_info=None):
        server_headers = [
            ('Date', 'Tue, 31 Mar 2015 12:54:48 GMT'),
            ('Server', 'WSGIServer 0.2'),
        ]
        self.headers_set = [status, response_headers + server_headers]

    def finish_response(self, result):
        try:
            status, response_headers = self.headers_set
            response = 'HTTP/1.1 {status}\r\n'.format(status=status)
            for header in response_headers:
                response += '{0}: {1}\r\n'.format(*header)
            response += '\r\n'
            for data in result:
                response += data.decode('utf-8')
            print(''.join(
                '> {line}\n'.format(line=line)
                for line in response.splitlines()
            ))
            #self.client_connection.sendall(bytes(response, 'UTF-8')),
            self.client_connection.sendall(response.encode('utf-8'))
            time.sleep(30)
        finally:
            self.client_connection.close()


SERVER_ADDRESS = (HOST, PORT) = '', 8888


def WsgiServer(server_address, application):
    server = WSGIServer(server_address)
    server.set_app(application)
    return server


class SimpleServer(object):
    address_family = socket.AF_INET
    socket_type = socket.SOCK_STREAM
    request_queue_size = 1024

    def __init__(self, server_address):
        self.listen_socket = listen_socket = socket.socket(
            self.address_family,
            self.socket_type
        )
        listen_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        listen_socket.bind(server_address)
        listen_socket.listen(self.request_queue_size)
        host, port = self.listen_socket.getsockname()[:2]
        self.server_name = socket.getfqdn(host)
        self.server_port = port
        self.headers_set = []
        print('Iterative Serving HTTP on port {port} ...'.format(port=port))

    def serve_forever(self):
        listen_socket = self.listen_socket
        while True:
            self.client_connection, client_address = listen_socket.accept()
            self.handle_request(self.client_connection)
            self.client_connection.close()

    def handle_request(self,client_connection):
        request = self.client_connection.recv(1024)
        print(request.decode())
        http_response = b"""\
HTTP/1.1 200 OK

Hello, World!
"""
        self.client_connection.sendall(http_response)
        time.sleep(30)


if __name__ == '__main__':
    if len(sys.argv) < 2: #if there is no wsgi application, run as simple server
        server = SimpleServer(SERVER_ADDRESS)
        server.serve_forever()
    else: #if there is any wsgi application, create a new wsgi server accordingly
        app_path = sys.argv[1]
        module, application = app_path.split(':')
        module = __import__(module)
        application = getattr(module, application)
        server = WsgiServer(SERVER_ADDRESS, application)
        server.serve_forever()
