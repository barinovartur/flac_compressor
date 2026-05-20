def crc8(data):
    # полином 0x07, начальное 0, побайтово, без финального xor
    c = 0
    for byte in data:
        c ^= byte
        for _ in range(8):
            if c & 0x80:
                c = ((c << 1) ^ 0x07) & 0xFF
            else:
                c = (c << 1) & 0xFF
    return c


def crc16(data):
    # полином 0x8005, начальное 0
    c = 0
    for byte in data:
        c ^= byte << 8
        for _ in range(8):
            if c & 0x8000:
                c = ((c << 1) ^ 0x8005) & 0xFFFF
            else:
                c = (c << 1) & 0xFFFF
    return c
