from flac_encoder.rice_coder import zigzag, find_best_k


def compute_residuals_fixed(samples, order):
    # фиксированные предсказатели FLAC, остатки начиная с индекса order
    # коэффициенты это знакочередующиеся биномиальные, треугольник Паскаля
    res = []
    n = len(samples)
    if order == 0:
        return list(samples)
    if order == 1:
        for i in range(1, n):
            res.append(samples[i] - samples[i-1])
        return res
    if order == 2:
        for i in range(2, n):
            res.append(samples[i] - 2*samples[i-1] + samples[i-2])
        return res
    if order == 3:
        for i in range(3, n):
            res.append(samples[i] - 3*samples[i-1] + 3*samples[i-2] - samples[i-3])
        return res
    # order == 4
    for i in range(4, n):
        res.append(samples[i] - 4*samples[i-1] + 6*samples[i-2] - 4*samples[i-3] + samples[i-4])
    return res


def estimate_fixed_size(samples, order, bps):
    # заголовок субфрейма 8 + warmup order*bps + residual (2+4+4 + сами биты Rice)
    res = compute_residuals_fixed(samples, order)
    zz = [zigzag(r) for r in res]
    _, rice = find_best_k(zz)
    return 8 + order * bps + 2 + 4 + 4 + rice
