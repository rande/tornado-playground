import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.process
import tornado.concurrent
import tornado.httpclient

class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Let's start with a blocking code: <a href='/step1'>Step 1</a><br />")
        self.write("End request!")

class Step1Handler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        http_client = tornado.httpclient.AsyncHTTPClient()

        # fetch will return a Future
        f = http_client.fetch("http://google.com", callback=self.on_fetch)

        print f

        return f

    def on_fetch(self, response):
        self.write("Let's try to not lock the ioloop: <a href='/step7'>Step 7</a><br />")

        self.write("End request!")

        print "End request!"

        self.finish()

class Step2Handler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        http_client = tornado.httpclient.AsyncHTTPClient()

        response = yield http_client.fetch("http://google.com")

        print response

        self.write("End request!")

        print "End request!"


io_loop = tornado.ioloop.IOLoop.instance()

application = tornado.web.Application([
    (r"/", HomeHandler),
    (r"/step1", Step1Handler),
    (r"/step2", Step2Handler),
])

if __name__ == "__main__":
    application.listen(5000)
    io_loop.start()