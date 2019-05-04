import struct
import abc
from enum import Enum
from typing import List, Union, Tuple, Dict


class ObjectCode:
    pass


class ByteCode:
    pass


class Instruction:
    pass


class Data:
    pass


class Operand:
    pass


class ObjectParameterType(Enum):
    Int8 = 0
    Int16 = 1
    Int32 = 2
    Float32 = 3
    String = 4


class ObjectParameter:
    input: bool
    output: bool
    type: ObjectParameterType

    def __init__(self, is_in, is_out, type):
        self.input = is_in
        self.output = is_out
        self.type = type

    def serialize(self) -> int:
        hex = 0x00
        if self.input:
            hex |= 0x80
        if self.output:
            hex |= 0x40
        hex |= self.type.value
        return hex


class PlainParams(Enum):
    Int8 = 0
    Int16 = 1
    Int32 = 2
    Float32 = 3
    String = 4
    Any = 5


class PlainParam:
    input: bool
    output: bool
    type: PlainParams
    name: str
    description: str

    def __init__(self, type, is_in, is_out, name, desc):
        self.type = type
        self.input = is_in
        self.output = is_out
        self.name = name
        self.description = desc


class LabelParam:
    name: str
    description: str

    def __init__(self, name, desc):
        self.name = name
        self.description = desc

    @property
    def input(self):
        return True

    @property
    def output(self):
        return False


class VariadicParam:
    input: bool
    output: bool
    type: PlainParams
    name: str
    description: str

    def __init__(self, type, is_in, is_out, name, desc):
        self.input = is_in
        self.output = is_out
        self.type = type
        self.name = name
        self.description = desc

    @property
    def typed(self) -> bool:
        return self.type != PlainParams.Any


class OpCode:
    ParamType = Union[PlainParam, LabelParam, VariadicParam]
    main_code: Tuple[str, int]
    sub_code: Union[Tuple[str, int], None]
    params: List[ParamType]
    description: str

    def __init__(self, main, sub, params, desc="?"):
        self.main_code = main
        self.sub_code = sub
        self.params = params
        self.description = desc


def TypeDecorator(something):
    mode_dict: Dict[Tuple[bool, bool], str] = {
        (True, False): 'IN',
        (False, True): 'OUT',
        (True, True): 'INOUT',
        (False, False): 'DUMMY'
    }
    type_dict: Dict[PlainParams, str] = {
        PlainParams.Int8: '8',
        PlainParams.Int16: '16',
        PlainParams.Int32: '32',
        PlainParams.String: 'S',
        PlainParams.Float32: 'F',
        PlainParams.Any: 'V'
    }
    for type, end in type_dict.items():
        for mode, start in mode_dict.items():
            def single_fn(name="?", desc="?"):
                return PlainParam(type=type, is_in=mode[0], is_out=mode[1], name=name, desc=desc)

            setattr(something, start + '_' + end, single_fn)

            def many_fn(name="?", desc="?"):
                return VariadicParam(type=type,
                                     is_in=mode[0],
                                     is_out=mode[1],
                                     name=name,
                                     desc=desc)

            setattr(something, start + "_" + end + "_MANY", many_fn)

    def label_fn(name="?", desc="?"):
        return LabelParam(name, desc)

    setattr(something, "LABEL", label_fn)


@TypeDecorator
class T:
    pass


OpCodes: List[OpCode] = []

