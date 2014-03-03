#! /usr/bin/env python3

import getopt, sys, time, os, re

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
  "+sys.argv[0]+" -D -s src -o obj -b bin -c \"xcrun clang++\" -O \"-Wall -Wextra -O2 -std=c++11 -stdlib=libc++\" -Isrc -L/usr/local/lib -e cpp -E main -M Makefile -N \"-std=c++11 -stlib=libc++\"\n\
\n\
GitHub repo: https://github.com/posva/configure-script")

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
def warning_msg(*args, **kwargs):
    print(c_yellow, end='')
    __builtins__.print(*args, **kwargs)
    print(c_clean, end='')
def info_msg(*args):
    print(c_blue, end='')
    __builtins__.print(*args, end = '')
    print(c_clean, end='')


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

# Find the dependencies of a file
# Memoization achieved with the dictionary deps
inc = re.compile("^\s*#include\s*[<\"](.*?)[<\"]")
deps = {} # dictionary with dependencies
# fi: file to check. must exist
def find_dependencies(fi):
    if fi in deps:
        return deps[fi]
    else:
        deps[fi] = set() # Empty set

    f = open(fi)
    for l in f:
        m = inc.match(l)
        if m:
            ff = check_file(m.groups()[0])
            if not ff in deps[fi]:
                deps[fi].add(ff)
                deps[fi].update(find_dependencies(ff))
            #print(ff+"->", end='')
            #print(deps[fi])
    f.close()
    return deps[fi]

# TODO autofind main methods.
# When no -E is given we try to find it
def find_exec():
    return ""

# fill the list of exec_name using the basename
# if both lists have same length then nothing will happen
def gen_exec_names():
    if not len(exec_name) == len(exec_file):
        exec_name.clear()
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
# GitHub repo: https://github.com/posva/configure-script\n\
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
all : "+bin_dir+"/"+exec_name[0]+" "+list2str(obj_files)+"\n\n")

    clean_list = [bin_dir+"/"+e for e in exec_name]

    i = 0
    while i < len(exec_file):
        if cmake_style:
          f.write(bin_dir+"/"+exec_name[i]+" : "+obj_dir+"/"+extre.sub(".o", os.path.basename(exec_file[i]))+" "+list2str(obj_files)+"\n\
	@echo -e \"\e[31;1mLinking $(EXEC)\e[0m\" && $(LINKER) $(LINK_OPT) $^ -o \"$@\" $(LIBS)\n\n")
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
extre = re.compile("\."+file_ext+"$")
# we need a list of all the .o files
# We need to remove the executables from the obj list if they're in it
tmp = [i for i in files if i not in exec_file]
obj_files = [srcobj.sub(obj_dir, extre.sub(".o", i)) for i in tmp]

# we generate if needed the executables names
if verbose:
    warning_msg(len(exec_file), " executables rules will be generated. ",len(exec_name), " names were given for these.", " Names will be generated automatically." if not len(exec_file) == len(exec_name) else "")
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
    info_msg("Checking dependencies for "+f+"...")
    l = find_dependencies(f)
    good_msg("OK")
    if verbose:
        warning_msg("Dependencies:", list2str(l))
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
    info_msg("Checking dependencies for "+f+"...")
    l = find_dependencies(f)
    good_msg("OK")
    if verbose:
        warning_msg("Dependencies:", list2str(l))
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


elapsed = (time.time() - start_time)
warning_msg("Makefile(%s) generated in %.5f seconds."%(makefile, elapsed))
