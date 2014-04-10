#! /usr/bin/env python3

import getopt, sys, time, os, re, tempfile, json
from zlib import adler32

start_time = time.time()

# Some variables that can be changed through options
# -c gcc to change this
cxx = "xcrun clang++" # Compiler
# -k to change the linker (the linker is used in only one rule of the Makefile)
linker = cxx

# Where are the files
# change with -s some-dir, same for -o and -b
src_dir = "src"
obj_dir = "obj"
bin_dir = "bin"

# Default options passed to the compiler. You can pass more options or edit
# these as much as you want
# Use -D to supress these options (by these I mean all of the default_ variables"
# Add new options with -O "-Wall -Os"
default_options = "-Wall -Wextra -O2 -std=c++11 -stdlib=libc++"
options = ""

# Include directories default options
# Add new directories with -Isrc/
default_include = "-I"+src_dir
include = ""

# Here is the linking step, add any library using the -l-lGL -l-lBox2D
# BEWARE OF THE DOUBLE -l, this is because in OS X you use -framework OpenGL and not -lGL
# Remember you can use it this way too:
# -l "-lGL -lBox2D"
# Add dirs using -L/usrs/local/lib
# Don't add any -L here
default_link = "-L/usr/local/lib"
link = ""
libs = ""

# Trying with Linux and OS X gave me different result, though I was using the clang++
# compiler. Therefore I added this option so we can set specifically the options for
# the linking step.
default_link_opt = "-std=c++11 -stdlib=libc++"
link_opt = ""

# Extension of the files that will be compiled
# Change with -e cc
file_ext = "cpp"
obj_ext = "o"

# Colors. Enabled by default, use -C to disable it
colors = True

# Files that have a main function and therefore and therefore cannot be linked
# against others "mains"
exec_file = []
# list of the names in the same order
# if not specified then the basename without extension is used
exec_name = []

# Name of the Makefile
# Change with -M newName
makefile = "Makefile"

# Almost useless since this script is already quite verbose
verbose = False

# Used to display the progress of the compilation instead of the executed command
# Default is false
cmake_style = ""

c_red = "[0;31m"
c_blue = "[1;34m"
c_green = "[0;32m"
c_br_green = "[1;32m"
c_yellow = "[0;33m"
c_clean = "[0m"

# the help
def usage():
    print("usage: "+sys.argv[0]+" [-hfDvp] [-s|--src src-dir] [-o|--obj obj-dir] [-b|--bin bin-dir] [-c|--compiler compiler] [-k|--linker linker] [-O|--options \"compiler options\"] [-L link-dirs] [-l \"-lsome-lib -lother-lib\"] [-I include-dir] [-M|--makefile Makefile-name] [-e|--file-extension file-extension] [-E|--executable executable-source] [--executable-name output-name] [-N|--linker-options linker-options]\n\n\
  "+c_yellow+"-h, --help"+c_clean+"               Show this help.\n\
  "+c_yellow+"-D, --no-default"+c_clean+"         Supress the default options for -L, -I, -N and -O.\n\
  "+c_yellow+"-v, --verbose"+c_clean+"            Verbose mode: Show the dependencies for every file\n\
  "+c_yellow+"-p, --cmake-style"+c_clean+"        CMake style: Display a percentage instead of the command executed\n\
\n\
  If you change the compiler with the -c option but not the linker with the -k option, the linker is set to the compiler\n\
  Remember that the -l option requires you to add the -l to any lib as it is shown in the example. However it's the oposite for the -L and -I options which both add the -L and the -I before every argument. Therefore consider using a single -l option and multiple -I and -L options.\n\
\n\
Running without arguments is equivalent to this:\n\
  "+sys.argv[0]+" -D -s "+src_dir+" -o "+obj_dir+" -b "+bin_dir+" -c \""+cxx+"\" -O \""+default_options+"\" "+default_include+" "+default_link+" -e "+file_ext+" -M "+makefile+" -N \""+default_link_opt+"\"\n\
\n\
GitHub repo: https://github.com/posva/configure.py")

