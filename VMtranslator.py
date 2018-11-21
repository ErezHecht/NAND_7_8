import sys
import os

from pathlib import Path

# from parser import Parser
# from codeWriter import CodeWriter
# ----------------------------- Constants ---------------------------------- #
# General:
VM_SUFFIX = ".vm"
ASM_SUFFIX = ".asm"
COMMENT = "//"
CONSTANT = "constant"
STATIC = "static"
POINTER = "pointer"
TEMP = "temp"
THIS = "this"
THAT = "that"
NEW_LINE = "\n"
AT = "@"
STACK_POINTER = "@SP\n"
TEMP_ONE = "@R13\n"
TEMP_TWO = "@R14\n"
# Operands :
M_PLUS_ONE = "M=M+1\n"
AT_STACK = "AM=M-1\n"
SUB_ADDRESS = "A=A-1\n"
ADDRESS_STACK_HEAD = "A=M-1\n"
SET_DATA = "D=M\n"
SET_M_TO_D = "M=D\n"
ADD_M_D = "M=D+M\n"
SUB_M_D = "M=M-D\n"
SUB_D_M = "D=M-D\n"
SUB_D = "D=D-M\n"
ADD_A_TO_D = "D=D+A\n"
NEG_M = "M=-M\n"
AND_M_D = "M=D&M\n"
OR_M_D = "M=D|M\n"
NOT_M = "M=!M\n"
SET_ADDRESS_TO_M = "A=M\n"
SET_FALSE = "M=0\n"
SET_TRUE = "M=-1\n"
SET_D_FALSE = "D=0\n"
SET_D_TRUE = "D=-1\n"
ADD_ADDRESS_WITH_DATA = "A=D+A\n"
SET_DATA_TO_ADDRESS = "D=A\n"

# Labels:
EQ_TRUE = "EQ_TRUE_"
EQ_END = "EQ_END_"
GT_TRUE = "GT_TRUE_"
GT_FALSE = "GT_FALSE_"
GT_NORM = "GT_NORM_"
GT_X_POS = "GT_X_POS_"
GT_END = "GT_END_"
LT_TRUE = "LT_TRUE_"
LT_FALSE = "LT_FALSE_"
LT_NORM = "LT_NORM_"
LT_X_NEG = "LT_X_NEG_"
LT_END = "LT_END_"
LABEL_START = "("
LABEL_END = ")\n"

# JUMPS:
EQ_JMP = "D;JEQ\n"
GT_JMP = "D;JGT\n"
LT_JMP = "D;JLT\n"
GE_JMP = "D;JGE\n"
LE_JMP = "D;JLE\n"
JMP = "0;JMP\n"
# Tables:
TRUE_LABELS = [EQ_TRUE, GT_TRUE, LT_TRUE]
END_LABELS = [EQ_END, GT_END, LT_END]
JUMPS = [EQ_JMP, GT_JMP, LT_JMP]

# "MACROS":
ADVANCE_STACK = STACK_POINTER + M_PLUS_ONE
POP_FROM_STACK = STACK_POINTER + AT_STACK + SET_DATA
ACCESS_TWO_SPOTS_IN_STACK = POP_FROM_STACK + SUB_ADDRESS
STORE_TWO_VARS_TEMP = STACK_POINTER + AT_STACK + SET_DATA + TEMP_TWO + \
                      SET_M_TO_D + STACK_POINTER + ADDRESS_STACK_HEAD + \
                      SET_DATA + TEMP_ONE + SET_M_TO_D

ADD = ACCESS_TWO_SPOTS_IN_STACK + ADD_M_D
SUB = ACCESS_TWO_SPOTS_IN_STACK + SUB_M_D
NEG = STACK_POINTER + ADDRESS_STACK_HEAD + NEG_M
AND = ACCESS_TWO_SPOTS_IN_STACK + AND_M_D
OR = ACCESS_TWO_SPOTS_IN_STACK + OR_M_D
NOT = STACK_POINTER + ADDRESS_STACK_HEAD + NOT_M
POP = TEMP_ONE + SET_M_TO_D + STACK_POINTER + AT_STACK + SET_DATA + TEMP_ONE \
      + SET_ADDRESS_TO_M + SET_M_TO_D
PUSH = STACK_POINTER + SET_ADDRESS_TO_M + SET_M_TO_D + ADVANCE_STACK

# Segment -> hack:
SEGMENTS = {"local": "LCL\n", "argument": "ARG\n", THIS: "THIS\n",
            THAT: "THAT\n"}
# C_Arithmetic -> hack:
ARITHMETIC = {"add": ADD, "sub": SUB, "neg": NEG, "and": AND, "or": OR,
              "not": NOT}
