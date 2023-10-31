import matplotlib as mpl
mpl.use("agg")

import io
import json
import mimetypes
from pathlib import Path
import signal
import socket

try:
    import tornado
except ImportError as err:
    raise RuntimeError("This example requires tornado.") from err
import tornado.httpserver
import tornado.ioloop
import tornado.web
import tornado.websocket

from matplotlib.backends.backend_webagg import (
    FigureManagerWebAgg, new_figure_manager_given_figure)
import matplotlib.pyplot as plt

# import script to create the figure
from create_figure import create_figure

port = 8080

class MyApplication(tornado.web.Application):
    figures = dict()

    def __init__(self):

        super().__init__([
            # Static files for the CSS and JS
            (r'/_static/(.*)',
             tornado.web.StaticFileHandler,
             {'path': FigureManagerWebAgg.get_static_file_path()}),

            # Static images for the toolbar
            (r'/_images/(.*)',
             tornado.web.StaticFileHandler,
             {'path': Path(mpl.get_data_path(), 'images')}),

            # The page that contains all of the pieces
            ('/', self.MainPage),

            ('/mpl.js', self.MplJs),

            # Sends images and events to the browser, and receives
            # events from the browser
            (r'/(?P<fignum>[0-9]+)/ws', self.WebSocket),

            # Handles the downloading (i.e., saving) of static images
            (r'/(?P<fignum>[0-9]+).(?P<fmt>[a-z0-9.]+)', self.Download),
        ],

        static_path='static',
        template_path='templates',
        )

    class MainPage(tornado.web.RequestHandler):
        """
        Serves the main HTML page.
        """

        def get(self):
            figure = create_figure()
            fignum = id(figure)
            manager = new_figure_manager_given_figure(fignum, figure)

            self.application.figures[fignum] = (figure, manager)

            nfigs = len(self.application.figures)
            print(f"New figure (id={fignum}) created!")
            print(f"There {'is' if nfigs == 1 else 'are'} "
                  f"currently {nfigs} open figure{'s' if nfigs != 1 else ''}!")


            ws_uri = f"ws://{self.request.host}"

            content = self.render_string(
                "index.html",
                ws_uri=ws_uri,
                fig_id=fignum
                )
            self.write(content)

    class MplJs(tornado.web.RequestHandler):
        """
        Serves the generated matplotlib javascript file.  The content
        is dynamically generated based on which toolbar functions the
        user has defined.  Call `FigureManagerWebAgg` to get its
        content.
        """

        def get(self):
            self.set_header('Content-Type', 'application/javascript')
            js_content = FigureManagerWebAgg.get_javascript()

            self.write(js_content)

    class Download(tornado.web.RequestHandler):
        """
        Handles downloading of the figure in various file formats.
        """

        def get(self, fmt, fignum):
            fignum = int(fignum)

            manager = self.application.figures[fignum][1]
            self.set_header(
                'Content-Type', mimetypes.types_map.get(fmt, 'binary'))
            buff = io.BytesIO()
            manager.canvas.figure.savefig(buff, format=fmt)
            self.write(buff.getvalue())

    class WebSocket(tornado.websocket.WebSocketHandler):
        """
        A websocket for interactive communication between the plot in
        the browser and the server.

        In addition to the methods required by tornado, it is required to
        have two callback methods:

            - ``send_json(json_content)`` is called by matplotlib when
              it needs to send json to the browser.  `json_content` is
              a JSON tree (Python dictionary), and it is the responsibility
              of this implementation to encode it as a string to send over
              the socket.

            - ``send_binary(blob)`` is called to send binary image data
              to the browser.
        """
        supports_binary = True


        def open(self, fignum):
            self.fignum = int(fignum)

            # Register the websocket with the FigureManager.
            self.manager = self.application.figures[self.fignum][1]
            self.manager.add_web_socket(self)

            if hasattr(self, 'set_nodelay'):
                self.set_nodelay(True)

        def on_close(self):
            # When the socket is closed, deregister the websocket with
            # the FigureManager.
            print(f"Socket closed, closing figure (id={self.manager.num}).")

            self.manager.remove_web_socket(self)
            self.application.figures.pop(self.manager.num)

            nfigs = len(self.application.figures)
            print(f"There {'is' if nfigs == 1 else 'are'} "
                  f"currently {nfigs} open figure{'s' if nfigs != 1 else ''}!")

        def on_message(self, message):
            # The 'supports_binary' message is relevant to the
            # websocket itself.  The other messages get passed along
            # to matplotlib as-is.

            # Every message has a "type" and a "figure_id".
            message = json.loads(message)
            if message['type'] == 'supports_binary':
                self.supports_binary = message['value']
            else:
                self.manager.handle_json(message)

        def send_json(self, content):
            self.write_message(json.dumps(content))

        def send_binary(self, blob):
            if self.supports_binary:
                self.write_message(blob, binary=True)
            else:
                data_uri = ("data:image/png;base64," +
                            blob.encode('base64').replace('\n', ''))
                self.write_message(data_uri)


if __name__ == "__main__":
    application = MyApplication()

    http_server = tornado.httpserver.HTTPServer(application)

    sockets = tornado.netutil.bind_sockets(port, '')
    http_server.add_sockets(sockets)

    for s in sockets:
        addr, port = s.getsockname()[:2]
        if s.family is socket.AF_INET6:
            addr = f'[{addr}]'
        print(f"Listening on http://{addr}:{port}/")
    print("Press Ctrl+C to quit")

    ioloop = tornado.ioloop.IOLoop.instance()

    def shutdown():
        ioloop.stop()
        print("Server stopped")

    old_handler = signal.signal(
        signal.SIGINT,
        lambda sig, frame: ioloop.add_callback_from_signal(shutdown))

    try:
        ioloop.start()
    finally:
        signal.signal(signal.SIGINT, old_handler)