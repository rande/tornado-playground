__author__ = 'rande'

"""
references
 - https://wiki.python.org/moin/Generators

"""

def simple_generator():
    """
    Simple generator that will return 1 value
    """
    yield "simple_generator 1"

for i in simple_generator():
    print i

print "---"

def loop_generator(max):

    inc = 0
    for i in xrange(0, max):
        sent = yield "loop_generator %d" % (inc + i)

        print "sent", sent
        print "inc", inc

        if sent and inc == 0:
            inc = int(sent)

for i in loop_generator(10):
    print i

print "---"

g = loop_generator(100)
print g

next(g)
g.send(100)

print next(g)