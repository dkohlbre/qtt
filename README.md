 Quick, Time This
==================
Time C stuff, really accurately, really easily.


Example Usage
-------------
from qtt import QTT

timer = QTT()

timer.add_c_test(cfunc="atof",typestring="double (const char*)",args=["343","46445.34324"])

timer.build()


See sse_example.py for a detailed example

What?
======
Time your (or standard) C functions!

This is terrible!
-----------------
Duh. its python code that generates C code and shoves it into gcc, what did you expect?

How do I use it?
----------------
It doesn't have install yet, run it from the checkout directory.

It should work on all x86_64 systems with RDTCSP as an available instruction.

Versions
========
This is version 2.0, its missing some features:
* Command line usage
* Good documentation
* A story for doing x86 asm tests easily