# Remove blanks at the begining
def remove_blank(s):
    if len(s) == 0:
        return s
    return s[1:] if s[0] == ' ' else s

# For printing
def good_msg(s):
    print(c_green+s+c_clean)
def error_msg(s):
    print(c_red+s+c_clean)
def warning_msg(s):
    print(c_yellow+s+c_clean)
def info_msg(s):
    print(c_blue+s+c_clean, end = '')


compiler_changed = False
linker_set = False

try:
    opts, args = getopt.getopt(sys.argv[1:], "pvhCs:o:b:c:k:DO:L:l:I:M:e:E:N:", ["help", "cmake-style", "no-colors", "src=", "obj=", "bin=", "file-extension=", "executable=", "executable-name=", "compiler=", "linker=", "options=", "no-default", "makefile=", "linker-options="])
except getopt.GetoptError as err:
    # print help information and exit:
        print(err) # will print something like "option -a not recognized"
        usage()
        sys.exit(2)
for o, a in opts:
    if o == "-v":
        verbose = True
    elif o in ("-h", "--help"):
        usage()
        sys.exit()
    elif o in ("-p", "--cmake-style"):
        cmake_style = True
    elif o in ("-C", "--no-colors"):
        colors = False
    elif o in ("-s", "--src"):
        if default_include == "-I"+src_dir:
            default_include = "-I"+a
        src_dir = a
    elif o in ("-b", "--bin"):
        bin_dir = a
    elif o in ("-o", "--obj"):
        obj_dir = a
    elif o == "-l":
        libs = a
    elif o == "-L":
        link += " -L"+a
    elif o in ("-e", "--file-extension"):
        file_ext = a
    elif o in ("-E", "--executable"):
        exec_file.append(a)
    elif o in ("--executable-name"):
        exec_name.append(a)
    elif o in ("-c", "--compiler"):
        cxx = a
        compiler_changed = True
    elif o in ("-k", "--linker"):
        linker = a
        linker_set = True
    elif o == "-I":
        include += " -I"+a
    elif o in ("-O", "--options"):
        options += " "+a
    elif o in ("-D", "--no-default"):
        default_options = ""
        default_include = ""
        default_link = ""
        default_link_opt = ""
    elif o in ("-M", "--makefile"):
        makefile = a
    elif o in ("-N", "--linker-options"):
        link_opt = a
    else:
        assert False, "unhandled option"

link = remove_blank(link)
include = remove_blank(include)
options = remove_blank(options)

# Change the linker if the compiler changed without specifying a new linker
if compiler_changed and not linker_set:
    linker = cxx

# COLORS!!!
if not colors:
    c_red = ""
    c_blue = ""
    c_green = ""
    c_br_green = ""
    c_yellow = ""
    c_clean = ""

# Function to recursively find directories
# This is used to find which directories need to be created in obj_dir
def find_dirs(top = '.'):
    if top == '.':
        l = os.listdir(top)
    else:
        l = [ top+'/'+i for i in os.listdir(top) if os.path.isdir(top+'/'+i)]
    i = 0
    while i < len(l):
        if not os.path.isdir(l[i]):
            l.pop(i)
        else:
            tmp = [ l[i]+'/'+j for j in os.listdir(l[i]) if os.path.isdir(l[i]+'/'+j) ]
            if len(tmp) > 0:
                l.pop(i)
                l.extend(tmp)
            else:
                i += 1
    return l

# Check if a file has \r in its content
def is_dos(filename):
    f = open(filename, "rb")
    for l in f:
        if b"\r" in l:
            return True
    return False

# convert a file to unix format
def convert_unix(filename):
    f = open(filename, "U")
    t = tempfile.TemporaryFile()

    for l in f:
        t.write(l)

    f.close()
    t.close()

    os.move(t.name, f.name)

