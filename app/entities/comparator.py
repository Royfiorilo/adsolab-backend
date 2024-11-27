import math
import warnings

warnings.filterwarnings('ignore')


class AdsorptionModelComparison:
    def __init__(self):
        self.results = {}
        self.best_model = None

    @staticmethod
    def determine_best_model(results, key):
        """Determina el mejor modelo basado en múltiples criterios."""
        scores = {}

        for result in results:

            rmse = result['statistics'].get('RMSE', float('inf'))
            aic = result['statistics'].get('AIC', float('inf'))
            chi_squared = result['statistics'].get('chi_squared', float('inf'))
            r_squared_adjusted = result['statistics'].get('r_squared_adjusted', 0)
            durbin_watson = result['statistics'].get('durbin_watson', 0)

            passes_normality = result['residuals'].get('passes_normality', False)
            passes_homoscedasticity = result['residuals'].get('passes_homoscedasticity', False)
            passes_independence = result['residuals'].get('passes_independence', False)


            if not math.isfinite(r_squared_adjusted) or not math.isfinite(rmse) or not math.isfinite(aic):
                print(f"Advertencia: Datos inválidos en modelo {result[key]}. Se omitirán del cálculo.")
                continue


            score = (
                    max(r_squared_adjusted, 0) * 0.25 +  # Asegurar que r_squared no sea negativo
                    (1 / max(rmse, 1e-9)) * 0.2 +  # Evitar división por 0
                    (1 / max(abs(aic), 1e-9)) * 0.2 +  # Asegurar que AIC no sea 0
                    (1 / (1 + chi_squared)) * 0.1 +
                    (1 / (1 + abs(durbin_watson - 2))) * 0.1 +
                    (0.05 if passes_normality else 0) +  # Normalidad
                    (0.05if passes_homoscedasticity else 0) +  # Homocedasticidad
                    (0.05 if passes_independence else 0)  # Independencia
            )

            # Asignar el puntaje al modelo
            scores[result[key]] = score

        # Seleccionar el mejor modelo basado en el puntaje más alto
        if not scores:
            raise ValueError("No se pudieron calcular puntajes válidos para ningún modelo.")

        best_model = max(scores, key=scores.get)
        return best_model

