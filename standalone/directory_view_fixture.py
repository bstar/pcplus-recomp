"""Public synthetic directory bytes; no private configuration or original data."""
def fixture():
    image = bytearray(23050)
    for entry in range(1, 201):
        at = 250 + (entry - 1) * 114
        name = b'LoSs oF CoNtRoL' if entry == 1 else b'FINAL 200' if entry == 200 else f'Node {entry:03}'.encode()
        if entry == 2:
            name = b'A\x01\x7f\xdb\xff'
        image[at:at + len(name)] = name
        image[at + 25:at + 29] = b'555\0'
        image[at + 46:at + 48] = bytes([5, 0])
        image[at + 49:at + 51] = bytes([8, 1])
        image[at + 72:at + 75] = bytes([4, 6, 0])
        image[at + 52:at + 59] = b'SECRETA'
        image[at + 75:at + 85] = b'HIDDENPASS'
    return bytes(image)
