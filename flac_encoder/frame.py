from flac_encoder.bit_writer import BitWriter
from flac_encoder.crc import crc8, crc16
from flac_encoder.subframe import encode_subframe


def encode_utf8_number(value, writer):
    # FLAC-вариант UTF-8 для целого, пишется уже когда writer выровнен по байту
    if value < 0x80:
        writer.write_bytes(bytes([value]))
        return
    # подбираем минимальное число байт
    # n байт: первый байт начинается с n единиц и одного нуля, остальные с 10
    # ёмкости: 2 байта 11 бит, 3 байта 16 бит, 4 байта 21 бит, 5 байт 26, 6 байт 31, 7 байт 36
    ranges = [11, 16, 21, 26, 31, 36]
    nbytes = 0
    for i, bits in enumerate(ranges):
        if value < (1 << bits):
            nbytes = i + 2
            break

    out = bytearray()
    # хвостовые байты по 6 бит снизу
    tail = []
    v = value
    for _ in range(nbytes - 1):
        tail.append(0x80 | (v & 0x3F))
        v >>= 6
    # головной байт: nbytes единиц, ноль, потом оставшиеся биты
    head_prefix_bits = nbytes  # столько единиц
    head_mask = ((1 << (8 - head_prefix_bits - 1)) - 1)
    head_top = (0xFF << (8 - head_prefix_bits)) & 0xFF
    head = head_top | (v & head_mask)
    out.append(head)
    for b in reversed(tail):
        out.append(b)
    writer.write_bytes(bytes(out))


def _blocksize_code(blocksize):
    # вернём (code, extra_bits, extra_value)
    # для нашего основного кейса 4096 это 0b1100, без доп байт
    table = {192: (0b0001, 0, 0),
             576: (0b0010, 0, 0), 1152: (0b0011, 0, 0),
             2304: (0b0100, 0, 0), 4608: (0b0101, 0, 0),
             256: (0b1000, 0, 0), 512: (0b1001, 0, 0),
             1024: (0b1010, 0, 0), 2048: (0b1011, 0, 0),
             4096: (0b1100, 0, 0), 8192: (0b1101, 0, 0),
             16384: (0b1110, 0, 0), 32768: (0b1111, 0, 0)}
    if blocksize in table:
        return table[blocksize]
    # иначе пишем через дополнительное поле, 8 бит если влезает, иначе 16
    if blocksize - 1 < 256:
        return (0b0110, 8, blocksize - 1)
    return (0b0111, 16, blocksize - 1)


def _sample_rate_code(sr):
    if sr == 88200:
        return (0b0001, 0, 0)
    if sr == 176400:
        return (0b0010, 0, 0)
    if sr == 192000:
        return (0b0011, 0, 0)
    if sr == 8000:
        return (0b0100, 0, 0)
    if sr == 16000:
        return (0b0101, 0, 0)
    if sr == 22050:
        return (0b0110, 0, 0)
    if sr == 24000:
        return (0b0111, 0, 0)
    if sr == 32000:
        return (0b1000, 0, 0)
    if sr == 44100:
        return (0b1001, 0, 0)
    if sr == 48000:
        return (0b1010, 0, 0)
    if sr == 96000:
        return (0b1011, 0, 0)
    # иначе берём из STREAMINFO
    return (0b0000, 0, 0)


def _channel_assignment(mode):
    return {"mono": 0b0000,
            "LR":   0b0001,
            "LS":   0b1000,
            "RS":   0b1001,
            "MS":   0b1010}[mode]


def encode_frame(channels_data, frame_number, sample_rate, channel_mode, bps, blocksize, writer):
    # сначала строим заголовок без CRC-8 в отдельный writer
    hdr = BitWriter()
    hdr.write_bits(0b11111111111110, 14)  # sync
    hdr.write_bit(0)                       # reserved
    hdr.write_bit(0)                       # blocking strategy fixed

    bs_code, bs_extra_bits, bs_extra_val = _blocksize_code(blocksize)
    sr_code, sr_extra_bits, sr_extra_val = _sample_rate_code(sample_rate)
    hdr.write_bits(bs_code, 4)
    hdr.write_bits(sr_code, 4)
    hdr.write_bits(_channel_assignment(channel_mode), 4)

    bps_code = {8: 0b001, 12: 0b010, 16: 0b100, 20: 0b101, 24: 0b110}[bps]
    hdr.write_bits(bps_code, 3)
    hdr.write_bit(0)  # reserved

    # номер фрейма в utf8-подобной кодировке, уже выровнено по байту
    encode_utf8_number(frame_number, hdr)

    if bs_extra_bits:
        hdr.write_bits(bs_extra_val, bs_extra_bits)
    if sr_extra_bits:
        hdr.write_bits(sr_extra_val, sr_extra_bits)

    header_bytes = hdr.get_bytes()
    c8 = crc8(header_bytes)

    # собираем весь фрейм в temp writer чтобы потом посчитать CRC-16
    frm = BitWriter()
    frm.write_bytes(header_bytes)
    frm.write_bytes(bytes([c8]))

    # субфреймы
    # для LS/RS/MS у "side" канала битовая глубина +1
    side_idx = None
    if channel_mode == "LS" or channel_mode == "MS":
        side_idx = 1
    elif channel_mode == "RS":
        side_idx = 0

    for i, ch in enumerate(channels_data):
        sub_bps = bps + 1 if i == side_idx else bps
        encode_subframe(ch, sub_bps, frm)

    frm.align_to_byte()

    body = frm.get_bytes()
    c16 = crc16(body)

    writer.write_bytes(body)
    writer.write_bits(c16, 16)
