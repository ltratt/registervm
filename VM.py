# Copyright (c) 2013 King's College London, created by Laurence Tratt
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.


import os, sys

try:
    import pypy
except:
    import sys
    sys.path.append(os.getenv("PYPY_SRC"))
from pypy.rlib import jit

INSTR_INC = 0
INSTR_DEC = 1
INSTR_GOTO = 2


jitdriver = jit.JitDriver(greens=["pc"], reds=["instrs", "regs"])

def loop(instrs, regs):
    pc = 0
    while pc < len(instrs):
        jitdriver.jit_merge_point(pc=pc, instrs=instrs, regs=regs)
        instr = get_instr(instrs, pc)
        if instr[0] == INSTR_INC:
            regs[instr[1]] += 1
            pc += 1
        elif instr[0] == INSTR_DEC:
            v = regs[instr[1]]
            if v == 0:
                if instr[2] < pc:
                    jitdriver.can_enter_jit(pc=pc, instrs=instrs, regs=regs)
                pc = instr[2]
            else:
                regs[instr[1]] = v - 1
                pc += 1
        else:
            assert instr[0] == INSTR_GOTO
            if instr[1] < pc:
                jitdriver.can_enter_jit(pc=pc, instrs=instrs, regs=regs)
            pc = instr[1]



@jit.elidable_promote()
def get_instr(instrs, pc):
    return instrs[pc]



def entry_point(argv):
    if len(argv) == 1:
        print "VM.py <file> [<arg1> ... <argn>]"
        return 1
    try:
        fd = os.open(argv[1], os.O_RDONLY, 0777)
        i = 0
        d = []
        while True:
            read = os.read(fd, 4096)
            if len(read) == 0:
                break
            d.append(read)
    except OSError:
        print "Error reading from '%s'." % argv[1]
        return 1

    lines = "".join(d).split("\n")
    resultr = int(lines[0])
    regs = [0] * resultr
    i = 0
    for r in argv[2:]:
        try:
            regs[i] = int(r)
        except ValueError:
            print "Command line argument '%s' not valid." % r
            return 1
        i += 1
    instrs = []
    for l in lines[1:]:
        type, params1 = l.split("(")
        params2 = [int(x) for x in params1[:-1].split(",")]
        if type == "Inc":
            instrs.append((INSTR_INC, params2[0], 0),)
        elif type == "Dec":
            instrs.append((INSTR_DEC, params2[0], params2[1]),)
        else:
            instrs.append((INSTR_GOTO, params2[0], 0),)
    loop(instrs, regs)
    print regs
    
    return 0



def jitpolicy(driver):
    from pypy.jit.codewriter.policy import JitPolicy
    return JitPolicy()



def target(*args):
    return entry_point, None



if __name__ == "__main__":
    entry_point(sys.argv)