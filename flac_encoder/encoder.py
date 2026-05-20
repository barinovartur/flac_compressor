import hashlib

from flac_encoder.wav_reader import read_wav
from flac_encoder.bit_writer import BitWriter
from flac_encoder.frame import encode_frame
from flac_encoder.streaminfo import build_streaminfo
from flac_encoder.decorrelation import select_stereo_mode


def encode_file(input_wav, output_flac, blocksize=4096, max_lpc_order=12):
    sr, bps, ch, total, samples, raw = read_wav(input_wav)

    md5 = hashlib.md5(raw).digest()

    frames = []
    min_frame = None
    max_frame = 0
    min_block = blocksize
    max_block = 0

    pos = 0
    frame_no = 0
    while pos < total:
        n = min(blocksize, total - pos)

        if ch == 1:
            mode = "mono"
            block_channels = [samples[0][pos:pos + n]]
        else:
            # выбираем лучшую декорреляцию для этого блока
            l = samples[0][pos:pos + n]
            r = samples[1][pos:pos + n]
            mode, sub0, sub1 = select_stereo_mode(l, r)
            block_channels = [sub0, sub1]

        # fixed blocking, в номере фрейма храним порядковый номер
        w = BitWriter()
        encode_frame(block_channels, frame_no, sr, mode, bps, n, w)
        fb = w.get_bytes()
        frames.append(fb)

        if min_frame is None or len(fb) < min_frame:
            min_frame = len(fb)
        if len(fb) > max_frame:
            max_frame = len(fb)
        if n < min_block:
            min_block = n
        if n > max_block:
            max_block = n

        pos += n
        frame_no += 1

    if min_frame is None:
        min_frame = 0

    si = build_streaminfo(min_block, max_block, min_frame, max_frame,
                          sr, ch, bps, total, md5)

    with open(output_flac, "wb") as f:
        f.write(b"fLaC")
        # last=1, type=0, length=34
        f.write(bytes([0x80, 0x00, 0x00, 0x22]))
        f.write(si)
        for fb in frames:
            f.write(fb)

    out_size = 4 + 4 + 34 + sum(len(x) for x in frames)
    in_size = len(raw)
    return {"input_size": in_size,
            "output_size": out_size,
            "ratio": in_size / out_size if out_size else 0,
            "frames": len(frames),
            "blocksize": blocksize,
            "sample_rate": sr,
            "channels": ch,
            "bps": bps,
            "total_samples": total}
