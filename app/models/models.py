def langmuir(qmax, k, ce):
    return qmax * (k * ce) / (1 + k * ce)

def langmuir_lineariazation(qmax, k, ce):
    return 1 / (qmax * k) + ce / qmax