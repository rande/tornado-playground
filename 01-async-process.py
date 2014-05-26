import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.process
import tornado.concurrent
import tornado.httpclient

from futures import ThreadPoolExecutor

import time

class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Let's start with a blocking code: <a href='/step1'>Step 1</a><br />")
        self.write("End request!")

class Step1Handler(tornado.web.RequestHandler):
    def get(self):
        """
        This code will block because time.sleep is blocking the process
        """

        time.sleep(5)

        self.write("You wait 5 seconds and you lock the ioloop<br/>")
        self.write("Try to start two simultaneous connections, the second one will last for 10s. <br />")

        self.write("Let's try to not lock the ioloop: <a href='/step2'>Step 2</a><br />")
        self.write("End request!")

class Step2Handler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        """
        This code will still block the ioloop because time.sleep is blocking event with the
        @tornado.web.asynchronous annotation.
        """
        time.sleep(5)

        self.write("You wait 5 seconds and you lock the ioloop<br/>")
        self.write("Try to start two simultaneous connections, the second one will last for 10s. <br />")

        self.write("Let's try to not lock the ioloop: <a href='/step3'>Step 3</a><br />")
        self.write("End request!")

        # the finish is mandatory to close the connection as the @tornado.web.asynchronous annotation
        # will not call the finish() method
        self.finish()

class Step3Handler(tornado.web.RequestHandler):
    def initialize(self, executor=None):
        """
        The executor is shared between each Handler instance, so you can control the number of thread running
        simultaneously at the same time.

        Note: the executor property is mandatory to use the @run_on_executor annotation
        """
        self.executor = executor

    @tornado.concurrent.run_on_executor
    def sleep(self):
        print "I will sleep 5s in foreground ..."

        time.sleep(5)

        print "I had sleep for 5s"

    @tornado.web.asynchronous
    def get(self):
        """
        This code will not block the event loop, because the @run_on_executor annotation puts the
        sleep method inside a thread, so the code return directly, this can be a good solution
        if you want to run a background job and NOT display the result to user.

        The ThreadPoolExecutor also manage up to 10 simultaneous thread, others will wait if the
        number of simultaneous connections > 10
        """
        self.sleep()

        self.write("You havn't wait 5 seconds and you don't block the ioloop<br/>")
        self.write("But you create multiple threads handled by the executor ... <br />")

        self.write("Let's try to not block the ioloop: <a href='/step4'>Step 4</a><br />")
        self.write("End request!")

        print "End request!"
        self.finish()

class Step4Handler(tornado.web.RequestHandler):
    def initialize(self, executor=None, io_loop=None):
        """
        The executor is shared between each Handler instance, so you can control the number of thread running
        simultaneously in the same time.

        Note: the executor property is mandatory to use the @run_on_executor annotation
        """
        self.executor = executor

        """
        The sleep now used the callback kwargs to provide a callback function, so the io_loop argument
        is required to run the blocking code.
        """
        self.io_loop = io_loop

    @tornado.concurrent.run_on_executor
    def sleep(self):
        """
        The @run_on_executor annotation always return a future object, so once the function terminate
        the future will contains the "hello" string as a result

        The callback will result this result (and not the future)
        """
        print "I will sleep 5s in foreground ..."

        time.sleep(5)

        print "I had sleep for 5s"

        return "Hello"

    @tornado.web.asynchronous
    def get(self):
        """
        This code will not block the event loop, because the @run_on_executor annotation puts the
        sleep method inside a thread, however the method call now provide a callback method.
        """
        self.sleep(callback=self.complete)

        self.write("You wait 5 seconds and you don't block the ioloop<br/>")
        self.write("Try to start two simultaneous connections, the second one will last for 5s. too ...  <br />")

    def complete(self, returned_value):
        self.write("The sleep method also return a message for you: %s" % returned_value)

        self.write("Let's try to not block the ioloop: <a href='/step5'>Step 5</a><br />")
        self.write("End request!")

        print "End request!"

        self.finish()

class Step5Handler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    def get(self):
        """
        The tornado.process.Subprocess class is async so the call will not block. The callback
        will close the connection when the response will be known.
        """
        print "Start process"
        p = tornado.process.Subprocess(["sleep", "5"])
        p.set_exit_callback(self.complete)
        print "Write output"

        self.write("You wait 5 seconds and you don't block the ioloop<br/>")
        self.write("Try to start two simultaneous connections, the second one will last for 5s. too ...  <br />")

    def complete(self, status_code):
        self.write("Let's try to not block the ioloop: <a href='/step6'>Step 6</a><br />")

        self.write("End request!")

        print "End request!"

        self.finish()

class Step6Handler(tornado.web.RequestHandler):
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

class Step7Handler(tornado.web.RequestHandler):
    @tornado.gen.coroutine
    def get(self):
        http_client = tornado.httpclient.AsyncHTTPClient()

        response = yield http_client.fetch("http://google.com")

        print response

        self.write("End request!")

        print "End request!"

class Step8Handler(tornado.web.RequestHandler):
    def sleep(self):
        pass
        ## how to do that ?
        # print "start to sleep"
        # f = tornado.concurrent.Future()
        #
        # time.sleep(5)
        #
        # print "start to wake up"
        # return f

    @tornado.gen.coroutine
    def get(self):
        print "start yielding"
        response = yield self.sleep()

        print response

        self.write("End request!")

        print "End request!"

# The ProcessPoolExecutor class is an Executor subclass that uses a pool of processes to execute calls asynchronously.
# ProcessPoolExecutor uses the multiprocessing module, which allows it to side-step the Global Interpreter Lock
# but also means that only picklable objects can be executed and returned.
#
# reference: https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor
executor = ThreadPoolExecutor(max_workers=10)
io_loop = tornado.ioloop.IOLoop.instance()

application = tornado.web.Application([
    (r"/", HomeHandler),
    (r"/step1", Step1Handler),
    (r"/step2", Step2Handler),
    (r"/step3", Step3Handler, dict(executor=executor)),
    (r"/step4", Step4Handler, dict(io_loop=io_loop, executor=executor)),
    (r"/step5", Step5Handler),
    (r"/step6", Step6Handler),
    (r"/step7", Step7Handler),
    (r"/step8", Step8Handler),
])

if __name__ == "__main__":
    application.listen(5000)
    io_loop.start()