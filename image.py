import struct
import abc
from typing import List

IHDR_LEN = 4 + 4 + 2 + 2 + 4
OHDR_LEN = 4 + 2 + 2 + 4
SIGNATURE = b'LEGO'


class VmObject(abc.ABC):
    def __init__(self):
        super().__init__()
        self.id = -1
        self.name = "unknown"
        self.offset = -1
        self.bytecode = b''

    def _generate_header(self, offset, owner, triggers, locals):
        self.offset = offset
        return struct.pack('<IHHI', offset, owner, triggers, locals)

    @abc.abstractmethod
    def generate_header(self, offset):
        pass


class VmThread(VmObject):
    def __init__(self):
        super().__init__()
        self.locals = 0

    def generate_header(self, offset):
        return self._generate_header(offset, 0, 0, self.locals)


class SubCall(VmObject):
    def __init__(self):
        super().__init__()
        self.locals = 0

    def generate_header(self, offset):
        return self._generate_header(offset, 0, 1, self.locals)


class Block(VmObject):
    def __init__(self, owner, triggers):
        super().__init__()
        self.owner = owner
        self.triggers = triggers

    def generate_header(self, offset):
        return self._generate_header(offset, self.owner, self.triggers, 0)


class Alias(VmObject):
    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def generate_header(self, offset):
        return self._generate_header(self.parent.offset)


class Image:
    globals: int
    version: float
    objects: List[VmObject]

    def __init__(self):
        self.objects = []
        self.version = 1.09
        self.globals = 0

    def _image_header(self, image_size) -> bytes:
        assert len(SIGNATURE) == 4, "Incorrect file signature specified"
        return SIGNATURE + struct.pack('<IHHI',
                                       image_size,
                                       int(self.version * 100),
                                       len(self.objects),
                                       self.globals)

    def _serialize_objects(self) -> bytes:
        hdrs = b''
        code = b''
        base = IHDR_LEN + OHDR_LEN * len(self.objects)

        obj: VmObject
        for obj in self.objects:
            start = base + len(code)
            code += obj.bytecode
            hdrs += obj.generate_header(start)

        return hdrs + code

    def serialize(self) -> bytes:
        objs = self._serialize_objects()

        total = IHDR_LEN + len(objs)
        ihdr = self._image_header(total)
        return ihdr + objs
