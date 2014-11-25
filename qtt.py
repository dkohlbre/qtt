#!/usr/bin/python
import argparse
import subprocess

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

class QTT:
    all_add_gcc_files =""
    all_includes = ""
    all_tests = ""
    all_testcalls = ""
    temp_file = ""

    def gcc_build(self):
        gccstring = "gcc -O -fforce-addr -std=c99 -o a.qtt -I. -L. "
        for f in self.all_add_gcc_files:
            if f != "":
                if f[-2:] == '.c':
                    gccstring += "--include "+f+" "
                elif f[-3:] == ".so":
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
        if includes_s != "":
            for i in includefiles.split(','):
                if "\"" not in i:
                    if i[-2:] != ".h":
                        includes_s += "#include <"+i+".h>\n"
                    else:
                        includes_s += "#include <"+i+">\n"
                else:
                    includes_s += "#include "+i+"\n"

        return (cfunction,addfile,includes_s)

    def c_snippet(self,cfunction,typestring,arglist,testnum):

        ret_s = typestring.split('(')[0]
        types_s = typestring.split('(')[1].split(')')[0]
        argnames = map(chr, range(0x61, 0x61+(len(types_s.split(',')))))
        typedargs_s = ''.join([x+" "+y+',' for (x,y) in zip(types_s.split(','),argnames)])[:-1]
        args_s = ''.join([x+"," for x in argnames])[:-1]

        # generate tests
        testruns_s = ''
        tests = arglist.split('),(')

        # find longest args
        m_len = reduce(lambda a,v: min(len(v),a),tests)

        for a in tests:
            t = a.replace('(','').replace(')','')
            testruns_s += "printf(\""+cfunction+" ("+t.replace('"','\\"')+")"+' '*(m_len-len(t)+2)+"%f\\n\","
            testruns_s +="__run_test_"+str(testnum)+"("+cfunction+","+t+"));\n"

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

        functext = "double __run_test_"+str(testnum)+"("+ret_s+" (*function) ("+types_s+"),"+typedargs_s+"){\n"
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
        functext +="}"


        return (testruns_s,functext)


    def add_c_test(self,tmpfile,cfunction,includefiles,typestring,arglist):

        self.temp_file = tmpfile

        (cfun,addfile,inc) = self.extract_c_data(cfunction,includefiles)
        self.all_add_gcc_files += addfile
        self.all_includes += inc

        (tests,funtext) = self.c_snippet(cfun,typestring,arglist,0)
        self.all_tests += funtext
        self.all_testcalls += tests

        replace_file(HOST_C_FILE,self.temp_file,[
            ("INCLUDES_HERE",self.all_includes),
            ("TESTFUNCTIONS",self.all_tests),
            ("TESTRUNS",self.all_testcalls)])

        return self.gcc_build()

    def asm_snippet(self,args):
        print args.asmcode
        print_unimp("ASM snippets")


def getargs():
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
    args = getargs()

    timer = QTT()

    if args.cfunction != None:
        r = timer.add_c_test(args.tmpfile,args.cfunction,args.includefiles,args.typestring,args.arglist)
    elif args.asmcode != None:
        r = asm_snippet(args)
    if r == 0:
        print_info("Seems like everything worked! Run ./a.qtt")