# This is the same but for files
# top: where to start the search
# ext: extension to be matched
def find_files(top, ext):
    dd = find_dirs(top)
    dd.append(top)
    l = []
    extre = re.compile("\."+ext+"$")
    for d in dd:
        tmp = [d+'/'+i for i in os.listdir(d) if os.path.isfile(d+'/'+i) and not extre.search(i) == None]
        l.extend(tmp)
    return l

# Recursively find a file and check its existence.
# We iterate through the include dirs (-I option) to find them and return the
# first occurrence
def check_file(fi):
    if os.path.isfile(src_dir+"/"+fi):
        return src_dir+"/"+fi
    else:
        dirs = include.split("-I")
        dirs[0] = '.' # instead of empty
        fi = os.path.basename(fi)
        for d in dirs:
            i = 0
            l = os.listdir(d)
            while i < len(l):
                dd = l[i] if d == '.' else d+'/'+l[i]
                if os.path.isdir(dd):
                    tmp = [ dd+"/"+j for j in os.listdir(dd) ]
                    l.extend(tmp)
                elif os.path.isfile(dd) and os.path.basename(dd) == fi:
                    return dd
                i = i+1
    return ""

# save the cache file
# this function should be called before exiting if the deps have changed
def save_cache():
    global cache_file, deps
    d = deps
    for k, v in d.items():
        d[k]['deps'] = list(v['deps'])
    with open(cache_file, 'w') as jf:
        if verbose:
            json.dump(d, jf, indent=2)
        else:
            json.dump(d, jf)
        jf.close()
        if verbose:
            warning_msg("Cache file saved to %s"%cache_file)

# Find the dependencies of a file
# Memoization achieved with the dictionary deps
inc = re.compile("^\s*#include\s*[<\"](.*?)[<\"]")
deps = {} # dictionary with dependencies
cache_file = "configure.cache"
if os.path.isfile(cache_file):
    if verbose:
        warning_msg("A cache file exist at %s"%cache_file)
    with open(cache_file) as jf:
        try:
            deps = json.load(jf)
        except ValueError:
            error_msg("The cache file is not JSON!")
        jf.close()
    info_msg("Checking if cache file is valid...")
    ok = True
    for k,v in deps.items():
        if not ('hash' in v and 'deps' in v) or not type(v) == dict:
            ok = False
    if ok:
        good_msg("OK")
    else:
        error_msg("KO")
        deps = {}
        warning_msg("Cache file is invalid, the dependencies must be calculated.")

# fast hashing file using adler32
def hash_file(fname):
    BLOCKSIZE=256*1024*1024
    asum = 1
    with open(fname) as f:
        while True:
            data = f.read(BLOCKSIZE)
            if not data:
                break
            asum = adler32(bytes(data, 'UTF-8'), asum)
            if asum < 0:
                asum += 2**32
    return asum

# each entry have hash of the file itself and a list of dependencies in order to
# use it as a cache and then only find dependencies of files that have changed.
# Using a hash turns out to be fastes than getting the date with
# os.path.getmdate() BUT I only tested doing a loop with the same file
# the model is: file-name: {'hash': 'hash string', 'deps': ["file1", "file2"]}
# deps is filled with that kind of entry
# fi: file to check. must exist
def find_dependencies(fi):
    global deps
    if fi in deps:
        ha = hash_file(fi)
        if ha == deps[fi]['hash']:
            return deps[fi]['deps']
        elif verbose:
            warning_msg("The file %s has changed (%d != %d), checking the dependencies again."%(fi, ha, deps[fi]['hash']))

    dep = {
                'hash' : hash_file(fi),
                'deps' : set()
               }

    f = open(fi, "U")
    try:
        i = 1
        for l in f:
            m = inc.match(l)
            if m:
                tmp = m.groups()[0].replace("\\","/") # win style include (so ugly)
                ff = check_file(tmp)
                #warning_msg("%s: %s -> %s"%(l, tmp, ff))
                if not ff == "" and not ff in dep:
                    dep['deps'].add(ff)
                    dep['deps'].update(find_dependencies(ff))
                elif ff == "":
                    error_msg("KO")
                    error_msg("%s, line %d: %s doesn't exist!"%(f.name, i, m.groups()[0]))
                    save_cache()
                    exit(1)
            i += 1
    except UnicodeDecodeError:
        error_msg("KO")
        error_msg("There was an error decoding file %s at line %d..."%(f.name, i))
        save_cache()
        exit(1)

    f.close()
    deps[fi] = dep
    return deps[fi]['deps']