OpCodes += [
    OpCode(("opERROR", 0x00), None,
           [

           ],
           "Terminate the current program and return failure"),

    OpCode(("opNOP", 0x01), None,
           [

           ],
           "Empty instruction"),

    OpCode(("opPROGRAM_STOP", 0x02), None,
           [
               T.IN_16("PRGID", "Program id (GUI_SLOT = all, CURRENT_SLOT = current)")
           ],
           "Stops specific program id slot"),

    OpCode(("opPROGRAM_START", 0x03), None,
           [
               T.IN_16("PRGID", "Program id"),
               T.IN_32("SIZE", "Size of image"),
               T.IN_32("*IP", "Address of image (value from opFILE(LOAD_IMAGE,..)  )"),
               T.IN_8("DEBUG", "Debug mode (0=normal, 1=debug, 2=don't execute)")
           ],
           "Start program id slot"),

    OpCode(("opOBJECT_STOP", 0x04), None,
           [
               T.IN_16("OBJID", "Object id")
           ],
           "Stops specific object"),

    OpCode(("opOBJECT_START", 0x05), None,
           [
               T.IN_16("OBJID", "Object id")
           ],
           "Start specific object"),

    OpCode(("opOBJECT_TRIG", 0x06), None,
           [
               T.IN_16("OBJID", "Object id")
           ],
           "Triggers object and run the object if fully triggered"),

    OpCode(("opOBJECT_WAIT", 0x07), None,
           [
               T.IN_16("OBJID", "Object id")
           ],
           "Wait until object has run"),

    OpCode(("opRETURN", 0x08), None,
           [

           ],
           "Return from byte code subroutine"),

    OpCode(("opCALL", 0x09), None,
           [
               T.IN_16("OBJID", "Object id"),
               T.IN_V_MANY("PARAMETERS", "Subcall arguments")
           ],
           "Calls byte code subroutine"),

    OpCode(("opOBJECT_END", 0x0A), None,
           [

           ],
           "Stops current object"),

    OpCode(("opSLEEP", 0x0B), None,
           [

           ],
           "Breaks execution of current VMTHREAD"),

    OpCode(("opPROGRAM_INFO", 0x0C), ("OBJ_STOP", 0),
           [
               T.IN_16("PRGID", "Program slot number"),
               T.IN_16("OBJID", "Object id")
           ],
           "Stop execution of a program object"),

    OpCode(("opPROGRAM_INFO", 0x0C), ("OBJ_START", 4),
           [
               T.IN_16("PRGID", "Program slot number"),
               T.IN_16("OBJID", "Object id")
           ],
           "Start execution of a program object"),

    OpCode(("opPROGRAM_INFO", 0x0C), ("GET_STATUS", 22),
           [
               T.IN_16("PRGID", "Program slot number"),
               T.OUT_8("DATA", "Program status")
           ],
           "Read current program status (RUNNING, WAITING, STOPPED, HALTED)"),

    OpCode(("opPROGRAM_INFO", 0x0C), ("GET_SPEED", 23),
           [
               T.IN_16("PRGID", "Program slot number"),
               T.OUT_32("DATA", "Program speed [instr/S]")
           ],
           "Get current program execution speed"),

    OpCode(("opPROGRAM_INFO", 0x0C), ("GET_PRGRESULT", 24),
           [
               T.IN_16("PRGID", "Program slot number"),
               T.OUT_8("DATA", "Program result [OK, BUSY, FAIL]")
           ],
           "Read program result"),

    OpCode(("opPROGRAM_INFO", 0x0C), ("SET_INSTR", 25),
           [
               T.IN_16("COUNT", "Instruction count")
           ],
           "Execute the current thread for the following number of instructions."),

    OpCode(("opLABEL", 0x0D), None,
           [
               T.LABEL("NO", "Label number")
           ],
           "Mark this position with a label (32 max per program)"),

    OpCode(("opPROBE", 0x0E), None,
           [
               T.IN_16("PRGID", "Program slot number"),
               T.IN_16("OBJID", "Object id (zero means globals)"),
               T.IN_32("OFFSET", "Offset (start from)"),
               T.IN_32("SIZE", "Size (length of dump) zero means all (max 1024)")
           ],
           "Display globals or object locals on terminal"),

    OpCode(("opDO", 0x0F), None,
           [
               T.IN_16("PRGID", "Program slot number"),
               T.IN_16("*IMAGE", "Address of image"),
               T.IN_16("*GLOBAL", "Address of global variables"),
           ],
           "Run byte code snippet"),
]

current_code = 0x10
for op in ["ADD", "SUB", "MUL", "DIV"]:
    options = {PlainParams.Int8: "8",
               PlainParams.Int16: "16",
               PlainParams.Int32: "32",
               PlainParams.Float32: "F"}
    for typ, end in options.items():
        OpCodes.append(OpCode(
            (f"op{op}{end}", current_code), None,
            [
                PlainParam(type=typ, is_in=True, is_out=False, name="SOURCE1", desc="First operand"),
                PlainParam(type=typ, is_in=True, is_out=False, name="SOURCE2", desc="Second operand"),
                PlainParam(type=typ, is_in=False, is_out=True, name="DESTINATION", desc="Destination operand"),
            ],
            f"Arithmetic {op} two DATA_{end} numbers and store the result."))
        current_code += 1

for op in ["OR", "AND", "XOR", "RL"]:
    suffixes = {PlainParams.Int8: "8",
                PlainParams.Int16: "16",
                PlainParams.Int32: "32"}
    for typ, end in suffixes.items():
        OpCodes.append(OpCode(
            (f"op{op}{end}", current_code), None,
            [
                PlainParam(type=typ, is_in=True, is_out=False, name="SOURCE1", desc="First operand"),
                PlainParam(type=typ, is_in=True, is_out=False, name="SOURCE2", desc="Second operand"),
                PlainParam(type=typ, is_in=False, is_out=True, name="DESTINATION", desc="Destination operand"),
            ],
            f"Bitwise {op} two DATA_{end} numbers and store the result."))
        current_code += 1
    current_code += 1  # LEGO did not use the remaining non-float slot

OpCodes += [
    OpCode(("opINIT_BYTES", 0x2F), None,
           [
               T.OUT_8("DESTINATION", "First element in DATA8 array to be initiated"),
               T.IN_8_MANY("SOURCE", "Variadic array with which to initialize the array")
           ],
           "Move LENGTH number of DATA8 from BYTE STREAM to memory DESTINATION START")
]

