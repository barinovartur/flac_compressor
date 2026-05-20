from flac_encoder.bit_writer import BitWriter


def build_streaminfo(min_block, max_block, min_frame, max_frame,
                     sample_rate, channels, bps, total_samples, md5_bytes):
    # 34 байта тела STREAMINFO без 4 байтового заголовка метаблока
    w = BitWriter()
    w.write_bits(min_block, 16)
    w.write_bits(max_block, 16)
    w.write_bits(min_frame, 24)
    w.write_bits(max_frame, 24)
    w.write_bits(sample_rate, 20)
    w.write_bits(channels - 1, 3)
    w.write_bits(bps - 1, 5)
    w.write_bits(total_samples, 36)
    w.write_bytes(md5_bytes)
    return w.get_bytes()
