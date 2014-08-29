#!/usr/bin/env python
#
# This script generates a test include file from a set of "Fuse" test vectors.
#
import os

# Start with this test name (this is a string; see tests files)
start_test = "00"

# Number of tests to run; use -1 to run all tests
run_tests = 1

# Set this to 1 to use regression test files instead of 'tests.*'
# It will run all regression tests (start_test, run_tests are ignored)
regress = 1

#------------------------------------------------------------------------------
# Determine which test files to use
tests_in = 'fuse/tests.in'
tests_expected = 'fuse/tests.expected'

# Regression testing executes all regression tests
if regress:
    tests_in = 'fuse/regress.in'
    tests_expected = 'fuse/regress.expected'
    start_test = "00"
    run_tests = -1

with open(tests_in) as f1:
    t1 = f1.read().splitlines()
# Remove all tests until the one we need to start with. Tests are separated by empty lines.
while t1[0].split(" ")[0]!=start_test:
    while len(t1.pop(0))>0:
        pass
t1 = filter(None, t1)   # Filter out empty lines

with open(tests_expected) as f2:
    t2 = f2.read().splitlines()
while t2[0].split(" ")[0]!=start_test:
    while len(t2.pop(0))>0:
        pass

# Count total clocks required to run all selected tests
total_clks = 0

def RegWrite(reg, hex):
    global total_clks
    ftest.write("force dut.reg_file.b2v_latch_" + reg + "_lo.we=1;\n")
    ftest.write("   force dut.reg_file.b2v_latch_" + reg + "_hi.we=1;\n")
    ftest.write("   force dut.reg_file.b2v_latch_" + reg + "_lo.db=8'h" + hex[2:] + ";\n")
    ftest.write("   force dut.reg_file.b2v_latch_" + reg + "_hi.db=8'h" + hex[0:2] + ";\n")
    ftest.write("#1 release dut.reg_file.b2v_latch_" + reg + "_lo.we;\n")
    ftest.write("   release dut.reg_file.b2v_latch_" + reg + "_hi.we;\n")
    ftest.write("   release dut.reg_file.b2v_latch_" + reg + "_lo.db;\n")
    ftest.write("   release dut.reg_file.b2v_latch_" + reg + "_hi.db;\n")
    ftest.write("#1 ")
    total_clks = total_clks + 2

def RegRead(reg, hex):
    global total_clks
    ftest.write("force dut.reg_file.b2v_latch_" + reg + "_lo.oe=1;\n")
    ftest.write("   force dut.reg_file.b2v_latch_" + reg + "_hi.oe=1;\n")
    ftest.write("#1 if (dut.reg_file.b2v_latch_" + reg + "_lo.db!==8'h" + hex[2:] +  ") $fdisplay(f,\"* Reg " + reg + " " + reg[1] + "=%h !=" + hex[2:] +  "\",dut.reg_file.b2v_latch_" + reg + "_lo.db);\n")
    ftest.write("   if (dut.reg_file.b2v_latch_" + reg + "_hi.db!==8'h" + hex[0:2] + ") $fdisplay(f,\"* Reg " + reg + " " + reg[0] + "=%h !=" + hex[0:2] + "\",dut.reg_file.b2v_latch_" + reg + "_hi.db);\n")
    ftest.write("   release dut.reg_file.b2v_latch_" + reg + "_lo.oe;\n")
    ftest.write("   release dut.reg_file.b2v_latch_" + reg + "_hi.oe;\n")
    ftest.write("#1 ")
    total_clks = total_clks + 2

#---------------------------- START -----------------------------------
# Create a file that should be included in the test_fuse source
ftest = open('test_fuse.i', 'w')
ftest.write("// Automatically generated by genfuse.py\n\n")

# Initial pre-test state is reset and control signals asserted
ftest.write("force dut.reg_file.reg_gp_we=0;\n")
ftest.write("force dut.reg_control.ctl_reg_sys_we=0;\n")
ftest.write("force dut.z80_top.fpga_reset=1;\n")
ftest.write("#2\n")
total_clks = total_clks + 2

