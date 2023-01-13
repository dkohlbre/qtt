#!/usr/bin/python3
import subprocess
import collections


def print_info(s):
    print("[QTT] " + s)


def print_unimp(fn):
    print_info(fn + " is unimplemented.")


class QTTvar:

    def __init__(self, name, setup=None):
        self.name = name
        self.setup = setup

    def __call__(self, *args, **kwordargs):
        if self.setup is None:
            return QTTvaruse(self.name, self.setup)
        else:
            return QTTvaruse(self.name, self.setup(*args, **kwordargs))


class QTTvaruse:

    def __init__(self, name, setup):
        self.name = name
        self.setup = setup


class QTTvardef:

    def __init__(self, name, typestr, declare, glbl):
        self.name = name
        self.typestr = typestr
        self.declare = declare
        self.glbl = glbl


class QTTtest:

    def __init__(self, func, harness, args, deps=None, setup=""):
        self.func = func
        self.args = args
        self.setup = setup
        self.harness = harness


def vectorver(thing):
    if isinstance(thing, collections.abc.Iterable) and type(thing) is not str:
        if len(thing) == 1 and thing[0] is None:
            return []
        return thing
    if thing is None:
        return []
    return (thing,)


def cstr(string):
    if string == "":
        return "\n"
    if string[-1] == "\n":
        if string[-2] == ";":
            return string
        return string[:-1] + ";\n"
    elif string[-1] == ";":
        return string + "\n"
    else:
        return string + ";\n"