current_code = 0x30
suffixes: Dict[PlainParams, str] = {PlainParams.Int8: "8",
                                    PlainParams.Int16: "16",
                                    PlainParams.Int32: "32",
                                    PlainParams.Float32: "F"}
for t1, n1 in suffixes.values():
    for t2, n2 in suffixes.values():
        OpCodes.append(OpCode(
            (f"opMOVE{n1}_{n2}", current_code), None,
            [
                PlainParam(type=t1, is_in=True, is_out=False, name="SOURCE", desc="Source value"),
                PlainParam(type=t2, is_in=False, is_out=True, name="DESTINATION", desc="Destination value"),
            ],
            f"Move a DATA_{n1} value to a DATA_{n2} slot."))
        current_code += 1

OpCodes += [
    OpCode(("opJR", 0x40), None,
           [
               T.IN_32("OFFSET", "Branch target, relative to ?")
           ],
           "Branch unconditionally relative"),
    OpCode(("opJR_FALSE", 0x41), None,
           [
               T.IN_8("FLAG", "Flag upon which to decide the action"),
               T.IN_32("OFFSET", "Branch target, relative to ?")
           ],
           "Branch relative if FLAG is FALSE (zero)"),
    OpCode(("opJR_TRUE", 0x42), None,
           [
               T.IN_8("FLAG", "Flag upon which to decide the action"),
               T.IN_32("OFFSET", "Branch target, relative to ?")
           ],
           "Branch relative if FLAG is TRUE (non zero)"),
    OpCode(("opJR_NAN", 0x43), None,
           [
               T.IN_F("VALUE", "Value upon which to decide the action"),
               T.IN_32("OFFSET", "Branch target, relative to ?")
           ],
           "Branch relative if VALUE is NAN (not a number)"),
]

current_code = 0x44
adjacent_code = 0x64
suffixes: Dict[PlainParams, str] = {PlainParams.Int8: "8",
                                    PlainParams.Int16: "16",
                                    PlainParams.Int32: "32",
                                    PlainParams.Float32: "F"}
ops: List[str] = ["LT", "GT", "EQ", "NEQ", "LTEQ", "GTEQ"]
for op in ops:
    for typ, end in suffixes:
        OpCodes.append(OpCode(
            (f"opCP_{op}{end}", current_code), None,
            [
                PlainParam(type=typ, is_in=True, is_out=False, name="LEFT", desc="First operand"),
                PlainParam(type=typ, is_in=True, is_out=False, name="RIGHT", desc="Second operand"),
                T.OUT_8("FLAG", "1 if condition holds, 0 otherwise")
            ],
            f"If LEFT is {op} RIGTH - set FLAG"))
        OpCodes.append(OpCode(
            (f"opJR_{op}{end}", adjacent_code), None,
            [
                PlainParam(type=typ, is_in=True, is_out=False, name="LEFT", desc="First operand"),
                PlainParam(type=typ, is_in=True, is_out=False, name="RIGHT", desc="Second operand"),
                T.IN_32("OFFSET", "Branch target, relative to ?")
            ],
            f"Branch relative OFFSET if LEFT is {op} RIGHT"))
        current_code += 1
        adjacent_code += 1

for typ, end in suffixes:
    OpCodes.append(OpCode(
        (f"opSELECT{end}", current_code), None,
        [
            T.IN_8("FLAG", "True -> select first, False -> select second"),
            PlainParam(type=typ, is_in=True, is_out=False, name="SOURCE1", desc="First value (True)"),
            PlainParam(type=typ, is_in=True, is_out=False, name="SOURCE2", desc="Second value (False)"),
            PlainParam(type=typ, is_in=False, is_out=True, name="*RESULT", desc="Destination"),
        ],
        f"Select a DATA_{end} depending on bool value of a flag"))
    current_code += 1

OpCodes += [
    OpCode(("opSYSTEM", 0x60), None,
           [
               T.IN_8("COMMAND", "Command string (HND)"),
               T.OUT_32("STATUS", "Return status of the command")
           ],
           "Executes a system command"),
    OpCode(("opPORT_CNV_OUTPUT", 0x61), None,
           [
               T.IN_32("PortIn", "EncodedPortNumber"),
               T.OUT_8("Layer", "Layer"),
               T.OUT_8("Bitfield", "Bitfield"),
               T.OUT_8("Inverted", "True if left/right motor are inverted (ie, C&A)"),
           ],
           "Convert encoded port to Layer and Bitfield"),
    OpCode(("opPORT_CNV_INPUT", 0x62), None,
           [
               T.IN_32("PortIn", "EncodedPortNumber"),
               T.OUT_8("Layer", "Layer"),
               T.OUT_8("PortOut", "0-index port for use with VM commands")
           ],
           "Convert encoded port to Layer and Port"),
    OpCode(("opNOTE_TO_FREQ", 0x63), None,
           [
               T.IN_8("NOTE", "Note string (e.c. 'C#4')"),
               T.OUT_16("FREQ", "Frequency [Hz]")
           ],
           "Convert note to tone"),
]
