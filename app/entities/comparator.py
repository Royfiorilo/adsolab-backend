import math

import numpy as np
from sklearn.linear_model import Ridge
from sklearn.model_selection import GridSearchCV
from sklearn.preprocessing import StandardScaler

from utils import round_list_numbers
from entities.statistics import Statistics


class AdsorptionModelComparison:
    def __init__(self):
        self.results = {}
        self.best_model = None

    @staticmethod
    def determine_heuristic_scores_models(results, key):
        """
    Determina el mejor modelo basado en múltiples criterios de evaluación estadística. La función
    calcula un puntaje para cada modelo utilizando varias métricas estadísticas y penaliza o premia
    cada modelo en función de sus características.

    Los criterios considerados son:
    - **R² ajustado**: Un valor mayor indica un modelo que se ajusta mejor a los datos, penalizando los modelos con muchos parámetros innecesarios.
    - **RMSE (Root Mean Squared Error)**: Se penaliza el modelo con un RMSE mayor, ya que indica un ajuste peor.
    - **AIC (Akaike Information Criterion)**: Penaliza modelos complejos con muchos parámetros, favoreciendo los modelos más simples que mejor se ajustan a los datos.
        Solo tiene sentido mirarlo con otro modelo, el que tenga el menor es mejor (puede ser negativo)
    - **Chi-cuadrado**: Penaliza el modelo si el valor de chi-cuadrado es alto, ya que indica un mal ajuste entre las predicciones y los datos observados.
    - **Durbin-Watson**: Evalúa la autocorrelación de los residuos. Un valor cerca de 2 es ideal, ya que indica independencia entre los residuos. Valores alejados de 2 (por debajo de 1.5 o por encima de 2.5) indican problemas de autocorrelación.
    - **Normalidad de los residuos**: La prueba de normalidad evalúa si los residuos siguen una distribución normal. Un valor p alto sugiere que los residuos son normales.
    - **Homoscedasticidad**: Evalúa si la varianza de los residuos es constante a lo largo de las observaciones. Si la prueba es exitosa (valor p alto), significa que no hay heterocedasticidad.
    - **Independencia de los residuos**: La prueba de Durbin-Watson mide la independencia de los residuos. Si el valor de la estadística de Durbin-Watson está cerca de 2, los residuos son independientes.

    **Cálculo del puntaje**:
    El puntaje de cada modelo se calcula como una combinación ponderada de los criterios anteriores:
    - Se asignan pesos a cada métrica según su importancia en la evaluación del modelo.
    - Se penalizan las métricas que tienen valores que indican un mal ajuste (por ejemplo, RMSE alto o AIC alto).
    - Se premian las métricas que indican un buen modelo (por ejemplo, un R² ajustado alto, RMSE bajo, o un valor cercano a 2 en Durbin-Watson).
    - Los modelos que pasan las pruebas de normalidad, homoscedasticidad e independencia reciben una pequeña bonificación.

    **Notas importantes**:
    - Se asegura que las métricas no sean inválidas (como valores `NaN` o infinitos). Si alguno de los valores es inválido, el modelo se omite.
    - Si los modelos no cumplen con los requisitos mínimos, se lanza una excepción.

    :param results: Lista de resultados de los modelos a evaluar. Cada resultado debe contener estadísticas y residuos.
    :param key: La clave que identifica de manera única a cada modelo en los resultados.
    :return: El modelo que obtuvo el mejor puntaje basado en los criterios descritos.
    """
        scores = {}

        for result in results:

            statistics  = result["statistics"]
            residuals = result["residuals"]

            rmse = statistics.get('RMSE', float('inf'))
            aic = statistics.get('AIC', float('inf'))
            chi_squared = statistics.get('chi_squared', float('inf'))
            r_squared_adjusted = statistics.get('adjust_r_squared', float('inf'))

            passes_normality = residuals.get('passes_normality', False)
            passes_homoscedasticity = residuals.get('passes_homoscedasticity', False)
            passes_independence = residuals.get('passes_independence', False)

            if  not math.isfinite(rmse) or not math.isfinite(aic):
                print(f"Advertencia: Datos inválidos en modelo. Se omitirán del cálculo.")
                scores[result[key]] = float('inf')
                continue

            score = (
                    r_squared_adjusted * 0.3 +  # Asegurar que r_squared no sea negativo
                    (1 / max(rmse, 1e-9)) * 0.3 +  # Evitar división por 0
                    (1 / max(abs(aic), 1e-9)) * 0.25 +  # Asegurar que AIC no sea 0
                    (1 / (1 + chi_squared)) * 0.1 +
                    (0.05 if passes_normality else 0) +  # Normalidad
                    (0.05 if passes_homoscedasticity else 0) +  # Homocedasticidad
                    (0.05 if passes_independence else 0)  # Independencia
            )

            scores[result[key]] = score

        if not scores:
            raise ValueError("No se pudieron calcular puntajes válidos para ningun modelo.")

        return scores

    @classmethod
    def _best_alpha(cls, X_scaled, y):
        ridge = Ridge()
        param_grid = {'alpha': [0.001, 0.1, 0.05, 0.2, 1, 5, 10, 100, 1000]}
        grid_search = GridSearchCV(estimator=ridge, param_grid=param_grid, scoring='neg_mean_squared_error', cv=5)
        grid_search.fit(X_scaled, y)
        return grid_search.best_params_['alpha']

    @classmethod
    def _manual_aic_bic_ridge(cls, X, y, y_pred):
        n = len(y)
        # num parametros num columns
        k = X.shape[1]

        rss = np.sum((y - y_pred) ** 2)
        sigma_squared = rss / n

        llf = -n / 2 * (np.log(2 * np.pi) + np.log(sigma_squared)) - rss / (2 * sigma_squared)

        aic = 2 * k - 2 * llf

        bic = np.log(n) * k - 2 * llf
        return aic, bic

    @classmethod
    def get_ml_coefs_models(cls, qe, models_y_preds, y_pred_extended):

        X = np.column_stack(tuple(models_y_preds))
        X_extended = np.column_stack(tuple(y_pred_extended))
        y = qe

        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        X_extended_scaler = scaler.transform(X_extended)

        # elijo best alpha
        alpha = cls._best_alpha(X, y)

        # regresion
        ridge = Ridge(alpha=alpha)
        ridge.fit(X_scaled, y)
        #To abs for comparison
        ridge_coefs = [ abs(coef)for coef in ridge.coef_]

        qe_pred_ridge = ridge.predict(X_scaled)


        ridge_aic, ridge_bic = cls._manual_aic_bic_ridge(X_scaled, y, qe_pred_ridge)
        statistics_ridge = Statistics.all_statistics(np.array(y), qe_pred_ridge, len(ridge_coefs), ridge_aic, ridge_bic)
        residuals_ridge = qe - qe_pred_ridge

        y_pred_ridge = ridge.predict(X_extended_scaler)
        return {
            "name": "Ridge",
            "y_pred": round_list_numbers(y_pred_ridge.tolist()),
            "coefs": round_list_numbers(ridge_coefs),
            "statistics": statistics_ridge,
            "residuals": {
                "values": residuals_ridge.tolist(),
                "analysis": Statistics.check_residuals(residuals_ridge)
            }
        }

    @classmethod
    def _get_extended_qe_ridge(cls, ce, ridge_model):
        min_ce = 0
        max_ce = ce.max()
        intermediate = np.linspace(min_ce, max_ce, 300)

        extended_ce = np.concatenate((ce, intermediate))

        extended_qe = ridge_model.predict(extended_ce.reshape(-1, 1))
        return extended_qe

