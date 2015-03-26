#!/usr/bin/python
from qtt import QTT


# Create a new QTT instance
timer = QTT()

# Add the headers and librarys we need for math operations
timer.add_include("math.h")
# Note: this could also be "/usr/lib/x86_64-linux-gnu/libm.so"
timer.add_library("-lm")

# Add a basic test
# This will run and return individual timings for:
#   floor(10.0)
#   floor(22.3)
#   floor(50.6)
timer.add_c_test(cfunc="floor",typestring="double (double)",args=[10.0,22.3,50.6])


# Add a list of tests with the same typestring and args
function_list = "log","log2","log10"
timer.add_c_test(cfunc=function_list,typestring="double (double)",args=[10.0,22.3,50.6])

# Add a function to test that takes two arguments
timer.add_c_test(cfunc="pow",typestring="double (double,double)",args=[(8,10),(10,10)])

# Create a new variable that we can use as a test argument
#  Setup specifies how to setup the variable before a test, it should be a function that returns
#  a valid-ish C string.
handyvar = timer.new_var(typestring="double",name="handyvar",setup=lambda val:"handyvar = "+str(val))

# Use it in a test
# This test will result in 3 tests being run
# 1)handyvar = 33.2;
#   ceil(handyvar);
# 2)ceil(56.5);
# 3)handyvar = 9.0;
#   ceil(handyvar);
timer.add_c_test(cfunc="ceil",typestring="double (double)",args=[handyvar(33.2),56.5,handyvar(9.000)])


# Build the test
timer.build()

# Now go run the locally created a.qtt!
