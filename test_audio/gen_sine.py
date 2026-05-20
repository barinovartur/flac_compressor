import wave
import struct
import math
import os


def gen(path, sr=44100, duration=2.0, freq=440.0, amp=10000, channels=1):
    n = int(sr * duration)
    data = []
    for i in range(n):
        v = int(amp * math.sin(2 * math.pi * freq * i / sr))
        for _ in range(channels):
            data.append(v)
    wf = wave.open(path, "wb")
    wf.setnchannels(channels)
    wf.setsampwidth(2)
    wf.setframerate(sr)
    wf.writeframes(struct.pack("<" + "h" * len(data), *data))
    wf.close()


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    gen(os.path.join(here, "sine_mono.wav"), channels=1)
    gen(os.path.join(here, "sine_stereo.wav"), channels=2)
    print("сгенерировано")
