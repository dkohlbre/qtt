 Quick, Time This
==================
Time C stuff, really accurately, really easily.


Example Usage
-------------
./qtt.py -c atof "double (const char*)" '("1"),("100000000.23242")'

./qtt.py -c pow -i math.h -l /usr/lib/x86_64-linux-gnu/libm.so "double (double,double)" '(1,2),(5,4)'

Or, from python:

from qtt import QTT

timer = QTT()

timer.add_c_test(cfunction="atof",typestring="double (const char*)",arglist=[("343"),("46445.34324")])

timer.gcc_build()


What?
======
Time your (or standard) C functions!

This is terrible!
-----------------
Duh. its python code that generates C code and shoves it into gcc, what did you expect?

How do I use it?
----------------
It doesn't have install yet, run it from the checkout directory.

It should work on all x86_64 systems.

./qtt.py --help is pretty helpful