EQ = "eq"
GT = "gt"
LT = "lt"
# Commands:
C_PUSH = "push"
C_POP = "pop"
C_ARITHMETIC = "C_ARITHMETIC"
ARITHMETIC_COMMANDS = ["add", "sub", "neg", "and", "or", "not", "eq", "lt",
                       "gt"]


# ------------------------------------------------------------------------- #

class CodeWriter:
    def __init__(self, out_address):
        """Opens the output file and gets ready to write in it."""
        self.OUT_ADDRESS = out_address
        self.EQ_INDEX = 0
        self.GT_INDEX = 0
        self.LT_INDEX = 0
        self.OUTPUT = ""

    def parse_file(self, address):
        file_commands = []
        with open(address, "r") as f:
            # Get all lines ignoring whitespace lines or comment lines:
            file_commands = [line.strip() for line in f if
                             not line.strip().startswith(COMMENT)
                             and len(line.strip()) != 0]
            # Get rid of comments after commands:
            for i in range(len(file_commands)):
                c = file_commands[i].find(COMMENT)
                if c != -1:
                    file_commands[i] = file_commands[i][:c]
                file_commands[i] = file_commands[i].split()
        return file_commands

    def write_to_file(self):
        with open(self.OUT_ADDRESS, 'w') as f:
            f.write(self.OUTPUT)

    def set_file_name(self, file_name):
        """Sets the name of the current input file - used for static."""
        self.FILE_NAME = file_name

    def write_command(self, command):
        """Translates the given command into asm and adds it to output. """
        # Comment showing what command is executed next
        self.OUTPUT += COMMENT + " ".join(command) + NEW_LINE
        if command[0] in ARITHMETIC_COMMANDS:
            self.write_arithmetic(command[0])
        elif command[0] == C_PUSH or command[0] == C_POP:
            self.write_push_pop(command[0], command[1], command[2])
        else:
            print("Error: Illegal Command")
            exit(-1)

    def write_arithmetic(self, command):
        """Writes to the output file the assembly code that implements the
        given arithmetic command."""
        if command == EQ:
            self.OUTPUT += self.__get_eq()
        elif command == GT:
            self.OUTPUT += self.__get_gt()
        elif command == LT:
            self.OUTPUT += self.__get_lt()
        else:
            self.OUTPUT += ARITHMETIC[command]

    def write_push_pop(self, command, segment, index):
        """Writes to the output file the assembly code that implements the
        given command, where command is either C_PUSH or C_POP."""
        if command == C_PUSH:
            self.OUTPUT += self.__push(segment, index)
        else:
            self.OUTPUT += self.__pop(segment, index)

    # PUSH functions:
    def __push(self, segment, index):
        out = ""
        if segment == STATIC:
            out += self.__get_static(index) + SET_DATA
        elif segment == CONSTANT:
            out += self.__get_constant(index)
        elif segment == POINTER:
            out += self.__get_pointer(index) + SET_DATA
        elif segment == TEMP:
            out += self.__get_temp(index) + SET_DATA
        else:
            out += self.__get_dynamic_memory(segment, index) + \
                   ADD_ADDRESS_WITH_DATA + SET_DATA
        out += PUSH
        return out

    def __get_static(self, index):
        return AT + self.FILE_NAME + str(index) + NEW_LINE

    def __at_i(self, index):
        return AT + str(index) + NEW_LINE

    def __get_dynamic_memory(self, segment, index):
        """Sets D to be the value at segment index, where segment is local,
        argument, this or that."""
        return AT + SEGMENTS[segment] + SET_DATA + self.__at_i(
            index)

    def __get_constant(self, index):
        return AT + str(index) + NEW_LINE + SET_DATA_TO_ADDRESS

    def __get_pointer(self, index):
        out = AT
        if index == "0":
            out += SEGMENTS[THIS]
        else:
            out += SEGMENTS[THAT]
        return out

    def __get_temp(self, index):
        return AT + str(5 + int(index)) + NEW_LINE

    # POP FUNCTIONS:
    def __pop(self, segment, index):
        out = ""
        # Access the relevant memory cell:
        if segment == CONSTANT:
            print("Error: Illegal pop location")
            exit(-1)
        elif segment == STATIC:
            out += self.__get_static(index) + SET_DATA_TO_ADDRESS
        elif segment == POINTER:
            out += self.__get_pointer(index) + SET_DATA_TO_ADDRESS
        elif segment == TEMP:
            out += self.__get_temp(index) + SET_DATA_TO_ADDRESS
        else:
            out += self.__get_dynamic_memory(segment, index) + ADD_A_TO_D
        # POP: Stores the address in R13 temporarily, and then pop into the
        # address saved.
        out += POP
        return out

    def __get_eq(self):
        """Returns the asm code for calculating equals:"""
        eq = ""
        str_index = str(self.EQ_INDEX)
        eq += STACK_POINTER + AT_STACK + SUB_ADDRESS
        eq += SUB_D_M
        eq += AT + EQ_TRUE + str_index + NEW_LINE
        eq += EQ_JMP
        eq += STACK_POINTER + ADDRESS_STACK_HEAD + SET_FALSE
        eq += AT + EQ_END + str_index + NEW_LINE
        eq += JMP
        eq += LABEL_START + EQ_TRUE + str_index + LABEL_END
        eq += STACK_POINTER + ADDRESS_STACK_HEAD + SET_TRUE
        eq += LABEL_START + EQ_END + str_index + LABEL_END
        self.EQ_INDEX += 1
        return eq

    def __get_gt(self):
        """Returns the asm code for calculating greater than:"""
        gt = ""
        str_index = str(self.GT_INDEX)
        gt += STORE_TWO_VARS_TEMP
        gt += TEMP_ONE + SET_DATA
        gt += AT + GT_X_POS + str_index + NEW_LINE + GT_JMP
        gt += TEMP_TWO + SET_DATA + AT + GT_FALSE + str_index + NEW_LINE + \
              GT_JMP
        gt += AT + GT_NORM + str_index + NEW_LINE + JMP
        gt += LABEL_START + GT_X_POS + str_index + LABEL_END
        gt += TEMP_TWO + SET_DATA + AT + GT_TRUE + str_index + NEW_LINE + \
              LE_JMP
        gt += LABEL_START + GT_NORM + str_index + LABEL_END
        gt += TEMP_ONE + SET_DATA + TEMP_TWO + SUB_D + AT + GT_TRUE + \
              str_index + NEW_LINE + GT_JMP
        gt += LABEL_START + GT_FALSE + str_index + LABEL_END
        gt += SET_D_FALSE + AT + GT_END + str_index + NEW_LINE + JMP
        gt += LABEL_START + GT_TRUE + str_index + LABEL_END
        gt += SET_D_TRUE
        gt += LABEL_START + GT_END + str_index + LABEL_END
        gt += STACK_POINTER + ADDRESS_STACK_HEAD + SET_M_TO_D
        self.GT_INDEX += 1
        return gt

    def __get_lt(self):
        """Returns the asm code for calculating less than:"""
        lt = ""
        str_index = str(self.LT_INDEX)
        lt += STORE_TWO_VARS_TEMP
        lt += TEMP_ONE + SET_DATA
        lt += AT + LT_X_NEG + str_index + NEW_LINE + LT_JMP
        lt += TEMP_TWO + SET_DATA + AT + LT_FALSE + str_index + NEW_LINE + \
              LT_JMP
        lt += AT + LT_NORM + str_index + NEW_LINE + JMP
        lt += LABEL_START + LT_X_NEG + str_index + LABEL_END
        lt += TEMP_TWO + SET_DATA + AT + LT_TRUE + str_index + NEW_LINE + \
              GE_JMP
        lt += LABEL_START + LT_NORM + str_index + LABEL_END
        lt += TEMP_ONE + SET_DATA + TEMP_TWO + SUB_D + AT + LT_TRUE + \
              str_index + NEW_LINE + LT_JMP
        lt += LABEL_START + LT_FALSE + str_index + LABEL_END
        lt += SET_D_FALSE + AT + LT_END + str_index + NEW_LINE + JMP
        lt += LABEL_START + LT_TRUE + str_index + LABEL_END
        lt += SET_D_TRUE
        lt += LABEL_START + LT_END + str_index + LABEL_END
        lt += STACK_POINTER + ADDRESS_STACK_HEAD + SET_M_TO_D
        self.LT_INDEX += 1
        return lt



def translate_file(file_path, code_writer):
    """Translate the current file"""
    commands = code_writer.parse_file(file_path)
    for i in range(len(commands)):
        code_writer.write_command(commands[i])


def translate_dir(arg):
    """Translate the files in a given directory"""
    files = []
    dir_path = Path(arg)
    for file in os.listdir(arg):
        if file.endswith(VM_SUFFIX):
            file_path = dir_path / file
            files.append((str(file_path), file.split('.')[0]))
    out_address = dir_path / dir_path.name
    code_writer = CodeWriter(str(out_address) + ASM_SUFFIX)
    for i in range(len(files)):
        code_writer.set_file_name(files[i][1])
        translate_file(files[i][0], code_writer)
    code_writer.write_to_file()


def main():
    # verify input files correctness:
    for i in range(1, len(sys.argv)):
        arg = sys.argv[i]
        if os.path.isdir(arg):
            translate_dir(arg)
        else:
            file_name = os.path.basename(os.path.splitext(arg)[0])
            code_writer = CodeWriter(arg.replace(VM_SUFFIX, ASM_SUFFIX))
            code_writer.set_file_name(file_name)
            translate_file(arg, code_writer)
            code_writer.write_to_file()


if __name__ == '__main__':
    main()
