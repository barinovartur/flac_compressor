import wave
import struct


def read_wav(path):
    wf = wave.open(path, "rb")
    sr = wf.getframerate()
    bps = wf.getsampwidth() * 8
    ch = wf.getnchannels()
    n = wf.getnframes()
    raw = wf.readframes(n)
    wf.close()

    # в WAV сэмплы interleaved: L R L R ...
    fmt = "<" + "h" * (n * ch)
    flat = struct.unpack(fmt, raw)

    samples = []
    for c in range(ch):
        samples.append(list(flat[c::ch]))

    return sr, bps, ch, n, samples, raw