# When no -E is given we try to find it
def find_exec():
    global exec_file
    main = re.compile("^\s*(int|void)\s+main\([^)]*\)")
    for fi in files:
        f = open(fi, "U")
        for l in f:
            if main.match(l):
                exec_file.append(f.name)
                break
        f.close()

# fill the list of exec_name using the basename
# if both lists have same length then nothing will happen
# TODO only generate the names you need
def gen_exec_names():
    global exec_name
    if not len(exec_name) == len(exec_file):
        exec_name = [] # python2 compatible
        #exec_name.clear()
        for e in exec_file:
            exec_name.append(extre.sub("", os.path.basename(e)))

# generate a string from an iterable object. Items are separated by spaces
def list2str(l):
    s = ""
    for i in l:
        s = i if s == "" else s +" "+i
    return s

# the Makefile header with some basic rules
def makefile_header():
    resp = re.compile("\s+")
    f = open(makefile, "w", encoding="utf-8")
    f.write("# Makefile generated with configure script by Eduardo San Martin Morote \n\
# aka Posva. http://posva.net\n\
# GitHub repo: https://github.com/posva/configure.py\n\
# Please report any bug to i@posva.net\n\
\n\
CXX := "+cxx+"\n\
LINKER := "+linker+"\n\
OPT := "+resp.sub(" ",default_options+" "+options+" "+default_include+" "+include)+"\n\
LINK_OPT := "+resp.sub(" ", default_link_opt+" "+link_opt+" "+link)+"\n\
LIBS := "+resp.sub(" ", default_link+" "+libs)+"\n\
SHELL := "+os.getenv("SHELL", "/bin/bash")+"\n\
")

    f.write("\n\
all : "+list2str([bin_dir+"/"+i for i in exec_name])+" "+list2str(obj_files)+"\n\n")

    clean_list = [bin_dir+"/"+e for e in exec_name]

    i = 0
    while i < len(exec_file):
        if cmake_style:
          f.write(bin_dir+"/"+exec_name[i]+" : "+obj_dir+"/"+extre.sub(".o", os.path.basename(exec_file[i]))+" "+list2str(obj_files)+"\n\
	@echo -e \"\e[31;1mLinking "+exec_name[i]+"\e[0m\" && $(LINKER) $(LINK_OPT) $^ -o \"$@\" $(LIBS)\n\n")
        else:
          f.write(bin_dir+"/"+exec_name[i]+" : "+obj_dir+"/"+extre.sub(".o", os.path.basename(exec_file[i]))+" "+list2str(obj_files)+"\n\
	$(LINKER) $(LINK_OPT) $^ -o \"$@\" $(LIBS)\n\n")

        i += 1

    f.write("\nrun : "+bin_dir+"/"+exec_name[0]+"\n\
	./"+bin_dir+"/"+exec_name[0]+"\n\
.PHONY : run\n\
\n\
# Create a file test-all.sh to make this work\n\
test : all\n\
	./test-all.sh\n\
.PHONY : test\n\
\n\
clean :\n\
	rm -f "+list2str(obj_files)+" "+list2str(clean_list)+"\n\
.PHONY : clean\n\
\n\
valgrind : all\n\
	valgrind -v --leak-check=full --tool=memcheck ./"+bin_dir+"/$(EXEC)\n\
.PHONY : valgrind\n\
")
    f.close()

# Read the tree of src_dir
tmp = find_dirs(src_dir)
srcobj = re.compile("^"+src_dir)
folders = [ srcobj.sub(obj_dir, d) for d in tmp]
folders.sort() # we sort so we can create correctly

