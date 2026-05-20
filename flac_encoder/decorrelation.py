def select_stereo_mode(left, right):
    # вычисляем mid и side, потом по сумме модулей выбираем что дешевле кодировать
    # side имеет битовую глубину на 1 больше, чем left/right
    n = len(left)
    mid = [0] * n
    side = [0] * n
    sum_l = 0
    sum_r = 0
    sum_m = 0
    sum_s = 0
    for i in range(n):
        l = left[i]
        r = right[i]
        # в FLAC mid это арифметический сдвиг вправо
        m = (l + r) >> 1
        s = l - r
        mid[i] = m
        side[i] = s
        sum_l += l if l >= 0 else -l
        sum_r += r if r >= 0 else -r
        sum_m += m if m >= 0 else -m
        sum_s += s if s >= 0 else -s

    # сумма модулей вместо точной оценки субфрейма
    cost_lr = sum_l + sum_r
    cost_ls = sum_l + sum_s
    cost_rs = sum_r + sum_s
    cost_ms = sum_m + sum_s

    best = "LR"
    best_cost = cost_lr
    if cost_ls < best_cost:
        best_cost = cost_ls
        best = "LS"
    if cost_rs < best_cost:
        best_cost = cost_rs
        best = "RS"
    if cost_ms < best_cost:
        best_cost = cost_ms
        best = "MS"

    if best == "LR":
        return ("LR", left, right)
    if best == "LS":
        return ("LS", left, side)
    if best == "RS":
        return ("RS", side, right)
    return ("MS", mid, side)
