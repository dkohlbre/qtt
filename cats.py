#!/usr/bin/python
import argparse
import subprocess

HOST_C_FILE = "timer.c"

def print_info(s):
    print "[CATS] "+s

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

def gcc_build(args):
    gccstring = "gcc -O -fforce-addr -std=c99 -o Cats_out -I. -L. "
    if args.addfile != '':
        gccstring += "--include "+args.addfile+" "
    if args.libfile != '':
        gccstring += args.libfile+" "
    gccstring +=args.tmpfile
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
        print_info("Building failed!")
    elif proc.returncode > 0:
        print_info("Building has problems...")
    return proc.returncode

def c_snippet(args):

    if ":" in args.cfunction:
        f = args.cfunction.split(':')[1]
        if f [-2:] == '.c':
            args.addfile = f
        elif f [-3:] == '.so':
            args.libfile = f
        else:
            print_info("I don't know how to add file:\""+s+"\"")
            return -1
        args.cfunction = args.cfunction.split(':')[0]

    ret_s = args.typestring.split('(')[0]
    types_s = args.typestring.split('(')[1].split(')')[0]
    argnames = map(chr, range(0x61, 0x61+(len(types_s.split(',')))))
    typedargs_s = ''.join([x+" "+y+',' for (x,y) in zip(types_s.split(','),argnames)])[:-1]
    args_s = ''.join([x+"," for x in argnames])[:-1]

    includes_s = ""
    if includes_s != "":
        for i in args.includefiles.split(','):
            if "\"" not in i:
                if i[-2:] != ".h":
                    includes_s += "#include <"+i+".h>\n"
                else:
                    includes_s += "#include <"+i+">\n"
            else:
                includes_s += "#include "+i+"\n"
    print includes_s
    # generate tests
    testruns_s = ''
    tests = args.arglist.split('),(')
    for a in tests:
        t = a.replace('(','').replace(')','')
        testruns_s += "printf(\""+args.cfunction+" ("+t.replace('"','\\"')+")      %f\\n\", __run_test("+args.cfunction+","+t+"));\n"

    # Build a C file
    replace_file(HOST_C_FILE,args.tmpfile,[
        ("INCLUDES_HERE",includes_s),
        ("RETTYPE",ret_s),
        ("RAWTYPES",types_s),
        ("TYPEDARGS",typedargs_s),
        ("REALARGS",args_s),
        ("TESTRUNS",testruns_s)])

    #Build tmpfile
    return gcc_build(args)


def asm_snippet(args):
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
                        type=str, default="/tmp/Cats_gen.c",
                        help='Temporary C file passed into gcc, defaults to in /tmp')


    args = parser.parse_args()
    return args


args = getargs()

if args.cfunction != None:
    c_snippet(args)
elif args.asmcode != None:
    asm_snippet(args)
