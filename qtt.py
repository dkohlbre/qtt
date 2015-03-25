#!/usr/bin/python
import argparse
import subprocess
import string

HOST_C_FILE = "timer.c"

def print_info(s):
    print "[QTT] "+s

def print_unimp(fn):
    print_info(fn+" is unimplemented.")

def replace_file(fin,fout,reps):
    fi = open(fin,'r')
    fo = open(fout,'w')

    for l in fi:
        for (t,r) in reps:
            if t in l:
                l = l.replace(t,r)
        fo.write(l)
    fi.close()
    fo.close()

class QTTvar:
    def __init__(self,s):
        self.s = s

class QTT:
    all_add_gcc_files =[]
    all_includes = ""
    all_tests = ""
    all_testcalls = ""
    temp_file = ""
    testcount = 0
    functions = {}
    setup = ""
    temp_file = "/tmp/qtt_tmp.c"

    def gcc_build(self):
        replace_file(HOST_C_FILE,self.temp_file,[
            ("INCLUDES_HERE",self.all_includes),
            ("FUNCTIONS_HERE", "\n".join(self.functions.values())),
            ("TESTFUNCTIONS",self.all_tests),
            ("SETUP", self.setup),
            ("TESTRUNS",self.all_testcalls)])

        gccstring = "gcc -O -std=c99 -o a.qtt -I. -L. "
        for f in self.all_add_gcc_files:
            if f != "":
                if f[-2:] == '.c':
                    gccstring += "--include "+f+" "
                elif f[-3:] == ".so":
                    gccstring += f+" "
                elif f[:2] == "-l":
                    gccstring += f+" "
                else:
                    print_unimp("File type:"+f)
                    return -1

        gccstring +=self.temp_file
        proc = subprocess.Popen(gccstring,shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)

        while proc.returncode == None:
            (stdout,stderr) = proc.communicate()
            if stdout is not None or stderr is not None:
                for l in stdout.split('\n'):
                    if l != '':
                        print "[GCC] "+l
                for l in stderr.split('\n'):
                    if l != '':
                        print "[GCC] "+l

        if proc.returncode < 0:
            print_info("Building failed! See "+self.temp_file)
        elif proc.returncode > 0:
            print_info("Building has problems...")
        return proc.returncode

    def extract_c_data(self,cfunction,includefiles):
        addfile = ""
        if ":" in cfunction:
            f = cfunction.split(':')[1]
            if f [-2:] == '.c':
                addfile = f
            elif f [-3:] == '.so':
                addfile = f
            else:
                print_info("I don't know how to add file:\""+s+"\"")
                return -1
            cfunction = cfunction.split(':')[0]

        includes_s = ""
        if includefiles != "":
            for i in includefiles.split(','):
                if "\"" not in i:
                    if i[-2:] != ".h":
                        includes_s += "#include <"+i+".h>\n"
                    else:
                        includes_s += "#include <"+i+">\n"
                else:
                    includes_s += "#include "+i+"\n"

        return (cfunction,addfile,includes_s)

    def arg_to_string(self,a):
        if type(a) is str:
            return a
        elif isinstance(a,QTTvar):
            return a.s
        else:
            return str(a)

    def add_setup(self, setup):
        self.setup += setup + "\n"

    def add_include(self,includefiles):
        includes_s = ""
        if includefiles != "":
            for i in includefiles.split(','):
                if "\"" not in i:
                    if i[-2:] != ".h":
                        includes_s += "#include <"+i+".h>\n"
                    else:
                        includes_s += "#include <"+i+">\n"
                else:
                    includes_s += "#include "+i+"\n"
        self.all_includes += includes_s

    def add_library(self,libfiles):
        self.all_add_gcc_files.append(libfiles)

    # add a c function.
    def add_function(self, fname, function):
        self.functions[fname] = function

    def make_func(self, num, ret_s, types_s, typedargs_s, args_s):
        # C test function
        # double __run_test(RETTYPE (*function) (RAWTYPES),TYPEDARGS){
        #   int ctr = 0;
        #   uint8_t real = 0;
        #   uint64_t st;
        #   uint64_t end;
        #   uint64_t offset;
        #  runme:
        #   st = rdtscp();
        #   /* Offset for running the loop and rdtscp */
        #   for(ctr=0;ctr<PERF_ITRS;ctr++){
        #   }
        #   end = rdtscp();
        #   offset = end-st;
        #   st = rdtscp();
        #   for(ctr=0;ctr<PERF_ITRS;ctr++){
        #     (*function)(REALARGS);
        #   }
        #   end = rdtscp();
        #   if(real == 0){ real = 1; goto runme;}
        #   /* Run everything for real, previous was just warmup */
        #   return (end-st-offset)/(float)PERF_ITRS;
        # }

        functext = "double __attribute__((noinline)) __run_test_"+str(num)+"("+ret_s+" (*function) ("+types_s+"),"+typedargs_s+"){\n"
        functext +="  int ctr = 0;\n"
        functext +="  uint8_t real = 0;\n"
        functext +="  uint64_t st;\n"
        functext +="  uint64_t end;\n"
        functext +="  uint64_t offset;\n"
        functext +=" runme:\n"
        functext +="  st = rdtscp();\n"
        functext +="  /* Offset for running the loop and rdtscp */\n"
        functext +="  for(ctr=0;ctr<PERF_ITRS;ctr++){\n"
        functext +="  }\n"
        functext +="  end = rdtscp();\n"
        functext +="  offset = end-st;\n"
        functext +="  st = rdtscp();\n"
        functext +="  for(ctr=0;ctr<PERF_ITRS;ctr++){\n"
        functext +="    (*function)("+args_s+");\n"
        functext +="  }\n"
        functext +="  end = rdtscp();\n"
        functext +="  if(real == 0){ real = 1; goto runme;}\n"
        functext +="  /* Run everything for real, previous was just warmup */\n"
        functext +="  return (end-st-offset)/(float)PERF_ITRS;\n"
        functext +="}\n"
        return functext



    def c_snippet(self,cfunction,typestring,arglist,setup,testnum):

        ret_s = typestring.split('(')[0]
        types_s = typestring.split('(')[1].split(')')[0]
        argnames = map(chr, range(0x61, 0x61+(len(types_s.split(',')))))
        typedargs_s = ''.join([x+" "+y+',' for (x,y) in zip(types_s.split(','),argnames)])[:-1]
        args_s = ''.join([x+"," for x in argnames])[:-1]

        # generate tests
        testruns_s = ''
        if setup != "":
            testruns_s += setup+"\n"
        # find longest args
        m_len = reduce(lambda a,v: max(len(str(v)),a),arglist,0)+5

        for args in arglist:
            arg_string = ""
            if type(args) is tuple:
                for a in args:
                    arg_string += self.arg_to_string(a)+","
            else:
                arg_string = self.arg_to_string(args)+" "

            printable_arg_string = arg_string[:-1].replace('\"','\\"')
            testruns_s += "printf(\""+cfunction+" "+printable_arg_string
            testruns_s += ' '*(m_len-len(printable_arg_string)+2)+"%f\\n\","
            testruns_s +="__run_test_"+str(testnum)+"("+cfunction+","+arg_string[:-1]+"));\n"

        return (testruns_s,self.make_func(testnum, ret_s, types_s, typedargs_s, args_s))


    def add_c_test(self,cfunction,typestring,arglist,libfiles="",includefiles="",tmpfile="/tmp/qtt_tmp.c",setup_string=""):

        self.all_add_gcc_files.append(libfiles)
        self.temp_file = tmpfile

        (cfun,addfile,inc) = self.extract_c_data(cfunction,includefiles)
        self.all_add_gcc_files.append(addfile)
        self.all_includes += inc

        (tests,funtext) = self.c_snippet(cfun,typestring,arglist,setup_string,self.testcount)
        self.testcount +=1
        self.all_tests += funtext
        self.all_testcalls += tests

    def add_asm_test(self, fname, arglist, assembly, outputs, inputs, clobbers, tmpfile="/tmp/qtt_tmp.c"):
        (tests, funtext) = self.asm_snippet(fname, arglist, assembly, outputs, inputs, clobbers, self.testcount)
        self.testcount+=1

        self.all_tests += funtext + "\n"
        self.all_testcalls += tests + "\n"

    def asm_snippet(self, fname, arglist, assembly, outputs, inputs, clobbers, testnum):

        # Make single-letter names for the function arguments
        input_names  = ["in"  + l for l,i in zip(string.ascii_letters, inputs)]
        output_names = ["out" + l for l,i in zip(string.ascii_letters, outputs)]

        types     = ", ".join(["int64_t"        for i in range(len(input_names))])
        typedargs = ", ".join(["int64_t %s"%(s) for s in input_names])
        argnames  = ", ".join(["%s"%(s)         for s in input_names])

        output_vars = "\n    ".join(["int64_t %s;"%(s) for s in output_names])

        output_constraints = ", ".join(['"%s" (%s)'%(const, name)
            for const,name in zip(outputs,output_names)])
        input_constraints = ", ".join(['"%s" (%s)'%(const, name)
            for const,name in zip(inputs,input_names)])
        clobbers_constraints = ", ".join(['"%s"'%(name)
            for name in clobbers])

        test_function_name = "test_%s"%(fname)

        asm = """__asm__ volatile(" %s "
        : %s
        : %s
        : %s); """ %( assembly, output_constraints, input_constraints, clobbers_constraints)

        function_type = "volatile int64_t"

        function = r"""
%s %s(%s) {
    %s
    %s
    return %s;
}""" %(function_type, test_function_name, typedargs, output_vars, asm, output_names[0])

        self.add_function(test_function_name, function)

        testruns = []
        for args in arglist:
            args = ", ".join([self.arg_to_string(a) + "LL" for a in args])

            testruns += [r"""printf("%s %-60s %%f\n", __run_test_%d(%s, %s));"""% \
              (fname, args, testnum, test_function_name, args)]

        return ("\n".join(testruns), self.make_func(testnum, function_type, types, typedargs, argnames))


