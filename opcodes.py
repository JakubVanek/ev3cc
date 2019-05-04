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
    Code = Tuple[str, int]

    main_code: Code
    sub_code: Union[Code, None]
    params: List[ParamType]
    description: str

    def __init__(self, main: Code, sub: Union[Code, None], desc: str, params: List[ParamType]):
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
           "Terminate the current program and return failure",
           [

           ]),

    OpCode(("opNOP", 0x01), None,
           "Empty instruction",
           [

           ]),

    OpCode(("opPROGRAM_STOP", 0x02), None,
           "Stops specific program id slot",
           [
               T.IN_16("PRGID", "Program id (GUI_SLOT = all, CURRENT_SLOT = current)")
           ]),

    OpCode(("opPROGRAM_START", 0x03), None,
           "Start program id slot",
           [
               T.IN_16("PRGID", "Program id"),
               T.IN_32("SIZE", "Size of image"),
               T.IN_32("*IP", "Address of image (value from opFILE(LOAD_IMAGE,..)  )"),
               T.IN_8("DEBUG", "Debug mode (0=normal, 1=debug, 2=don't execute)")
           ]),

    OpCode(("opOBJECT_STOP", 0x04), None,
           "Stops specific object",
           [
               T.IN_16("OBJID", "Object id")
           ]),

    OpCode(("opOBJECT_START", 0x05), None,
           "Start specific object",
           [
               T.IN_16("OBJID", "Object id")
           ]),

    OpCode(("opOBJECT_TRIG", 0x06), None,
           "Triggers object and run the object if fully triggered",
           [
               T.IN_16("OBJID", "Object id")
           ]),

    OpCode(("opOBJECT_WAIT", 0x07), None,
           "Wait until object has run",
           [
               T.IN_16("OBJID", "Object id")
           ]),

    OpCode(("opRETURN", 0x08), None,
           "Return from byte code subroutine",
           [

           ]),

    OpCode(("opCALL", 0x09), None,
           "Calls byte code subroutine",
           [
               T.IN_16("OBJID", "Object id"),
               T.IN_V_MANY("PARAMETERS", "Subcall arguments")
           ]),

    OpCode(("opOBJECT_END", 0x0A), None,
           "Stops current object",
           [

           ]),

    OpCode(("opSLEEP", 0x0B), None,
           "Breaks execution of current VMTHREAD",
           [

           ]),

    OpCode(("opPROGRAM_INFO", 0x0C), ("OBJ_STOP", 0),
           "Stop execution of a program object",
           [
               T.IN_16("PRGID", "Program slot number"),
               T.IN_16("OBJID", "Object id")
           ]),

    OpCode(("opPROGRAM_INFO", 0x0C), ("OBJ_START", 4),
           "Start execution of a program object",
           [
               T.IN_16("PRGID", "Program slot number"),
               T.IN_16("OBJID", "Object id")
           ]),

    OpCode(("opPROGRAM_INFO", 0x0C), ("GET_STATUS", 22),
           "Read current program status (RUNNING, WAITING, STOPPED, HALTED)",
           [
               T.IN_16("PRGID", "Program slot number"),
               T.OUT_8("DATA", "Program status")
           ]),

    OpCode(("opPROGRAM_INFO", 0x0C), ("GET_SPEED", 23),
           "Get current program execution speed",
           [
               T.IN_16("PRGID", "Program slot number"),
               T.OUT_32("DATA", "Program speed [instr/S]")
           ]),

    OpCode(("opPROGRAM_INFO", 0x0C), ("GET_PRGRESULT", 24),
           "Read program result",
           [
               T.IN_16("PRGID", "Program slot number"),
               T.OUT_8("DATA", "Program result [OK, BUSY, FAIL]")
           ]),

    OpCode(("opPROGRAM_INFO", 0x0C), ("SET_INSTR", 25),
           "Execute the current thread for the following number of instructions.",
           [
               T.IN_16("COUNT", "Instruction count")
           ]),

    OpCode(("opLABEL", 0x0D), None,
           "Mark this position with a label (32 max per program)",
           [
               T.LABEL("NO", "Label number")
           ]),

    OpCode(("opPROBE", 0x0E), None,
           "Display globals or object locals on terminal",
           [
               T.IN_16("PRGID", "Program slot number"),
               T.IN_16("OBJID", "Object id (zero means globals)"),
               T.IN_32("OFFSET", "Offset (start from)"),
               T.IN_32("SIZE", "Size (length of dump) zero means all (max 1024)")
           ]),

    OpCode(("opDO", 0x0F), None,
           "Run byte code snippet",
           [
               T.IN_16("PRGID", "Program slot number"),
               T.IN_16("*IMAGE", "Address of image"),
               T.IN_16("*GLOBAL", "Address of global variables"),
           ]),
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
            f"Arithmetic {op} two DATA_{end} numbers and store the result.",
            [
                PlainParam(type=typ, is_in=True, is_out=False, name="SOURCE1", desc="First operand"),
                PlainParam(type=typ, is_in=True, is_out=False, name="SOURCE2", desc="Second operand"),
                PlainParam(type=typ, is_in=False, is_out=True, name="DESTINATION", desc="Destination operand"),
            ]))
        current_code += 1

