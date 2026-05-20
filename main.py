import argparse
import sys
import time

from flac_encoder.encoder import encode_file

sys.stdout.reconfigure(encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="FLAC-подобный энкодер")
    p.add_argument("input", help="входной WAV файл, 16-бит PCM")
    p.add_argument("output", help="выходной FLAC файл")
    p.add_argument("--blocksize", type=int, default=4096,
                   help="размер блока в сэмплах (по умолчанию 4096)")
    p.add_argument("--max-lpc", type=int, default=12,
                   help="максимальный порядок LPC (по умолчанию 12)")
    args = p.parse_args()

    t0 = time.time()
    stats = encode_file(args.input, args.output,
                        blocksize=args.blocksize,
                        max_lpc_order=args.max_lpc)
    dt = time.time() - t0

    print("файл:", args.input, "->", args.output)
    print("сэмплов:", stats["total_samples"], "каналов:", stats["channels"],
          "sr:", stats["sample_rate"], "bps:", stats["bps"])
    print("фреймов:", stats["frames"], "blocksize:", stats["blocksize"])
    print("исходный размер:", stats["input_size"], "байт")
    print("сжатый размер:", stats["output_size"], "байт")
    print("коэффициент сжатия: %.3f" % stats["ratio"])
    print("время: %.2f сек" % dt)


if __name__ == "__main__":
    main()
