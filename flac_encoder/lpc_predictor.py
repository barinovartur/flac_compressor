import math

from flac_encoder.rice_coder import zigzag, find_best_k


def autocorrelation(samples, max_lag):
    # R(k) = sum(s[i]*s[i+k]) для i от 0 до n-k-1, без окна
    n = len(samples)
    R = [0.0] * (max_lag + 1)
    for k in range(max_lag + 1):
        s = 0.0
        for i in range(n - k):
            s += samples[i] * samples[i + k]
        R[k] = s
    return R


def levinson_durbin(R, p):
    # итеративный алгоритм, возвращаем p коэффициентов LPC
    a = [0.0] * p
    E = R[0]
    if E <= 0:
        return a
    for m in range(p):
        # коэффициент отражения
        k_num = R[m + 1]
        for i in range(m):
            k_num -= a[i] * R[m - i]
        k = k_num / E
        # симметричное обновление
        new_a = a[:]
        new_a[m] = k
        for i in range(m):
            new_a[i] = a[i] - k * a[m - 1 - i]
        a = new_a
        E = E * (1 - k * k)
        if E <= 0:
            break
    return a[:p]


def quantize_coefficients(coefs, precision):
    cmax = 0.0
    for c in coefs:
        ac = c if c >= 0 else -c
        if ac > cmax:
            cmax = ac
    if cmax == 0:
        return [0] * len(coefs), 0

    # shift подбираем так чтобы максимум по модулю влез в (precision-1) бит знакового
    shift = precision - 1 - int(math.ceil(math.log2(cmax))) - 1
    if shift < 0:
        shift = 0
    if shift > 15:
        # 5-битное знаковое в файле может хранить максимум 15
        shift = 15

    lim = (1 << (precision - 1)) - 1
    low = -(1 << (precision - 1))
    q = []
    for c in coefs:
        v = int(round(c * (1 << shift)))
        if v > lim:
            v = lim
        elif v < low:
            v = low
        q.append(v)
    return q, shift


def compute_residuals_lpc(samples, qcoefs, shift):
    # остатки точно как у декодера, целочисленная арифметика
    order = len(qcoefs)
    res = []
    n = len(samples)
    for i in range(order, n):
        pred = 0
        for j in range(order):
            pred += qcoefs[j] * samples[i - 1 - j]
        # арифметический сдвиг вправо
        pred >>= shift
        res.append(samples[i] - pred)
    return res


def _estimate_lpc_size(samples, bps, order, qcoefs, shift, precision):
    # 8 заголовок + order*bps warmup + 4 (precision-1) + 5 shift + order*precision коэффициенты
    # + 2+4+4 заголовок RESIDUAL + сами биты Rice
    res = compute_residuals_lpc(samples, qcoefs, shift)
    zz = [zigzag(r) for r in res]
    _, rice = find_best_k(zz)
    return 8 + order * bps + 4 + 5 + order * precision + 2 + 4 + 4 + rice, res


def find_best_lpc_config(samples, bps, max_order=12):
    # перебираем порядки 1..max_order, возвращаем лучший
    precision = 12
    R = autocorrelation(samples, max_order)
    best = None
    for order in range(1, max_order + 1):
        if order >= len(samples):
            break
        coefs = levinson_durbin(R, order)
        # если все нули, нет смысла пробовать
        if all(c == 0 for c in coefs):
            continue
        qcoefs, shift = quantize_coefficients(coefs, precision)
        if all(c == 0 for c in qcoefs):
            continue
        size, res = _estimate_lpc_size(samples, bps, order, qcoefs, shift, precision)
        if best is None or size < best[4]:
            best = (order, qcoefs, shift, res, size)
    return best
