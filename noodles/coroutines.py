"""
We use coroutines to handle the communication between the scheduler and
the different workers. Some of the functionality here may be reinventing
some batteries. If so, submit an issue and teach me the idiomatic way!
"""

from queue import Queue
from functools import wraps


def coroutine_sink(f):
    """
    A sink should be send `None` first, so that the coroutine arrives
    at the `yield` position. This wrapper takes care that this is done
    automatically when the coroutine is started.
    """
    @wraps(f)
    def g(*args, **kwargs):
        sink = f(*args, **kwargs)
        sink.send(None)
        return sink

    return g


class IOQueue:
    """
    We mock a server/client situation by creating a pipe object that
    recieves items in a sink, stores them in a synchronised queue
    object, and sends them out again in source. Any number of threads
    or objects may create a sink or source. All pool to the same Queue.

    This implementation serves as an example and to glue the local threaded
    runner together. On one side there is a worker pool, taking jobs from one
    of these queues. On the other side there is the controller taking results
    from a second pipe, the snake biting its tail.
    """
    def __init__(self, blocking=True):
        self.Q = Queue()
        self.blocking = blocking

    @coroutine_sink
    def sink(self):
        while True:
            r = yield
            self.Q.put(r)

    def source(self):
        while True:
            v = self.Q.get()
            yield v
            self.Q.task_done()

            # try:
            #     v = self.Q.get(self.blocking)
            #     yield v
            #     self.Q.task_done()
            # except:
            #     yield

    # def wait(self):
    #     self.Q.join()


class Connection:
    """
    Combine a source and a sink. These should represent the IO of
    some object, probably a worker.
    """
    def __init__(self, source, sink, name=None):
        self.source = source
        self.sink = sink
        self.name = name if name else "connection-{0:0x}".format(id(self))

    def setup(self):
        src = self.source()
        snk = self.sink()
        return src, snk


class QueueConnection(Connection):
    """
    Takes an input and output queue, and conceptually links them,
    returning a pair containing a source from the input queue
    and a sink to the output queue.
    """
    def __init__(self, d_in, d_out):
        super(QueueConnection, self).__init__(d_in.source, d_out.sink)


def patch(source, sink):
    """
    Create a direct link between a source and a sink.
    """
    for v in source:
        sink.send(v)
