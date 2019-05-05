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

OpCodes += [
    OpCode(("opUI_READ", 0x81), ("GET_VBATT", 1),
           "Read battery voltage",
           [
               T.OUT_F("VALUE", "Battery voltage [V]")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_IBATT", 2),
           "Read battery current",
           [
               T.OUT_F("VALUE", "Battery current [A]")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_OS_VERS", 3),
           "Get os version string",
           [
               T.IN_8("LENGTH", "Maximal length of string returned (-1 = no check)"),
               T.OUT_8("DESTINATION", "String variable or handle to string")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_EVENT", 4),
           "Get event (internal use)",
           [
               T.OUT_8("EVENT", "Event [1,2 = Bluetooth events]")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_TBATT", 5),
           "Read battery temperature",
           [
               T.OUT_F("VALUE", "Battery temperature rise [C]")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_IINT", 6),
           "Read battery current integral (used for protection?)",
           [
               T.OUT_F("VALUE", "Integrated current [A]")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_IMOTOR", 7),
           "Read current going through the motors",
           [
               T.OUT_F("VALUE", "Motor current [A]")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_STRING", 8),
           "Get string from terminal",
           [
               T.IN_8("LENGTH", "Maximal length of string returned"),
               T.OUT_8("DESTINATION", "String variable or handle to string")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_HW_VERS", 9),
           "Get hardware version string",
           [
               T.IN_8("LENGTH", "Maximal length of string returned (-1 = no check)"),
               T.OUT_8("DESTINATION", "String variable or handle to string")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_FW_VERS", 10),
           "Get firmware version string",
           [
               T.IN_8("LENGTH", "Maximal length of string returned (-1 = no check)"),
               T.OUT_8("DESTINATION", "String variable or handle to string")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_FW_BUILD", 11),
           "Get firmware build string",
           [
               T.IN_8("LENGTH", "Maximal length of string returned (-1 = no check)"),
               T.OUT_8("DESTINATION", "String variable or handle to string")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_OS_BUILD", 12),
           "Get os build string",
           [
               T.IN_8("LENGTH", "Maximal length of string returned (-1 = no check)"),
               T.OUT_8("DESTINATION", "String variable or handle to string")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_ADDRESS", 13),
           "Get address from terminal (used for debugging)",
           [
               T.OUT_32("VALUE", "Address from lms_cmdin")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_CODE", 14),
           "Get code snippet from terminal (used for debugging)",
           [
               T.IN_32("LENGTH", "Maximal code stream length"),
               T.OUT_32("*IMAGE", "Address of image"),
               T.OUT_32("GLOBAL", "Address of global variables"),
               T.OUT_8("FLAG", "Flag tells if image is ready to execute [1=ready]")
           ]),

    OpCode(("opUI_READ", 0x81), ("KEY", 15),
           "Get key from terminal (used for debugging)",
           [
               T.OUT_8("VALUE", "Key value from lms_cmdin (0 = no key)")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_SHUTDOWN", 16),
           "Get and clear shutdown flag (internal use)",
           [
               T.OUT_8("FLAG", "Flag [1=want to shutdown]")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_WARNING", 17),
           "Read warning bit field (internal use)",
           [
               T.OUT_8("WARNINGS", "Bit field containing various warnings")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_LBATT", 18),
           "Get battery level in %",
           [
               T.OUT_8("PCT", "Battery level [0..100]")
           ]),

    OpCode(("opUI_READ", 0x81), ("TEXTBOX_READ", 21),
           "Read line from text box",
           [
               T.IN_8("TEXT", "First character in text box text (must be zero terminated)"),
               T.IN_32("SIZE", "Maximal text size (including zero termination)"),
               T.IN_8("DELIMITERS", "Delimiter code"),
               T.IN_8("LENGTH", "Maximal length of string returned (-1 = no check)"),
               T.IN_16("LINE", "Selected line number"),
               T.OUT_8("DESTINATION", "String variable or handle to string")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_VERSION", 26),
           "Get version string",
           [
               T.IN_8("LENGTH", "Maximal length of string returned (-1 = no check)"),
               T.OUT_8("DESTINATION", "String variable or handle to string")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_IP", 27),
           "Get IP address string",
           [
               T.IN_8("LENGTH", "Maximal length of string returned (-1 = no check)"),
               T.OUT_8("DESTINATION", "String variable or handle to string")
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_POWER", 29),
           "Get brick power info in a single call",
           [
               T.OUT_F("VBATT", "Battery voltage [V]"),
               T.OUT_F("IBATT", "Battery current [A]"),
               T.OUT_F("IINT", "Battery current integral [A]"),
               T.OUT_F("IMOTOR", "Motor current [A]"),
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_SDCARD", 30),
           "Check SD card presence",
           [
               T.OUT_8("STATE", "SD card present [0..1]"),
               T.OUT_32("TOTAL", "Kbytes in total"),
               T.OUT_32("FREE", "Kbytes free"),
           ]),

    OpCode(("opUI_READ", 0x81), ("GET_USBSTICK", 31),
           "Check USB stick presence",
           [
               T.OUT_8("STATE", "USB stick present [0..1]"),
               T.OUT_32("TOTAL", "Kbytes in total"),
               T.OUT_32("FREE", "Kbytes free"),
           ]),
]

OpCodes += [
    OpCode(("opUI_WRITE", 0x82), ("WRITE_FLUSH", 1),
           "Flush terminal buffer",
           [

           ]),

    OpCode(("opUI_WRITE", 0x82), ("FLOATVALUE", 2),
           "Log a float to terminal",
           [
               T.IN_F("VALUE", "Value to write"),
               T.IN_8("FIGURES", "Total number of figures inclusive decimal point"),
               T.IN_8("DECIMALS", "Number of decimals")
           ]),

    OpCode(("opUI_WRITE", 0x82), ("STAMP", 3),
           "Log a timestamp to terminal",
           [
               T.IN_8("SOURCE", "User-specified Stamp ID")
           ]),

    OpCode(("opUI_WRITE", 0x82), ("PUT_STRING", 8),
           "Log a string to terminal",
           [
               T.IN_8("STRING", "First character in string to write")
           ]),

    OpCode(("opUI_WRITE", 0x82), ("CODE", 14),
           "Log binary data to terminal",
           [
               T.IN_8("ARRAY", "First byte in byte array to write"),
               T.IN_32("LENGTH", "Length of array")
           ]),

    OpCode(("opUI_WRITE", 0x82), ("DOWNLOAD_END", 15),
           "Send to brick when file down load is completed (plays sound and updates the UI browser)",
           [

           ]),

    OpCode(("opUI_WRITE", 0x82), ("SCREEN_BLOCK", 16),
           "Set or clear screen block status (if screen blocked - all graphical screen action are disabled)",
           [
               T.IN_8("STATUS", "Value [0 = normal,1 = blocked]"),
           ]),

    OpCode(("opUI_WRITE", 0x82), ("ALLOW_PULSE", 17),
           "Enable pixel blinking for debugging",
           [
               T.IN_8("ENABLE", "Value [0 = disabled,1 = enabled]"),
           ]),

    OpCode(("opUI_WRITE", 0x82), ("SET_PULSE", 18),
           "Trigger pixel blink",
           [
               T.IN_8("MASK", "Bitmask for blinking"),
           ]),

    OpCode(("opUI_WRITE", 0x82), ("TEXTBOX_APPEND", 21),
           "Append line of text at the bottom of a text box",
           [
               T.IN_8("TEXT", "First character in text box text (must be zero terminated)"),
               T.IN_32("SIZE", "Maximal text size (including zero termination)"),
               T.IN_8("DELIMITERS", "Delimiter code"),
               T.IN_8("SOURCE", "String variable or handle to string to append"),
           ]),

    OpCode(("opUI_WRITE", 0x82), ("SET_BUSY", 22),
           "Assert/deassert WARNING_BUSY warning flag",
           [
               T.IN_8("VALUE", "Value [0,1]"),
           ]),

    OpCode(("opUI_WRITE", 0x82), ("VALUE8", 9),
           "Log number to terminal",
           [
               T.IN_8("VALUE", "Value to write"),
           ]),

    OpCode(("opUI_WRITE", 0x82), ("VALUE16", 10),
           "Log number to terminal",
           [
               T.IN_8("VALUE", "Value to write"),
           ]),

    OpCode(("opUI_WRITE", 0x82), ("VALUE32", 11),
           "Log number to terminal",
           [
               T.IN_8("VALUE", "Value to write"),
           ]),

    OpCode(("opUI_WRITE", 0x82), ("VALUEF", 12),
           "Log number to terminal",
           [
               T.IN_8("VALUE", "Value to write"),
           ]),

    OpCode(("opUI_WRITE", 0x82), ("INIT_RUN", 25),
           "Start the 'Mindstorms' 'run' screen",
           [

           ]),

    OpCode(("opUI_WRITE", 0x82), ("UPDATE_RUN", 26),
           "Neither documented nor implemented",
           [

           ]),

    OpCode(("opUI_WRITE", 0x82), ("LED", 27),
           "Set brick LED pattern",
           [
               T.IN_8("PATTERN", "LED pattern (see leJOS or LEGO doc)"),
           ]),

    OpCode(("opUI_WRITE", 0x82), ("POWER", 29),
           "Set the shutdown-after-unload flag for d_power.ko",
           [
               T.IN_8("PATTERN", "Value [0,1]"),
           ]),

    OpCode(("opUI_WRITE", 0x82), ("TERMINAL", 31),
           "Enable/disable terminal stdout output",
           [
               T.IN_8("STATE", "Value [0 = Off,1 = On]"),
           ]),

    OpCode(("opUI_WRITE", 0x82), ("GRAPH_SAMPLE", 30),
           "Update tick to scroll graph horizontally in memory when drawing graph in 'scope' mode",
           [

           ]),

    OpCode(("opUI_WRITE", 0x82), ("SET_TESTPIN", 24),
           "Set test pin level",
           [
               T.IN_8("STATE", "Value [0 = low,1 = high]"),
           ]),
]

OpCodes += [
    OpCode(("opUI_BUTTON", 0x83), ("SHORTPRESS", 1),
           "Read and reset button short-press status",
           [
               T.IN_8("BUTTON", "Button code"),
               T.OUT_8("STATE", "Button has been pressed (0 = no, 1 = yes)"),
           ]),

    OpCode(("opUI_BUTTON", 0x83), ("LONGPRESS", 2),
           "Read and reset button long-press status",
           [
               T.IN_8("BUTTON", "Button code"),
               T.OUT_8("STATE", "Button has been hold down(0 = no, 1 = yes)"),
           ]),

    OpCode(("opUI_BUTTON", 0x83), ("WAIT_FOR_PRESS", 3),
           "Stop thread until any button is pressed",
           [

           ]),

    OpCode(("opUI_BUTTON", 0x83), ("FLUSH", 4),
           "Reset all present button state",
           [

           ]),

    OpCode(("opUI_BUTTON", 0x83), ("PRESS", 5),
           "Simulate button press",
           [
               T.IN_8("BUTTON", "Button code"),
           ]),

    OpCode(("opUI_BUTTON", 0x83), ("RELEASE", 6),
           "Simulate button release",
           [
               T.IN_8("BUTTON", "Button code"),
           ]),

    OpCode(("opUI_BUTTON", 0x83), ("GET_HORZ", 7),
           "Read horizontal key axis",
           [
               T.IN_16("VALUE", "Horizontal arrows data (-1 = left, +1 = right, 0 = not pressed)"),
           ]),

    OpCode(("opUI_BUTTON", 0x83), ("GET_VERT", 8),
           "Read vertical key axis",
           [
               T.IN_16("VALUE", "Vertical arrows data (-1 = up, +1 = down, 0 = not pressed)"),
           ]),

    OpCode(("opUI_BUTTON", 0x83), ("PRESSED", 9),
           "Read button pressed status",
           [
               T.IN_8("BUTTON", "Button code"),
               T.OUT_8("STATE", "Button is pressed (0 = no, 1 = yes)"),
           ]),

    OpCode(("opUI_BUTTON", 0x83), ("SET_BACK_BLOCK", 10),
           "Set UI back button blocked flag",
           [
               T.IN_8("BLOCKED", "New flag value (0 = not blocked, 1 = blocked)"),
           ]),

    OpCode(("opUI_BUTTON", 0x83), ("GET_BACK_BLOCK", 11),
           "Get UI back button blocked flag",
           [
               T.IN_8("BLOCKED", "Current flag value (0 = not blocked, 1 = blocked)"),
           ]),

    OpCode(("opUI_BUTTON", 0x83), ("TESTSHORTPRESS", 12),
           "Read button short-press status, without reset",
           [
               T.IN_8("BUTTON", "Button code"),
               T.OUT_8("STATE", "Button has been hold down(0 = no, 1 = yes)"),
           ]),

    OpCode(("opUI_BUTTON", 0x83), ("TESTLONGPRESS", 13),
           "Read button long-press status, without reset",
           [
               T.IN_8("BUTTON", "Button code"),
               T.OUT_8("STATE", "Button has been hold down(0 = no, 1 = yes)"),
           ]),

    OpCode(("opUI_BUTTON", 0x83), ("GET_BUMBED", 14),
           "Read and reset button bump status",
           [
               T.IN_8("BUTTON", "Button code"),
               T.OUT_8("STATE", "Button has been pressed (0 = no, 1 = yes)"),
           ]),

    OpCode(("opUI_BUTTON", 0x83), ("GET_CLICK", 15),
           "Get and clear click sound request (internal use only)",
           [
               T.OUT_8("CLICK", "Click sound request (0 = no, 1 = yes)"),
           ]),
]

OpCodes += [
    OpCode(("opUI_DRAW", 0x84), ("UPDATE", 0),
           "Refresh statusbar & screen",
           [

           ]),

    OpCode(("opUI_DRAW", 0x84), ("CLEAN", 1),
           "Reset font & clear screen",
           [

           ]),

    OpCode(("opUI_DRAW", 0x84), ("PIXEL", 2),
           "Draw a pixel",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("LINE", 3),
           "Draw a line",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_16("X1", "X end cord [0..LCD_WIDTH]"),
               T.IN_16("Y1", "Y end cord [0..LCD_HEIGHT]"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("CIRCLE", 4),
           "Draw a circle",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_16("R", "Radius"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("TEXT", 5),
           "Draw some text",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_16("STRING", "First character in string to draw"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("ICON", 6),
           "Draw an icon",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_8("TYPE", "Icon type (pool)"),
               T.IN_8("NO", "Icon number ID"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("PICTURE", 7),
           "Draw an image",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_32("*IP", "Address of picture"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("VALUE", 8),
           "Draw a float value",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_F("VALUE", "Value to write"),
               T.IN_8("FIGURES", "Total number of figures inclusive decimal point"),
               T.IN_8("DECIMALS", "Number of decimals"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("FILLRECT", 9),
           "Fill a rectangle",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_16("X1", "X size [0..LCD_WIDTH - X0]"),
               T.IN_16("Y1", "Y size [0..LCD_HEIGHT - Y0]"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("RECT", 10),
           "Draw a rectangle",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_16("X1", "X size [0..LCD_WIDTH - X0]"),
               T.IN_16("Y1", "Y size [0..LCD_HEIGHT - Y0]"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("NOTIFICATION", 11),
           "Draw a notification window",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_8("ICON1", "First icon"),
               T.IN_8("ICON2", "Second icon"),
               T.IN_8("ICON3", "Third icon"),
               T.IN_8("STRING", "First character in notification string"),
               T.IN_8("*STATE", "State 0 = INIT"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("QUESTION", 12),
           "Draw a question window",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_8("ICON1", "First icon"),
               T.IN_8("ICON2", "Second icon"),
               T.IN_8("STRING", "First character in notification string"),
               T.IN_8("*STATE", "State 0 = NO, 1 = OK"),
               T.OUT_8("OK", "Answer 0 = NO, 1 = OK, -1 = SKIP"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("KEYBOARD", 13),
           "Draw a keyboard",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_8("ICON1", "First icon"),
               T.IN_8("LENGTH", "Maximal string length"),
               T.IN_8("DEFAULT", "Default string (0 = none)"),
               T.IN_8("*CHARSET", "Internal use (must be a variable initialised by a 'valid character set')"),
               T.OUT_8("STRING", "First character in string receiving keyboard input"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("BROWSE", 14),
           "Draw a browser",
           [
               T.IN_8("TYPE", "Browser type"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_16("X1", "X size [0..LCD_WIDTH]"),
               T.IN_16("Y1", "Y size [0..LCD_HEIGHT]"),
               T.IN_8("LENGTH", "Maximal string length"),
               T.OUT_8("TYPE",
                       "Item type (folder, byte code file, sound file, ...)(must be a zero initialised variable)"),
               T.OUT_8("STRING", "First character in string receiving keyboard input"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("VERTBAR", 15),
           "Draw a vertical bar",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_16("X1", "X size [0..LCD_WIDTH]"),
               T.IN_16("Y1", "Y size [0..LCD_HEIGHT]"),
               T.IN_16("MIN", "Minimum value"),
               T.IN_16("MAX", "Maximum value"),
               T.IN_16("ACT", "Actual value"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("INVERSERECT", 16),
           "Invert a rectangle on-screen",
           [
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_16("X1", "X size [0..LCD_WIDTH - X0]"),
               T.IN_16("Y1", "Y size [0..LCD_HEIGHT - Y0]"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("SELECT_FONT", 17),
           "Select font type; font will change to 0 when UPDATE is called",
           [
               T.IN_8("TYPE", "Font type [0..2]"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("TOPLINE", 18),
           "Enable/disable top status line",
           [
               T.IN_8("ENABLE", "Enable top status line (0 = disabled, 1 = enabled)"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("FILLWINDOW", 19),
           "Fill a Y-delimited window",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR] (Color != BG_COLOR and FG_COLOR -> test pattern)"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_16("Y1", "Y size [0..LCD_HEIGHT]"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("SCROLL", 20),
           "Scroll up the on-screen graphics",
           [
               T.IN_16("Y", "Scroll by Y lines [0..LCD_HEIGHT]"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("DOTLINE", 21),
           "Draw a dotted line",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_16("X1", "X end [0..LCD_WIDTH]"),
               T.IN_16("Y1", "Y end [0..LCD_HEIGHT]"),
               T.IN_16("ON", "On pixels"),
               T.IN_16("OFF", "Off pixels"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("VIEW_VALUE", 22),
           "Draw a special view for float values?",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_F("VALUE", "Value to write"),
               T.IN_8("FIGURES", "Total number of figures inclusive decimal point"),
               T.IN_8("DECIMALS", "Number of decimals"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("VIEW_UNIT", 23),
           "Draw a special view for float values with units?",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_F("VALUE", "Value to write"),
               T.IN_8("FIGURES", "Total number of figures inclusive decimal point"),
               T.IN_8("DECIMALS", "Number of decimals"),
               T.IN_8("LENGTH", "Maximal string length"),
               T.IN_8("STRING", "First character in string to draw"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("FILLCIRCLE", 24),
           "Draw a special view for float values?",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_16("R", "Radius"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("STORE", 25),
           "Store LcdSafe to a LCD save pool",
           [
               T.IN_8("NO", "Level number"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("RESTORE", 26),
           "Restore LcdSafe from a LCD save pool",
           [
               T.IN_8("NO", "Level number (N=0 -> Saved screen just before run)"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("ICON_QUESTION", 27),
           "Draw a question window?",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_8("*STATE", "State 0 = INIT"),
               T.IN_32("ICONS", "bitfield with icons"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("BMPFILE", 28),
           "Draw an image from file",
           [
               T.IN_8("COLOR", "Color [BG_COLOR..FG_COLOR]"),
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_8("NAME", "First character in filename (character string)"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("POPUP", 29),
           "Toggle a popup from this program/object",
           [
               T.IN_8("OPEN", "True -> open, False -> close"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("GRAPH_SETUP", 30),
           "Initialize a graph window",
           [
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("X1", "X size [0..(LCD_WIDTH - X0)]"),
               T.IN_8("ITEMS", "Number of datasets in arrays"),
               T.IN_16("OFFSET", "DATA16 array (handle) containing Y start cord [0..LCD_HEIGHT]"),
               T.IN_16("SPAN", "DATA16 array (handle) containing Y size [0..(LCD_HEIGHT - hOFFSET[])]"),
               T.IN_F("MIN", "DATAF array (handle) containing min values"),
               T.IN_F("MAX", "DATAF array (handle) containing max values"),
               T.IN_F("SAMPLE", "DATAF array (handle) containing sample values"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("GRAPH_DRAW", 31),
           "Draw a part of a graph",
           [
               T.IN_8("VIEW", "Dataset number to view (0=all)"),
               T.OUT_F("ACTUAL", "Last datapoint?"),
               T.OUT_F("LOWEST", "Minimum datapoint?"),
               T.OUT_F("HIGHEST", "Maximum datapoint?"),
               T.OUT_F("AVERAGE", "Average datapoint?"),
           ]),

    OpCode(("opUI_DRAW", 0x84), ("TEXTBOX", 32),
           "Draws and controls a text box (one long string containing characters and line delimiters) on the screen",
           [
               T.IN_16("X0", "X start cord [0..LCD_WIDTH]"),
               T.IN_16("Y0", "Y start cord [0..LCD_HEIGHT]"),
               T.IN_16("X1", "X size [0..LCD_WIDTH]"),
               T.IN_16("Y1", "Y size [0..LCD_HEIGHT]"),
               T.IN_8("TEXT", "First character in text box text (must be zero terminated)"),
               T.IN_32("SIZE", "Maximal text size (including zero termination)"),
               T.IN_8("DELIMITERS", "Delimiter code"),
               T.IN_8("LINE", "Selected line number"),
           ]),
]

OpCodes += [
    OpCode(("opTIMER_WAIT", 0x85), None,
           "Setup timer to wait TIME mS",
           [
               T.IN_32("TIME", "Time to wait [mS]"),
               T.IN_32("TIMER", "Variable used for timing")
           ]),

    OpCode(("opTIMER_READY", 0x86), None,
           "Wait for timer ready (wait for timeout)",
           [
               T.IN_32("TIMER", "Variable used for timing")
           ]),

    OpCode(("opTIMER_READ", 0x87), None,
           "Read free running timer [mS]",
           [
               T.IN_32("TIME", "Time to wait [mS]"),
               T.OUT_32("TIME", "Value")
           ]),

    OpCode(("opTIMER_READ_US", 0x8F), None,
           "Read free running timer [uS]",
           [
               T.OUT_32("TIME", "Value")
           ])
]
