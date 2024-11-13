import numpy as np
from scipy.optimize import curve_fit
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error
from sklearn.model_selection import KFold
from scipy import stats
import pandas as pd
import warnings

warnings.filterwarnings('ignore')


class AdsorptionModelComparison:
    def __init__(self):
        self.models = {}
        self.results = {}
        self.best_model = None

    def add_model(self, name, function, initial_params, param_bounds=None):
        """
        Añade un modelo de adsorción para comparación

        Parameters:
        -----------
        name : str
            Nombre del modelo
        function : callable
            Función que define el modelo
        initial_params : list
            Parámetros iniciales para el ajuste
        param_bounds : tuple, optional
            Límites inferior y superior para los parámetros
        """
        self.models[name] = {
            'function': function,
            'initial_params': initial_params,
            'param_bounds': param_bounds
        }

    def _fit_model(self, x, y, model_info):
        """Ajusta un modelo a los datos dados"""
        try:
            if model_info['param_bounds']:
                popt, pcov = curve_fit(
                    model_info['function'],
                    x, y,
                    p0=model_info['initial_params'],
                    bounds=model_info['param_bounds']
                )
            else:
                popt, pcov = curve_fit(
                    model_info['function'],
                    x, y,
                    p0=model_info['initial_params']
                )
            return popt, pcov
        except:
            return None, None

    def _calculate_metrics(self, y_true, y_pred):
        """Calcula múltiples métricas de ajuste"""
        if len(y_true) != len(y_pred):
            return None

        metrics = {
            'R2': r2_score(y_true, y_pred),
            'MSE': mean_squared_error(y_true, y_pred),
            'RMSE': np.sqrt(mean_squared_error(y_true, y_pred)),
            'MAE': mean_absolute_error(y_true, y_pred),
            'Chi_square': np.sum(((y_true - y_pred) ** 2) / (y_pred + 1e-10)),
            'ARE': np.mean(np.abs((y_true - y_pred) / y_true)) * 100
        }

        # Criterio de información de Akaike (AIC)
        n = len(y_true)
        p = 2  # número de parámetros
        metrics['AIC'] = n * np.log(metrics['MSE']) + 2 * p

        # Criterio de información bayesiano (BIC)
        metrics['BIC'] = n * np.log(metrics['MSE']) + p * np.log(n)

        return metrics

    def _check_residuals(self, residuals):
        """Analiza los residuos del modelo"""
        # Test de normalidad
        _, normality_p = stats.shapiro(residuals)

        # Test de homocedasticidad (Breusch-Pagan)
        _, homo_p = stats.levene(residuals, np.ones_like(residuals))

        # Test de autocorrelación
        _, indep_p = stats.durbin_watson(residuals)

        return {
            'normality': normality_p > 0.05,
            'homoscedasticity': homo_p > 0.05,
            'independence': 1.5 < indep_p < 2.5
        }

    def compare_models(self, x_data, y_data, cv_folds=5):
        """
        Compara todos los modelos añadidos usando validación cruzada

        Parameters:
        -----------
        x_data : array-like
            Variables independientes
        y_data : array-like
            Variables dependientes
        cv_folds : int
            Número de particiones para validación cruzada
        """
        x_data = np.array(x_data)
        y_data = np.array(y_data)

        # Inicializar resultados
        for name in self.models.keys():
            self.results[name] = {
                'metrics': [],
                'params': [],
                'residuals_check': [],
                'cv_scores': []
            }

        # Validación cruzada
        kf = KFold(n_splits=cv_folds, shuffle=True, random_state=42)

        for train_idx, test_idx in kf.split(x_data):
            X_train, X_test = x_data[train_idx], x_data[test_idx]
            y_train, y_test = y_data[train_idx], y_data[test_idx]

            for name, model_info in self.models.items():
                # Ajustar modelo
                params, _ = self._fit_model(X_train, y_train, model_info)

                if params is not None:
                    # Predecir
                    y_pred = model_info['function'](X_test, *params)

                    # Calcular métricas
                    metrics = self._calculate_metrics(y_test, y_pred)

                    # Analizar residuos
                    residuals = y_test - y_pred
                    residuals_check = self._check_residuals(residuals)

                    # Guardar resultados
                    self.results[name]['metrics'].append(metrics)
                    self.results[name]['params'].append(params)
                    self.results[name]['residuals_check'].append(residuals_check)
                    self.results[name]['cv_scores'].append(metrics['R2'])

        # Calcular promedios y desviaciones estándar
        for name in self.models.keys():
            if self.results[name]['metrics']:
                avg_metrics = pd.DataFrame(self.results[name]['metrics']).mean()
                std_metrics = pd.DataFrame(self.results[name]['metrics']).std()
                self.results[name]['avg_metrics'] = avg_metrics
                self.results[name]['std_metrics'] = std_metrics

        # Determinar el mejor modelo
        self._determine_best_model()

        return self.get_summary()

    def _determine_best_model(self):
        """Determina el mejor modelo basado en múltiples criterios"""
        scores = {}

        for name, result in self.results.items():
            if result['metrics']:  # Si hay métricas disponibles
                # Criterios de puntuación (mayor es mejor)
                avg_metrics = result['avg_metrics']
                residuals_ok = pd.DataFrame(result['residuals_check']).all(axis=0).all()
                cv_stability = np.std(result['cv_scores'])

                # Calcular puntuación total
                score = (
                        avg_metrics['R2'] * 0.3 +  # Ajuste general
                        (1 / avg_metrics['RMSE']) * 0.2 +  # Precisión
                        (1 / avg_metrics['AIC']) * 0.2 +  # Complejidad del modelo
                        residuals_ok * 0.2 +  # Cumplimiento de supuestos
                        (1 / cv_stability) * 0.1  # Estabilidad en validación cruzada
                )

                scores[name] = score

        if scores:
            self.best_model = max(scores, key=scores.get)

    def get_summary(self):
        """Genera un resumen de la comparación de modelos"""
        summary = {
            'best_model': self.best_model,
            'model_comparison': {}
        }

        for name, result in self.results.items():
            if result['metrics']:
                summary['model_comparison'][name] = {
                    'average_metrics': result['avg_metrics'].to_dict(),
                    'std_metrics': result['std_metrics'].to_dict(),
                    'cv_score_mean': np.mean(result['cv_scores']),
                    'cv_score_std': np.std(result['cv_scores']),
                    'residuals_check': pd.DataFrame(result['residuals_check']).all(axis=0).to_dict()
                }

        return summary