for op in ["OR", "AND", "XOR", "RL"]:
    suffixes = {PlainParams.Int8: "8",
                PlainParams.Int16: "16",
                PlainParams.Int32: "32"}
    for typ, end in suffixes.items():
        OpCodes.append(OpCode(
            (f"op{op}{end}", current_code), None,
            f"Bitwise {op} two DATA_{end} numbers and store the result.",
            [
                PlainParam(type=typ, is_in=True, is_out=False, name="SOURCE1", desc="First operand"),
                PlainParam(type=typ, is_in=True, is_out=False, name="SOURCE2", desc="Second operand"),
                PlainParam(type=typ, is_in=False, is_out=True, name="DESTINATION", desc="Destination operand"),
            ]))
        current_code += 1
    current_code += 1  # LEGO did not use the remaining non-float slot

OpCodes += [
    OpCode(("opINIT_BYTES", 0x2F), None,
           "Move LENGTH number of DATA8 from BYTE STREAM to memory DESTINATION START",
           [
               T.OUT_8("DESTINATION", "First element in DATA8 array to be initiated"),
               T.IN_8_MANY("SOURCE", "Variadic array with which to initialize the array")
           ])
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
            f"Move a DATA_{n1} value to a DATA_{n2} slot.",
            [
                PlainParam(type=t1, is_in=True, is_out=False, name="SOURCE", desc="Source value"),
                PlainParam(type=t2, is_in=False, is_out=True, name="DESTINATION", desc="Destination value"),
            ]))
        current_code += 1

OpCodes += [
    OpCode(("opJR", 0x40), None,
           "Branch unconditionally relative",
           [
               T.IN_32("OFFSET", "Branch target, relative to ?")
           ]),

    OpCode(("opJR_FALSE", 0x41), None,
           "Branch relative if FLAG is FALSE (zero)",
           [
               T.IN_8("FLAG", "Flag upon which to decide the action"),
               T.IN_32("OFFSET", "Branch target, relative to ?")
           ]),

    OpCode(("opJR_TRUE", 0x42), None,
           "Branch relative if FLAG is TRUE (non zero)",
           [
               T.IN_8("FLAG", "Flag upon which to decide the action"),
               T.IN_32("OFFSET", "Branch target, relative to ?")
           ]),

    OpCode(("opJR_NAN", 0x43), None,
           "Branch relative if VALUE is NAN (not a number)",
           [
               T.IN_F("VALUE", "Value upon which to decide the action"),
               T.IN_32("OFFSET", "Branch target, relative to ?")
           ]),
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
            f"If LEFT is {op} RIGTH - set FLAG",
            [
                PlainParam(type=typ, is_in=True, is_out=False, name="LEFT", desc="First operand"),
                PlainParam(type=typ, is_in=True, is_out=False, name="RIGHT", desc="Second operand"),
                T.OUT_8("FLAG", "1 if condition holds, 0 otherwise")
            ]))

        OpCodes.append(OpCode(
            (f"opJR_{op}{end}", adjacent_code), None,
            f"Branch relative OFFSET if LEFT is {op} RIGHT",
            [
                PlainParam(type=typ, is_in=True, is_out=False, name="LEFT", desc="First operand"),
                PlainParam(type=typ, is_in=True, is_out=False, name="RIGHT", desc="Second operand"),
                T.IN_32("OFFSET", "Branch target, relative to ?")
            ]))

        current_code += 1
        adjacent_code += 1