class QTT:
    def __init__(self, tmpfile="/tmp/qtt_tmp.c",
                 outfile="a.qtt", iterations=200000, use_rdtscp=True):
        self.tmpfile = tmpfile
        self.outfile = outfile
        self.iterations = iterations
        self.testruns = []
        self.libs = []
        self.includes = []
        self.harnesses = []
        self.varlist = []
        self.setup = ""
        # TODO detect if rdtscp is available, use this for now
        self.use_rdtscp = use_rdtscp

    def build(self, cc="gcc"):
        output = QTTgenerate_includes(self.includes)
        output += QTTgenerate_magic(
            self.iterations, self.use_rdtscp, self.varlist)
        output += QTTgenerate_harnesses(self.harnesses)
        # TODO setup?
        output += QTTgenerate_main(self.testruns, self.setup, self.varlist)
        ftmp = open(self.tmpfile, 'w')
        ftmp.write(output)
        ftmp.close()

        gccstring = "{CC} -O -std=gnu99 -o {OUTF} -I. -L. {TMP} {LIBS}".format(
            CC=cc,
            OUTF=self.outfile,
            TMP=self.tmpfile,
            LIBS=' '.join(self.libs)
        )
        print_info("Build command: " + gccstring)
        proc = subprocess.Popen(gccstring, shell=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        while proc.returncode is None:
            (stdout, stderr) = proc.communicate()
            if stdout is not None or stderr is not None:
                for line in stdout.splitlines():
                    if line != '':
                        print("[GCC] " + line)
                for line in stderr.splitlines():
                    if line != '':
                        print("[GCC] " + line)

        if proc.returncode < 0:
            print_info("Building failed! See " + self.tmpfile)
        elif proc.returncode > 0:
            print_info("Building has problems...")
        else:
            print_info("Building succeeded, run " + self.outfile)

    def add_setup(self, setup):
        self.setup += cstr(setup)

    def run(self):
        results = {}
        err = False
        proc = subprocess.Popen("./" + self.outfile, shell=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        while proc.returncode is None:
            (stdout, stderr) = proc.communicate()
            if stdout is not None and not err:
                for l in stdout.split('\n'):
                    if "function      cycles" in l or "========" in l:
                        continue
                    if len(l.split()) == 3:
                        (fn, args, val) = l.split()
                        if fn not in results:
                            results[fn] = {}
                        results[fn][args] = float(val)
            if stderr is not None:
                if len(stderr) > 1:
                    err = True
        return results, err

    # Start Internal Functions#######
    def add_harness(self, typestring):
        if typestring in self.harnesses:
            return self.harnesses.index(typestring)
        else:
            self.harnesses.append(typestring)
            return len(self.harnesses) - 1

    # End Internal Functions#######

    def add_library(self, libfiles):
        for lib in vectorver(libfiles):
            if lib[-3:] != ".so" and lib[:2] != "-l":
                print_unimp("File type:" + lib)
                exit(1)
            self.libs.append(lib)

    def add_include(self, *includes):
        for inc in vectorver(includes):
            self.includes.append(inc)

    def new_var(self, typestring, name, setup=None, declare=None, glbl=False):
        self.varlist.append(QTTvardef(name, typestring, declare, glbl))
        return QTTvar(name, setup)

    def add_c_test(self, cfunc, typestring, args,
                   libfiles=None, includefiles=None, setup=None):

        # Vectorization is comfy and easy to wear
        if isinstance(cfunc, collections.abc.Iterable) and type(cfunc) is not str:
            [self.add_c_test(c, typestring, args,
                             libfiles, includefiles, setup)
             for c in cfunc]
            return

        # We need one of the terrible harnesses to run the function
        harness = self.add_harness(typestring)

        # Generate test instances for each arg set
        for argt in args:
            self.testruns.append(
                QTTtest(cfunc, harness, vectorver(argt), setup))

        # Handle libfiles and includes
        self.add_library(libfiles)
        self.add_include(includefiles)


def QTTgenerate_includes(includes):
    string = '''#include <stdio.h>
    #include <stdint.h>
    #include <inttypes.h>
    #include <string.h>
    #include <stdlib.h>
'''
    for i in includes:
        if "\"" not in i and "<" not in i:
            if i[-2:] != ".h" and i[-2:] != ".c":
                string += "#include <" + i + ".h>\n"
            else:
                string += "#include <" + i + ">\n"
        else:
            string += "#include " + i + "\n"

    return string


def QTTgenerate_magic(iterations, use_rdtscp, varlist):
    # See
    # http://www.intel.com/content/www/us/en/embedded/training/ia-32-ia-64-benchmark-code-execution-paper.html
    string = '''#define PERF_ITRS ''' + str(iterations)
    string += '''
static inline uint64_t rdtscp_start(){
  uint64_t v;'''
    if use_rdtscp:
        string += '''
  __asm__ volatile("cpuid;"
                   "rdtsc;"
                   "shl $32,%%rdx;"
                   "or %%rdx,%%rax;"
                   : "=a" (v)
                   :
                   : "%rcx","%rdx");

  return v;
}'''

    else:
        string += '''
  __asm__ volatile("cpuid;"
                   "rdtsc;"
                   "shl $32,%%rdx;"
                   "or %%rdx,%%rax;"
                   : "=a" (v)
                   :
                   : "%rcx","%rdx");

  return v;
}'''

    string += '''
static inline uint64_t rdtscp_stop(){
  uint64_t v;'''
    if use_rdtscp:
        string += '''
  __asm__ volatile("rdtscp;"
                   "shl $32,%%rdx;"
                   "or %%rdx,%%rax;"
                   "mov %%rax,%0;"
                   : "=r" (v)
                   :
                   : "%rcx","%rdx");

  return v;
}'''

    else:
        string += '''
  __asm__ volatile("cpuid;"
                   "rdtsc;"
                   "shl $32,%%rdx;"
                   "or %%rdx,%%rax;"
                   : "=a" (v)
                   :
                   : "%rcx","%rdx");

  return v;
}'''
    for v in varlist:
        if v.declare is not None and not v.glbl:
            string += cstr(v.declare)
        else:
            string += v.typestr + " " + v.name + ";\n"

    return string


def QTTgenerate_main(tests, setup, varlist):
    string = '''int main(int argc, char* argv[]){
  printf(    "function ""     cycles\\n");
  printf(    "====================\\n");
'''
    string += setup

    for v in varlist:
        if v.declare is not None and not v.glbl:
            string += cstr(v.declare)
        else:
            string += v.typestr + " " + v.name + ";\n"

    for t in tests:
        string += QTTgenerate_test_string(t)

    string += "}"
    return string


def QTTgenerate_harnesses(typestrings):
    string = ""
    for (i, ts) in enumerate(typestrings):
        string += QTTgenerate_harness(ts, i)
    return string


def QTTgenerate_harness(typestring, num):
    ret_s = typestring.split('(')[0]
    types_s = typestring.split('(')[1].split(')')[0]
    argnames = list(
        map(chr, list(range(0x61, 0x61 + (len(types_s.split(',')))))))
    typedargs_s = ''.join(
        ["{X} {Y},".format(X=x, Y=y)
         for (x, y) in zip(types_s.split(','), argnames)])[:-1]
    args_s = ''.join([x + "," for x in argnames])[:-1]

    functext = """
double __attribute__((noinline)) __run_test_{NUM}({RET} (*function) ({TYPES}),{TYPEDARGS}){{
  int ctr = 0;
  uint8_t real = 0;
  uint64_t st;
  uint64_t end;
  uint64_t offset;
 runme:
  st = rdtscp_start();
  /* Offset for running the loop and rdtscp */
  for(ctr=0;ctr<PERF_ITRS;ctr++){{
  }}
  end = rdtscp_stop();
  offset = end-st;
  st = rdtscp_start();
  for(ctr=0;ctr<PERF_ITRS;ctr++){{
    (*function)({ARGS});
  }}
  end = rdtscp_stop();
  if(real == 0){{ real = 1; goto runme;}}
  /* Run everything for real, previous was just warmup */
  return (end-st-offset)/(float)PERF_ITRS;
}}
""".format(NUM=str(num),
           RET=ret_s,
           TYPES=types_s,
           TYPEDARGS=typedargs_s,
           ARGS=args_s)

    return functext


def QTTgenerate_test_string(test):
    setup = test.setup

    argstring = ""
    for v in test.args:
        if isinstance(v, QTTvaruse):
            if v.setup is not None:
                setup += cstr(v.setup)
            argstring += "," + v.name
        elif type(v) is str:
            argstring += ",\"" + v + "\""
        else:
            argstring += "," + str(v)

    string = "printf(\"" + test.func + " " + argstring[1:].replace('\"', '\\"')
    string += ' ' * (len(argstring) + 2) + "%f\\n\","

    string += "__run_test_" + str(test.harness) + "(" + test.func + argstring
    string += "));\n"
    return setup + string
