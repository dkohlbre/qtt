 Quick, Time This
==================
Time C stuff, really accurately, really easily.


Example Usage
-------------
./qtt.py -c atof "double (const char*)" '("1"),("100000000.23242")'

./qtt.py -c pow -i math.h -l /usr/lib/x86_64-linux-gnu/libm.so "double (double,double)" '(1,2),(5,4)'

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

Support for using QTT as a library should be ready soon.

./qtt.py --help is pretty helpful
