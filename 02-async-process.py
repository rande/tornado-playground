import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.process
import tornado.concurrent
import tornado.httpclient
import datetime

class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Let's start with a blocking code: <a href='/step1'>Step 1</a><br />")
        self.write("End request!")

class LongProcessHandler(tornado.web.RequestHandler):
    def initialize(self, io_loop=None):
        self.io_loop = io_loop

    @tornado.gen.coroutine
    def get(self):
        print "Start long non-blocking process"
        yield tornado.gen.Task(self.io_loop.add_timeout, datetime.timedelta(seconds=5))
        print "End long non-blocking process"

class Step1Handler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        http_client = tornado.httpclient.AsyncHTTPClient()

        # fetch will return a Future
        f = http_client.fetch("http://localhost:5000/long-process", callback=self.on_fetch)

        print f

        return f

    def on_fetch(self, response):
        self.write("Let's try to not lock the ioloop: <a href='/step2'>Step 2</a><br />")

        self.write("End request!")

        print "End request!"

        self.finish()

class Step2Handler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        http_client = tornado.httpclient.AsyncHTTPClient()

        response = yield http_client.fetch("http://localhost:5000/long-process")

        print response

        self.write("End request!")

        print "End request!"


io_loop = tornado.ioloop.IOLoop.instance()

application = tornado.web.Application([
    (r"/", HomeHandler),
    (r"/long-process", LongProcessHandler, dict(io_loop=io_loop)),
    (r"/step1", Step1Handler),
    (r"/step2", Step2Handler),
])

if __name__ == "__main__":
    application.listen(5000)
    io_loop.start()