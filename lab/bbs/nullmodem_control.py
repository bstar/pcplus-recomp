"""DOSBox-X nontransparent null-modem framing, separate from Telnet.

Upstream src/hardware/serialport/nullmodem.cpp readChar/setRTSDTR:
FF FF is literal FF; FF flags carries RTS/CTS bit0, DTR/DSR bit1, break bit2.
"""


class Control:
    def __init__(self, lines):
        self.pending = False
        self.lines = lines

    def feed(self, data):
        output = bytearray()
        for value in data:
            if self.pending:
                self.pending = False
                if value == 255:
                    output.append(255)
                else:
                    self.lines(bool(value & 1), bool(value & 2), bool(value & 4))
            elif value == 255:
                self.pending = True
            else:
                output.append(value)
        return bytes(output)

    @staticmethod
    def encode(data):
        return data.replace(b'\xff', b'\xff\xff')


class Writer:
    def __init__(self, writer):
        self.writer = writer

    def write(self, data):
        self.writer.write(Control.encode(data))

    async def drain(self):
        await self.writer.drain()

    def close(self):
        self.writer.close()
