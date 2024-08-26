import sympy as sp
import numpy as np
from scipy import stats



if __name__ == '__main__':

    # Definimos los símbolos que vamos a usar
    ce, qe, m, b, q_max, k = sp.symbols('ce qe m b q_max k')

    # Paso 1: Definir la ecuación
    equation_str = "ce/qe = (1/q_max) * ce + 1 / (q_max * k)"
    print("Paso 1 - Ecuación original:", equation_str)

    # Paso 2: Convertir la ecuación a una expresión SymPy
    left, right = equation_str.split('=')
    equation = sp.Eq(sp.sympify(left), sp.sympify(right))
    print("Paso 2 - Ecuación SymPy:", equation)

    # Paso 3: Aislar qe en el lado izquierdo
    equation_solved = sp.solve(equation, qe)[0]
    print("Paso 3 - Ecuación resuelta para qe:", equation_solved)

    # Paso 4: Sustituir qe por m*ce + b (forma lineal)
    linear_eq = equation_solved.subs(qe, m*ce + b)
    print("Paso 4 - Ecuación linealizada:", linear_eq)

    # Paso 5: Resolver el sistema de ecuaciones
    solution = sp.solve([
        sp.Eq(linear_eq.coeff(ce), 0),  # Coeficiente de ce debe ser cero
        sp.Eq(linear_eq.subs(ce, 0), 0)  # Término independiente debe ser cero
    ], (q_max, k))

    print("Paso 5 - Solución del sistema:")
    print("q_max =", solution[0][0])
    print("k =", solution[0][1])

    # Paso 6: Usar datos reales para calcular m y b
    ce_data = np.array([0.1, 0.2, 0.3, 0.4, 0.5])
    qe_data = np.array([0.05, 0.08, 0.1, 0.11, 0.12])
    slope, intercept, _, _, _ = stats.linregress(ce_data, ce_data/qe_data)

    print("\nPaso 6 - Valores calculados:")
    print("Pendiente (m) =", slope)
    print("Intersección (b) =", intercept)

    # Paso 7: Calcular los valores finales de q_max y k
    q_max_value = float(solution[0][0].subs({m: slope, b: intercept}))
    k_value = float(solution[0][1].subs({m: slope, b: intercept}))

    print("\nPaso 7 - Resultados finales:")
    print("q_max =", q_max_value)
    print("k =", k_value)

