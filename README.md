Tornado Playground
==================

00-python-basis.py
------------------

Some python basis about yield

01-sync-process.py
------------------

Playing with Blocking RequestHandler (and how to make them non blocking)

 - open 3 terminals
 - start ``python 01-sync-process.py``
 - on others terminals: ``curl http://localhost:5000/step[1-X]`` to test each step

02-async-process.py
-------------------

Playing with Non Blocking RequestHandler (by using asynchronous library)

 - open 3 terminals
 - start ``python 02-async-process.py``
 - on others terminals: ``curl http://localhost:5000/step[1-X]`` to test each step