# Read each test from the testdat.in file
while True:
    ftest.write("//" + "-" * 80 + "\n")
    if len(t1)==0 or run_tests==0:
        break
    run_tests = run_tests-1

    # Format of the test.in file:
    # <arbitrary test description>
    # AF BC DE HL AF' BC' DE' HL' IX IY SP PC
    # I R IFF1 IFF2 IM <halted> <tstates>
    name = t1.pop(0)
    ftest.write("$fdisplay(f,\"Testing opcode " + name + "\");\n\n")
    name = name.split(" ")[0]
    r = t1.pop(0).split(' ')
    r = filter(None, r)
    # 0  1  2  3  4   5   6   7   8  9  10 11   (index)
    # AF BC DE HL AF' BC' DE' HL' IX IY SP PC
    RegWrite("af", r[0])
    RegWrite("bc", r[1])
    RegWrite("de", r[2])
    RegWrite("hl", r[3])
    RegWrite("af2", r[4])
    RegWrite("bc2", r[5])
    RegWrite("de2", r[6])
    RegWrite("hl2", r[7])
    RegWrite("ix", r[8])
    RegWrite("iy", r[9])
    RegWrite("sp", r[10])
    RegWrite("pc", r[11])

    s = t1.pop(0).split(' ')
    s = filter(None, s)
    # 0 1 2    3    4  5        6          (index)
    # I R IFF1 IFF2 IM <halted> <tstates?>
    RegWrite("ir", s[0]+s[1])
    # TODO: Store IFF1/IFF2, IM, in_halt

    # Read memory configuration until the line contains only -1
    while True:
        m = t1.pop(0).split(' ')
        if m[0]=="-1":
            break
        address = int(m.pop(0),16)
        while True:
            d = m.pop(0)
            if d=="-1":
                break
            ftest.write("   ram.Mem[" + str(address) + "] = 8'h" + d + ";\n")
            address = address+1

    # Prepare instruction to be run. By releasing the fpga_reset, internal CPU reset will be active
    # for 1T and the engine will try to clear PC and IR registers. We need to prevent that by forcing
    # reg_sys_we to 0 during that time.
    # Due to the instruction execution overlap, first 2T of an instruction may be writing
    # value back to a general purpose register (like AF). We need to prevent that as well.
    # Similarly, we let the execution continues 2T into the next instruction but we prevent
    # it from writing to system registers so it cannot update PC and IR (again)
    ftest.write("#1 force dut.z80_top.fpga_reset=0;\n")
    ftest.write("#2 release dut.reg_control.ctl_reg_sys_we;\n")
    ftest.write("#5 release dut.reg_file.reg_gp_we;\n")
    ftest.write("#1\n")
    total_clks = total_clks + 9

    # Read and parse the tests expected list which contains the expected results of our run,
    # including the number of clocks for a particular instruction
    xname = t2.pop(0).split()[0]
    if name!=xname:
        print("Test " + name + " does not correspond to test.expected " + xname)
        break
    # Skip the memory access logs; read to the expected register content list
    while True:
        l = t2.pop(0)
        if l[0]!=' ':
            break
    r = l.split(' ')
    r = filter(None, r)

    s = t2.pop(0).split(' ')
    s = filter(None, s)

    ticks = int(s[6]) * 2 - 6
    total_clks = total_clks + ticks
    ftest.write("#" + str(ticks) + " // Execute\n")

    ftest.write("   force dut.reg_control.ctl_reg_sys_we=0;\n")
    ftest.write("#4 force dut.reg_file.reg_gp_we=0;\n")
    ftest.write("   force dut.z80_top.fpga_reset=1;\n")
    total_clks = total_clks + 4

    # Now we can issue register reading commands
    # We are guided on what to read and check by the content of "test.expected" file

    # Read the result: registers and memory
    # 0  1  2  3  4   5   6   7   8  9  10 11   (index)
    # AF BC DE HL AF' BC' DE' HL' IX IY SP PC
    RegRead("af", r[0])
    RegRead("bc", r[1])
    RegRead("de", r[2])
    RegRead("hl", r[3])
    RegRead("af2", r[4])
    RegRead("bc2", r[5])
    RegRead("de2", r[6])
    RegRead("hl2", r[7])
    RegRead("ix", r[8])
    RegRead("iy", r[9])
    RegRead("sp", r[10])
    RegRead("pc", r[11])
    # 0 1 2    3    4  5        6          (index)
    # I R IFF1 IFF2 IM <halted> <tstates?>
    RegRead("ir", s[0]+s[1])

    # Read memory configuration until an empty line or -1 at the end
    while True:
        m = t2.pop(0).split(' ')
        m = filter(None, m)
        if len(m)==0 or m[0]=="-1":
            break
        address = int(m.pop(0),16)
        while True:
            d = m.pop(0)
            if d=="-1":
                break
            ftest.write("   if (ram.Mem[" + str(address) + "]!==8'h" + d + ") $fdisplay(f,\"* Mem[" + hex(address)[2:] + "]=%h !=" + d + "\",ram.Mem[" + str(address) + "]);\n")
            address = address+1

    ftest.write("#1\n")
    total_clks = total_clks + 1

# Write out the total number of clocks that this set of tests takes to execute
ftest.write("`define TOTAL_CLKS " + str(total_clks + 1) + "\n")
ftest.write("$fdisplay(f,\"=== Tests completed ===\");\n")

# Touch a file that includes 'test_fuse.i' to ensure it will recompile correctly
os.utime("test_fuse.sv", None)
