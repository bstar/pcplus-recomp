"""Lossless PCPlus 2.01 dialing-directory codec, proved against program IO.

Pure byte codec: no implicit file IO, migration, enum coercion or code-page guess.
Length alone does not identify a PCPLUS.DIR file. See docs/DIRECTORY.md.
"""
from dataclasses import dataclass
import struct

RECORD_SIZE = 114
RECORD_COUNT = 200
DIAL_CODE_COUNT = 10
DIAL_CODE_SIZE = 25
HEADER_SIZE = DIAL_CODE_COUNT * DIAL_CODE_SIZE
DIRECTORY_SIZE = HEADER_SIZE + RECORD_COUNT * RECORD_SIZE
STRING_FIELDS = {
    'name': (0x00, 25), 'number': (0x19, 21), 'script': (0x34, 9),
    'last_call_date': (0x3d, 9), 'password': (0x4b, 11),
    'keyboard_file': (0x56, 9), 'meta_file': (0x5f, 9), 'note_file': (0x69, 9),
}
WORD_FIELDS = {'baud_index': 0x2e, 'completed_call_count': 0x46}
BYTE_FIELDS = {
    'parity_index': 0x30, 'data_bits': 0x31, 'stop_bits': 0x32,
    'duplex_index': 0x33, 'protocol_index': 0x48, 'terminal_id': 0x49,
    'dialing_mode': 0x4a, 'port_override': 0x68,
}
BAUD_RATES = (300, 1200, 2400, 4800, 9600, 19200, 38400, 57600, 115200)
PARITIES = ('NONE', 'ODD', 'EVEN', 'MARK', 'SPACE')
DUPLEXES = ('FULL', 'HALF')
DIALING_MODES = ('MODEM', 'DIRECT')


def _integer(value, maximum):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError(f'Expected an unsigned integer in 0..{maximum}')
    return value


def _cstring(region):
    if b'\0' not in region:
        raise ValueError('Unterminated field; original bytes remain available')
    return region.split(b'\0', 1)[0]


def _replace_string(image, offset, capacity, value):
    if not isinstance(value, (bytes, bytearray, memoryview)):
        raise TypeError('Use bytes; choose the text encoding explicitly')
    value = bytes(value)
    if b'\0' in value or len(value) >= capacity:
        raise ValueError(f'Expected at most {capacity - 1} non-NUL bytes')
    output = bytearray(image)
    # Old bytes after the terminator are preserved, as are all other fields.
    output[offset:offset + len(value) + 1] = value + b'\0'
    return bytes(output)


@dataclass(frozen=True)
class DirectoryRecord201:
    _image: bytes

    def __post_init__(self):
        object.__setattr__(self, '_image', bytes(self._image))
        if len(self._image) != RECORD_SIZE:
            raise ValueError(f'Expected exactly {RECORD_SIZE} bytes')

    def to_bytes(self):
        return self._image

    def string(self, name):
        offset, size = STRING_FIELDS[name]
        return _cstring(self._image[offset:offset + size])

    def with_string(self, name, value):
        offset, size = STRING_FIELDS[name]
        return DirectoryRecord201(_replace_string(self._image, offset, size, value))

    def integer(self, name):
        if name in WORD_FIELDS:
            return struct.unpack_from('<H', self._image, WORD_FIELDS[name])[0]
        return self._image[BYTE_FIELDS[name]]

    def with_integer(self, name, value):
        output = bytearray(self._image)
        if name in WORD_FIELDS:
            struct.pack_into('<H', output, WORD_FIELDS[name], _integer(value, 65535))
        else:
            output[BYTE_FIELDS[name]] = _integer(value, 255)
        # Unknown enum values are deliberately retained; this edits storage only.
        return DirectoryRecord201(output)

    @classmethod
    def default(cls):
        """Re-author the verified program's blank-record template, not user data."""
        return (cls(bytes(RECORD_SIZE)).with_integer('baud_index', 2)
                .with_integer('data_bits', 8).with_integer('stop_bits', 1)
                .with_string('last_call_date', b'00/00/00')
                .with_integer('protocol_index', 4).with_integer('terminal_id', 6))


def _record_index(number):
    if type(number) is not int or not 1 <= number <= RECORD_COUNT:
        raise ValueError('Directory entries use original one-based numbers 1..200')
    return HEADER_SIZE + (number - 1) * RECORD_SIZE


def _dial_code_index(letter):
    if not isinstance(letter, str) or len(letter) != 1 or not 'A' <= letter <= 'J':
        raise ValueError('Expected a dialing-code letter A..J')
    return (ord(letter) - ord('A')) * DIAL_CODE_SIZE


@dataclass(frozen=True)
class DialingDirectory201:
    _image: bytes

    def __post_init__(self):
        object.__setattr__(self, '_image', bytes(self._image))
        if len(self._image) < DIRECTORY_SIZE:
            raise ValueError(f'Directory requires at least {DIRECTORY_SIZE} bytes')

    @classmethod
    def from_bytes(cls, data, *, allow_trailing=False):
        data = bytes(data)
        if len(data) != DIRECTORY_SIZE and not allow_trailing:
            raise ValueError(f'Expected exactly {DIRECTORY_SIZE} bytes; format identification is external')
        return cls(data)

    def to_bytes(self):
        return self._image

    @property
    def trailing_bytes(self):
        """Opaque suffix, if explicitly accepted; original reader ignores it."""
        return self._image[DIRECTORY_SIZE:]

    def record(self, number):
        offset = _record_index(number)
        return DirectoryRecord201(self._image[offset:offset + RECORD_SIZE])

    def with_record(self, number, record):
        if not isinstance(record, DirectoryRecord201):
            raise TypeError('Expected DirectoryRecord201')
        offset = _record_index(number)
        return DialingDirectory201(self._image[:offset] + record.to_bytes() + self._image[offset + RECORD_SIZE:])

    def dial_code(self, letter):
        offset = _dial_code_index(letter)
        return _cstring(self._image[offset:offset + DIAL_CODE_SIZE])

    def with_dial_code(self, letter, value):
        return DialingDirectory201(_replace_string(self._image, _dial_code_index(letter), DIAL_CODE_SIZE, value))

    @classmethod
    def blank(cls):
        return cls(bytes(HEADER_SIZE) + DirectoryRecord201.default().to_bytes() * RECORD_COUNT)
