from flac_encoder.fixed_predictor import compute_residuals_fixed, estimate_fixed_size
from flac_encoder.lpc_predictor import find_best_lpc_config
from flac_encoder.rice_coder import encode_residuals


def _write_verbatim(samples, bps, writer):
    # 1 бит pad, 6 бит тип 000001, 1 бит wasted
    writer.write_bit(0)
    writer.write_bits(0b000001, 6)
    writer.write_bit(0)
    for s in samples:
        writer.write_signed(s, bps)


def _write_constant(value, bps, writer):
    writer.write_bit(0)
    writer.write_bits(0b000000, 6)
    writer.write_bit(0)
    writer.write_signed(value, bps)


def _write_fixed(samples, order, bps, writer):
    # тип FIXED порядка o это 0b001000 | o
    writer.write_bit(0)
    writer.write_bits(0b001000 | order, 6)
    writer.write_bit(0)
    for i in range(order):
        writer.write_signed(samples[i], bps)
    res = compute_residuals_fixed(samples, order)
    encode_residuals(res, order, writer)


def _write_lpc(samples, order, qcoefs, shift, residuals, bps, writer):
    # тип LPC порядка o это 0b100000 | (o-1), порядки 1..32
    precision = 12
    writer.write_bit(0)
    writer.write_bits(0b100000 | (order - 1), 6)
    writer.write_bit(0)
    for i in range(order):
        writer.write_signed(samples[i], bps)
    # precision - 1 в 4 битах
    writer.write_bits(precision - 1, 4)
    # shift в 5 битах знаковое
    writer.write_signed(shift, 5)
    # коэффициенты по precision бит каждый
    for c in qcoefs:
        writer.write_signed(c, precision)
    encode_residuals(residuals, order, writer)


def encode_subframe(samples, bps, writer):
    n = len(samples)

    # CONSTANT, если все сэмплы одинаковые
    all_same = True
    first = samples[0]
    for s in samples:
        if s != first:
            all_same = False
            break
    if all_same:
        _write_constant(first, bps, writer)
        return

    verbatim_size = 8 + n * bps
    best_size = verbatim_size
    best_kind = ("VERBATIM", None)

    # FIXED порядки 0..4
    for order in range(5):
        if order >= n:
            break
        size = estimate_fixed_size(samples, order, bps)
        if size < best_size:
            best_size = size
            best_kind = ("FIXED", order)

    # LPC порядки 1..12
    lpc = find_best_lpc_config(samples, bps, max_order=12)
    if lpc is not None:
        order, qcoefs, shift, residuals, size = lpc
        if size < best_size:
            best_size = size
            best_kind = ("LPC", order, qcoefs, shift, residuals)

    if best_kind[0] == "VERBATIM":
        _write_verbatim(samples, bps, writer)
    elif best_kind[0] == "FIXED":
        _write_fixed(samples, best_kind[1], bps, writer)
    else:
        _, order, qcoefs, shift, residuals = best_kind
        _write_lpc(samples, order, qcoefs, shift, residuals, bps, writer)
