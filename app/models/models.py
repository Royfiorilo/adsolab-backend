from scipy.stats import linregress

def langmuir(qmax, k, ce):
    return qmax * (k * ce) / (1 + k * ce)

def langmuir_lineariazation(qmax, k, ce):
    return 1 / (qmax * k) + ce / qmax

def langmuir_linerization2(qmax, k, ce):
    return (1 / k * qmax) * (1 / ce) + 1 / qmax

def langmuir_linearizations(name, ce, qe):
    inv_ce = 1 / ce
    inv_qe = 1 / qe
    slope, intercept, r_value, p_value, std_err = linregress(inv_ce, inv_qe)
    match name:
        case 'langmuir 1':
            q_max = 1 / intercept
            k = slope * q_max
        case 'langmuir 2':
            q_max = 1 / intercept
            k = 1 / (slope * q_max)
    return k, q_max, r_value