for typ, end in suffixes:

    OpCodes.append(OpCode(
        (f"opSELECT{end}", current_code), None,
        f"Select a DATA_{end} depending on bool value of a flag",
        [
            T.IN_8("FLAG", "True -> select first, False -> select second"),
            PlainParam(type=typ, is_in=True, is_out=False, name="SOURCE1", desc="First value (True)"),
            PlainParam(type=typ, is_in=True, is_out=False, name="SOURCE2", desc="Second value (False)"),
            PlainParam(type=typ, is_in=False, is_out=True, name="*RESULT", desc="Destination"),
        ]))

    current_code += 1

OpCodes += [
    OpCode(("opSYSTEM", 0x60), None,
           "Executes a system command",
           [
               T.IN_8("COMMAND", "Command string (HND)"),
               T.OUT_32("STATUS", "Return status of the command")
           ]),

    OpCode(("opPORT_CNV_OUTPUT", 0x61), None,
           "Convert encoded port to Layer and Bitfield",
           [
               T.IN_32("PortIn", "EncodedPortNumber"),
               T.OUT_8("Layer", "Layer"),
               T.OUT_8("Bitfield", "Bitfield"),
               T.OUT_8("Inverted", "True if left/right motor are inverted (ie, C&A)"),
           ]),

    OpCode(("opPORT_CNV_INPUT", 0x62), None,
           "Convert encoded port to Layer and Port",
           [
               T.IN_32("PortIn", "EncodedPortNumber"),
               T.OUT_8("Layer", "Layer"),
               T.OUT_8("PortOut", "0-index port for use with VM commands")
           ]),

    OpCode(("opNOTE_TO_FREQ", 0x63), None,
           "Convert note to tone",
           [
               T.IN_8("NOTE", "Note string (e.c. 'C#4')"),
               T.OUT_16("FREQ", "Frequency [Hz]")
           ]),
]

OpCodes += [
    OpCode(("opINFO", 0x7C), ("SET_ERROR", 1),
           "Push new error to VM error queue.",
           [
               T.IN_8("NUMBER", "Error number")
           ]),

    OpCode(("opINFO", 0x7C), ("GET_ERROR", 2),
           "Pop an error from VM error queue.",
           [
               T.OUT_8("NUMBER", "Error number")
           ]),

    OpCode(("opINFO", 0x7C), ("ERRORTEXT", 3),
           "Convert error number to text string",
           [
               T.IN_8("NUMBER", "Error number"),
               T.IN_8("LENGTH", "Maximal length of string returned (-1 = no check)"),
               T.OUT_8("DESTINATION", "String variable or handle to string")
           ]),

    OpCode(("opINFO", 0x7C), ("GET_VOLUME", 4),
           "Get brick volume",
           [
               T.OUT_8("VALUE", "Volume [0..100%]")
           ]),

    OpCode(("opINFO", 0x7C), ("SET_VOLUME", 5),
           "Set brick volume",
           [
               T.IN_8("VALUE", "Volume [0..100%]")
           ]),

    OpCode(("opINFO", 0x7C), ("GET_MINUTES", 6),
           "Get inactive time before entering sleep",
           [
               T.OUT_8("VALUE", "Minutes to sleep [0..120min] (0 = ~)")
           ]),

    OpCode(("opINFO", 0x7C), ("SET_MINUTES", 7),
           "Set inactive time before entering sleep",
           [
               T.IN_8("VALUE", "Minutes to sleep [0..120min] (0 = ~)")
           ]),
]