def qtt_getargs():
    parser = argparse.ArgumentParser(description='Time pretty much anything in C.')

    parser.add_argument('typestring', metavar='typestring', type=str, default=None,
                        help='Headerfile style typestring ex: "int (uint8_t,char*)"')

    parser.add_argument('arglist', metavar='arglist', type=str, default="(0)",
                        help='List of arguments to try, comma separated tuples. ex: "(0,2),(5,3)"')

    parser.add_argument('-c', dest='cfunction', action='store',  metavar='C function',
                        type=str, default=None,
                        help='A C function to call, either in a header included or in a file with -f."\
                        "Or with a colon, ex: foo:testme.c')

    parser.add_argument('-f', dest='addfile', action='store',  metavar='filename',
                        type=str, default="",
                        help='C file to compile with, add this if it has a function you need.')

    parser.add_argument('-l', dest='libfile', action='store',  metavar='filename',
                        type=str, default="",
                        help='.so to link against. Can be specified in -c via :')

    parser.add_argument('-a', dest='asmcode', action='store',metavar='ASM snippet',
                        type=str, default=None,
                        help='A short x86_64 asm snippet. Can use imported functions.')

    parser.add_argument('-i','--include', dest='includefiles', action='store',metavar='list',
                        type=str, default="",
                        help='Comma separated list of #includes required to build')

    parser.add_argument('--tmpfile', dest='tmpfile', action='store',metavar='name',
                        type=str, default="/tmp/qtt_gen.c",
                        help='Temporary C file passed into gcc, defaults to in /tmp')


    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = qtt_getargs()

    timer = QTT()

    if args.cfunction != None:
        try:
            arglist = eval('['+args.arglist+']')
        except:
            print_info("FATAL: Cannot parse arglist argument as python tuples!")
        timer.add_c_test(tmpfile=args.tmpfile,cfunction=args.cfunction,includefiles=args.includefiles,typestring=args.typestring,arglist=arglist,libfiles=args.libfile)
        r = timer.gcc_build()
    elif args.asmcode != None:
        r = timer.asm_snippet(args)
    if r == 0:
        print_info("Seems like everything worked! Run ./a.qtt")
