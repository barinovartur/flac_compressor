class BitWriter:
    def __init__(self):
        self.buf = bytearray()
        self.cur = 0
        self.nbits = 0
        self.total = 0

    def write_bit(self, b):
        self.cur = (self.cur << 1) | (b & 1)
        self.nbits += 1
        self.total += 1
        if self.nbits == 8:
            self.buf.append(self.cur)
            self.cur = 0
            self.nbits = 0

    def write_bits(self, value, n):
        # старший бит первым
        if n <= 0:
            return
        value &= (1 << n) - 1
        for i in range(n - 1, -1, -1):
            self.write_bit((value >> i) & 1)

    def write_signed(self, value, n):
        # двоичное дополнение в n битах
        if value < 0:
            value += (1 << n)
        self.write_bits(value, n)

    def write_bytes(self, data):
        if self.nbits == 0:
            self.buf.extend(data)
            self.total += 8 * len(data)
        else:
            for byte in data:
                self.write_bits(byte, 8)

    def write_unary(self, n):
        # n нулей и потом единица
        for _ in range(n):
            self.write_bit(0)
        self.write_bit(1)

    def align_to_byte(self):
        if self.nbits != 0:
            self.write_bits(0, 8 - self.nbits)

    def get_bytes(self):
        # вызывать после align_to_byte если нужны все биты
        if self.nbits != 0:
            return bytes(self.buf) + bytes([self.cur << (8 - self.nbits)])
        return bytes(self.buf)

    def bits_written(self):
        return self.total
