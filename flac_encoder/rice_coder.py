def zigzag(n):
    # положительные в чётные, отрицательные в нечётные
    if n >= 0:
        return n << 1
    return ((-n) << 1) - 1


def _rice_bits(residuals_zigzag, k):
    total = 0
    for u in residuals_zigzag:
        total += (u >> k) + 1 + k
    return total


def find_best_k(residuals_zigzag):
    # перебор k от 0 до 14, возвращаем лучший и размер в битах
    best_k = 0
    best_b = _rice_bits(residuals_zigzag, 0)
    for k in range(1, 15):
        b = _rice_bits(residuals_zigzag, k)
        if b < best_b:
            best_b = b
            best_k = k
    return best_k, best_b


def encode_residuals(residuals, predictor_order, writer):
    # вся секция RESIDUAL при partition_order=0
    zz = [zigzag(r) for r in residuals]
    k, _ = find_best_k(zz)

    # coding method 00 для 4-битного k
    writer.write_bits(0b00, 2)
    writer.write_bits(0, 4)
    writer.write_bits(k, 4)
    for u in zz:
        q = u >> k
        writer.write_unary(q)
        if k > 0:
            writer.write_bits(u & ((1 << k) - 1), k)
