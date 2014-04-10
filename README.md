configure.py
============

configure script for C/C++ project. Generates Makefiles

This is quite the python3 version of [this](https://github.com/posva/configure-script)

![img](http://i.imgur.com/Z6Lmt6V.png)

#Usage

You should have a `configure` file as in the repo that pass the right options to the script so you only have to do
`./configure` and then `make run`

**I'll add a full example here later**

#TODO List
- [x] Cache file
- [x] Use dates instead of hash
- [ ] factorize some coe

#Knows Issues

* The script cannot detect multi lines comments or process any #ifdef. Therefore any of these includes will be treated as if they were valid and will try to find them.
* ~~Recursive include: if you include one file inside itself you'll have a RuntimeError. This may happen if the include is used as a comment~~

#Help

Do `./configure.py -h` to display help about options.

#Contact

You can contact me at i@posva.net
