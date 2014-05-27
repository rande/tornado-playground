import tornado.ioloop
import tornado.web
import tornado.gen
import tornado.process
import tornado.concurrent
import tornado.httpclient

from futures import ThreadPoolExecutor

import time, datetime

class HomeHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Let's start with a blocking code: <a href='/step1'>Step 1</a><br />")
        self.write("End request!")

class Step1Handler(tornado.web.RequestHandler):
    def heavy_blocking_method(self):
        time.sleep(5)

    def get(self):
        """
        This code will block because time.sleep is blocking the process
        """
        self.heavy_blocking_method()

        self.write("You wait 5 seconds and you lock the ioloop<br/>")
        self.write("Try to start two simultaneous connections, the second one will last for 10s. <br />")

        self.write("Let's try to not lock the ioloop: <a href='/step2'>Step 2</a><br />")
        self.write("End request!")

class Step2Handler(tornado.web.RequestHandler):

    def heavy_blocking_method(self):
        time.sleep(5)

    @tornado.web.asynchronous
    def get(self):
        """
        This code will still block the ioloop because time.sleep is blocking event with the
        @tornado.web.asynchronous annotation.
        """
        self.heavy_blocking_method()

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
    def heavy_blocking_method(self):
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
        self.heavy_blocking_method()

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
    def heavy_blocking_method(self):
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
        self.heavy_blocking_method(callback=self.complete)

        self.write("You wait 5 seconds and you don't block the ioloop<br/>")
        self.write("Try to start two simultaneous connections, the second one will last for 5s. too ...  <br />")

    def complete(self, returned_value):
        self.write("The sleep method also return a message for you: %s" % returned_value)

        self.write("Let's try to not block the ioloop: <a href='/step5'>Step 5</a><br />")
        self.write("End request!")

        print "End request!"

        self.finish()

class Step5Handler(tornado.web.RequestHandler):
    def heavy_blocking_method(self):
        """
        The tornado.process.Subprocess class is async so the call will not block. The callback
        will close the connection when the response will be known.
        """
        print "Start process"
        p = tornado.process.Subprocess(["sleep", "5"])
        p.set_exit_callback(self.complete)
        print "Write output"

    @tornado.web.asynchronous
    def get(self):
        self.heavy_blocking_method()

        self.write("You wait 5 seconds and you don't block the ioloop<br/>")
        self.write("Try to start two simultaneous connections, the second one will last for 5s. too ...  <br />")

    def complete(self, status_code):
        self.write("Let's try to not block the ioloop: <a href='/step6'>Step 6</a><br />")

        self.write("End request!")

        print "End request!"

        self.finish()


class Step6Handler(tornado.web.RequestHandler):
    def initialize(self, io_loop=None):
        self.io_loop = io_loop

    @tornado.gen.coroutine
    def heavy_blocking_method(self):
        print "start yielding"

        task = yield tornado.gen.Task(self.io_loop.add_timeout, datetime.timedelta(seconds=5))

        print "Task", task

    @tornado.web.asynchronous
    def get(self):

        future = self.heavy_blocking_method(callback=self.complete)

        print future

        return future

    def complete(self, result):
        self.write("Let's try to not block the ioloop: <a href='/step9'>Step 9</a><br />")

        self.write("End request!")

        print "End request!"

        self.finish()

class Step7Handler(tornado.web.RequestHandler):
    """
    This code will block the IO loop, because the coroutine annotation only works with
    async lib, like the HTTPClient (see 02-async-process.py)
    """
    def initialize(self, io_loop=None, executor=None):
        self.io_loop = io_loop
        self.executor = executor

    def heavy_blocking_method(self, callback):
        print "start sleep"

        print "callback", callback

        time.sleep(5)

        print "End sleep"

        callback("hello world!!")

    @tornado.gen.coroutine
    def get(self):

        print "Start request"

        result = yield tornado.gen.Task(self.heavy_blocking_method)

        print "result", result

        self.write("Let's try to not block the ioloop: <a href='/step9'>Step 9</a><br />")

        self.write("End request!")

        print "End request!"

        self.finish()


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
    (r"/step6", Step6Handler, dict(io_loop=io_loop)),
    (r"/step7", Step7Handler, dict(io_loop=io_loop,  executor=executor)),
])

if __name__ == "__main__":
    application.listen(5000)
    io_loop.start()