# List files that are going t be checked
files = find_files(src_dir, file_ext)

if verbose:
    warning_msg("%d files must be checked"%len(files))
if len(exec_file) == 0:
    info_msg("No executables files were given, finding them...")
    find_exec()
    if len(exec_file) == 0:
        error_msg("KO")
        error_msg("There is no main function!")
        exit(1)
    good_msg("OK")
    if verbose:
        warning_msg("Executables found: %s"%list2str(exec_file))

extre = re.compile("\."+file_ext+"$")
# we need a list of all the .o files
# We need to remove the executables from the obj list if they're in it
tmp = [i for i in files if i not in exec_file]
obj_files = [srcobj.sub(obj_dir, extre.sub(".o", i)) for i in tmp]

# we generate if needed the executables names
if verbose:
    warning_msg("%d executable rules will be generated. %d names were given for these.%s"%(len(exec_file), len(exec_name), " Names will be generated automatically." if not len(exec_file) == len(exec_name) else ""))

# Generate names if needed
if not len(exec_file) == len(exec_name):
    gen_exec_names()

# Start the generation
info_msg("Creating some rules for Makefile...")
makefile_header()
good_msg("OK")

info_msg("Creating directories...")
if not os.path.isdir(bin_dir):
    os.mkdir(bin_dir)
if not os.path.isdir(obj_dir):
    os.mkdir(obj_dir)

try:
    for i in folders:
        if not os.path.isdir(i):
            os.mkdir(i)
except FileExistsError:
    print(sys.exc_info()[2])
    error_msg("KO")
    exit(1)

good_msg("OK")

m = open(makefile, "a", encoding="utf-8")
now_file = 0

# for those files that are not in src_dir we must create the rules too
exec_c_files = []
for f in exec_file:
    if not f in files:
        exec_c_files.append(f)

total_files = len(files)+len(exec_c_files)

for f in files:
    if f in deps:
        info_msg("Checking for modifications on %s..."%f)
    else:
        info_msg("Checking dependencies for %s..."%f)
    l = find_dependencies(f)
    good_msg("OK")
    if verbose:
        warning_msg("Dependencies: %s"%list2str(l))
    o = srcobj.sub(obj_dir, extre.sub(".o", f))
    if cmake_style:
        now_file = now_file+1
        perc = 100 * now_file / total_files
        rule = o + ": " + f + " " + list2str(l) + """
	@echo -e \"["""+str(int(perc))+"""%] \e[32mBuilding $@\e[0m\" && $(CXX) $(OPT) $< -c -o $@
"""
        m.write(rule)
    else:
        rule = o + ": " + f + " " + list2str(l) + """
	$(CXX) $(OPT) $< -c -o $@
"""
        m.write(rule)

for f in exec_c_files:
    info_msg("Checking dependencies for %s..."%f)
    if not os.path.isfile(f):
        error_msg("OK")
        error_msg("File %s doesn't exists"%f)
        save_cache()
        exit(1)
    else:
        l = find_dependencies(f)
        good_msg("OK")
        if verbose:
            warning_msg("Dependencies: %s"%list2str(l))
        o = obj_dir+"/"+extre.sub(".o", os.path.basename(f))
        if cmake_style:
            now_file = now_file+1
            perc = 100 * now_file / total_files
            rule = o + ": " + f + " " + list2str(l) + """
	@echo -e \"["""+str(int(perc))+"""%] \e[32mBuilding $@\e[0m\" && $(CXX) $(OPT) $< -c -o $@
"""
            m.write(rule)
        else:
            rule = o + ": " + f + " " + list2str(l) + """
	$(CXX) $(OPT) $< -c -o $@
"""
            m.write(rule)

m.close()

# save the cache
save_cache()

elapsed = (time.time() - start_time)
warning_msg("Makefile(%s) generated in %.5f seconds."%(makefile, elapsed))