OpCodes += [
    OpCode(("opSTRINGS", 0x7D), ("GET_SIZE", 1),
           "Get size of string (not including zero termination)",
           [
               T.IN_8("SOURCE", "String variable or handle to string"),
               T.OUT_16("SIZE", "Size")
           ]),

    OpCode(("opSTRINGS", 0x7D), ("ADD", 2),
           "Add two strings (SOURCE1 + SOURCE2 -> DESTINATION)",
           [
               T.IN_8("SOURCE1", "First string variable or handle to string"),
               T.IN_8("SOURCE2", "Second string variable or handle to string"),
               T.OUT_8("DESTINATION", "Destination string variable or handle to string")
           ]),

    OpCode(("opSTRINGS", 0x7D), ("COMPARE", 3),
           "Compare two strings",
           [
               T.IN_8("SOURCE1", "First string variable or handle to string"),
               T.IN_8("SOURCE2", "Second string variable or handle to string"),
               T.OUT_8("RESULT", "Result (0 = not equal, 1 = equal)")
           ]),

    OpCode(("opSTRINGS", 0x7D), ("DUPLICATE", 5),
           "Duplicate a string (SOURCE1 -> DESTINATION)",
           [
               T.IN_8("SOURCE1", "Source string variable or handle to string"),
               T.OUT_8("DESTINATION", "Destination string variable or handle to string")
           ]),

    OpCode(("opSTRINGS", 0x7D), ("VALUE_TO_STRING", 6),
           "Convert floating point value to a string (strips trailing zeroes)",
           [
               T.IN_F("VALUE", "Value to write (if 'nan' up to 4 dashes is returned: '----')"),
               T.IN_8("FIGURES", "Total number of figures inclusive decimal point (FIGURES < 0 -> Left adjusted)"),
               T.IN_8("DECIMALS", "Number of decimals"),
               T.OUT_8("DESTINATION", "Destination string variable or handle to string")
           ]),

    OpCode(("opSTRINGS", 0x7D), ("STRING_TO_VALUE", 7),
           "Convert string to floating point value",
           [
               T.IN_8("SOURCE", "Source string variable or handle to string"),
               T.OUT_F("VALUE", "Value")
           ]),

    OpCode(("opSTRINGS", 0x7D), ("STRIP", 8),
           "Strip a string for spaces (SOURCE1 -> DESTINATION)",
           [
               T.IN_8("SOURCE", "Source string variable or handle to string"),
               T.OUT_8("DESTINATION", "Destination string variable or handle to string")
           ]),

    OpCode(("opSTRINGS", 0x7D), ("NUMBER_TO_STRING", 9),
           "Convert integer value to a string",
           [
               T.IN_16("VALUE", "Value to write"),
               T.IN_8("FIGURES", "Total number of figures"),
               T.OUT_8("DESTINATION", "String variable or handle to string")
           ]),

    OpCode(("opSTRINGS", 0x7D), ("SUB", 10),
           "Return DESTINATION: a substring from SOURCE1 that starts were SOURCE2 ends",
           [
               T.IN_8("SOURCE1", "First string variable or handle to string"),
               T.IN_8("SOURCE2", "Second string variable or handle to string"),
               T.OUT_8("DESTINATION", "Destination string variable or handle to string")
           ]),

    OpCode(("opSTRINGS", 0x7D), ("VALUE_FORMATTED", 11),
           "Convert floating point value to a formatted string",
           [
               T.IN_F("VALUE", "Value to write"),
               T.IN_8("FORMAT", "Format string variable or handle to string"),
               T.IN_8("SIZE", "Total size of destination string"),
               T.OUT_8("DESTINATION", "Destination string variable or handle to string")
           ]),

    OpCode(("opSTRINGS", 0x7D), ("NUMBER_FORMATTED", 12),
           "Convert integer number to a formatted string",
           [
               T.IN_32("NUMBER", "Number to write"),
               T.IN_8("FORMAT", "Format string variable or handle to string"),
               T.IN_8("SIZE", "Total size of destination string"),
               T.OUT_8("DESTINATION", "Destination string variable or handle to string")
           ]),
]

OpCodes += [
    OpCode(("opMEMORY_WRITE", 0x7E), None,
           "Write VM memory",
           [
               T.IN_16("PRGID", "Program slot number (must be running)"),
               T.IN_16("OBJID", "Object id (zero means globals)"),
               T.IN_32("OFFSET", "Offset (start from)"),
               T.IN_32("SIZE", "Size (length of array to write)"),
               T.IN_8("ARRAY", "First element of DATA8 array to write")
           ]),

    OpCode(("opMEMORY_READ", 0x7F), None,
           "Read VM memory",
           [
               T.IN_16("PRGID", "Program slot number (must be running)"),
               T.IN_16("OBJID", "Object id (zero means globals)"),
               T.IN_32("OFFSET", "Offset (start from)"),
               T.IN_32("SIZE", "Size (length of array to read)"),
               T.OUT_8("ARRAY", "First element of DATA8 array to receive data")
           ]),

    OpCode(("opUI_FLUSH", 0x80), None,
           "User Interface flush buffers",
           [

           ])
]
