import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import r2_score, mean_squared_error
from statsmodels.stats.stattools import durbin_watson

from utils import round_number

ROUND_DIGIT = 4


class Statistics():
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Statistics, cls).__new__(cls)
            cls._initialize_instance()
        return cls._instance

    @classmethod
    def _initialize_instance(cls):
        """Inicializa los atributos de la instancia singleton"""
        pass

    @classmethod
    def r_squared(cls, y_exp, y_pred):

        '''
        Calculo de R2 resolviendo con la suma de cuadrado de los resuidos y suma total de cuadrados.
        rss = np.sum((y_exp - y_pred) ** 2)
        y_mean = np.mean(y_exp)
        tss = np.sum((y_exp - y_mean) ** 2)
        r2 = 1 - rss/tss
        :param y_exp: Array de los valores experimentales.
        :param y_pred: Array de las predecciones realizadas.
        :return: Valor numérico de R cuadrado.
        '''
        r2 = r2_score(y_exp, y_pred)
        return r2


    @classmethod
    def linear_r_squeared(cls, pearson_coef):
        '''Calculo de R2 cuando se trata de un modelo lineal.
        Coincide con el Coeficiente de Pearson obtenido de la regresion lineal'''

        return pearson_coef ** 2

    @classmethod
    def adjust_r_squared(cls, y_exp, y_pred, num_params):
        '''
        Calcula el R² ajustado que penaliza el número de parámetros del modelo
        :param y_exp: Array de los valores experimentales.
        :param y_pred: Array de las predecciones realizadas.
        :param num_params: Número de parámetros del modelo.
        :return: Valor numérico de R cuadrado ajustado.
        '''
        n = len(y_exp)
        r2_adjusted = 1 - (((n-1) / (n - num_params - 1)) * (1 - cls.r_squared(y_exp, y_pred)))
        return r2_adjusted

    @classmethod
    def chi_squared(cls, y_exp, y_pred):
        '''
        Realiza el cálculo matemático utilizando la funcio chisquare de scipy.
        La manera de calcularla es como está detallado a continuación
        chi_squared = np.sum(((y_exp - y_pred) ** 2) / np.abs(y_pred))
        '''
        chi_squared = np.sum(((y_exp - y_pred) ** 2) / ((y_pred + 1e-10) ** 2))
        return chi_squared

    @classmethod
    def adjust_chi_squared(cls, y_exp, y_pred, num_params):
        n = len(y_exp)
        chi2_adjusted = cls.chi_squared(y_exp, y_pred) / (n - num_params)
        return chi2_adjusted


    @classmethod
    def rmse(cls, y_exp, y_pred):
        rmse = np.sqrt(mean_squared_error(y_exp, y_pred))
        return rmse

    @classmethod
    def sse(cls, y_exp, y_pred):
        sse = np.sum((y_exp - y_pred) ** 2)
        return sse

    @classmethod
    def hybrid(cls, y_exp, y_pred, num_params):
        '''
        Cálculo de un indicador híbrido que combina la suma de los errores cuadrados con la cantidad de parámetros del modelo.
        Penaliza modelos con más parámetros.

        La fórmula es:
        Híbrido = (100 / (n - p)) * ∑ ((y_exp - y_pred)² / y_exp)

        :param y_exp: Array de los valores experimentales.
        :param y_pred: Array de las predicciones realizadas por el modelo.
        :param num_params: Número de parámetros del modelo.
        :return: Valor numérico del indicador híbrido.
        '''
        n = len(y_exp)
        hybrid = None
        if n > 1:
            hybrid = (100 / (n - num_params)) * np.sum((y_exp - y_pred) ** 2 / (y_exp+ 1e-10))
        return hybrid



    @classmethod
    def all_statistics(cls, y_exp, y_pred, num_params, aic, bic):
        '''
        Calcula todas las estadísticas de ajuste del modelo, que incluyen R², R² ajustado, chi-cuadrado, RMSE, SSE, AIC y BIC.
        Se utiliza como un resumen global de la calidad del modelo.

        :param y_exp: Array de los valores experimentales.
        :param y_pred: Array de las predicciones realizadas por el modelo.
        :param num_params: Número de parámetros del modelo.
        :param aic: Valor del criterio de información de Akaike.
        :param bic: Valor del criterio de información bayesiano.
        :return: Diccionario con las estadísticas calculadas.
        '''
        hybrid = cls.hybrid(y_exp, y_pred, num_params)
        stats = {
            "r_squared": round_number(cls.r_squared(y_exp, y_pred)),
            "adjust_r_squared": round_number(cls.adjust_r_squared(y_exp, y_pred, num_params)),
            "chi_squared": round_number(cls.chi_squared(y_exp, y_pred)),
            "adjust_chi_squeared": round_number(cls.adjust_chi_squared(y_exp, y_pred, num_params)),
            "RMSE": round_number(cls.rmse(y_exp, y_pred)),
            "SSE": round_number(cls.sse(y_exp, y_pred)),
            "HYBRID": round_number(hybrid) if hybrid else None,
            "AIC": round_number(aic),
            "BIC": round_number(bic)
        }

        return stats

    @classmethod
    def check_residuals(self, residuals):
        '''
        Evalúa los residuos del modelo para comprobar tres supuestos importantes:
        normalidad, homocedasticidad y autocorrelación.
        - Normalidad: Medido con la prueba de Shapiro-Wilk.
        - Homocedasticidad: Medido con la prueba de Levene.
        - Autocorrelación: Medido con la estadística de Durbin-Watson.

        :param residuals: Residuos del modelo.
        :return: Diccionario con los valores p de las pruebas y los resultados binarios de cada prueba.
        '''

        # Normalidad (Shapiro-Wilk): Evaluamos si los residuos siguen una distribución normal.
        # Si el valor p es menor o igual a 0.05, los residuos no son normales.
        _, normality_p = stats.shapiro(residuals)

        # Homocedasticidad (Levene): Evaluamos si los residuos tienen varianzas constantes.
        # Si el valor p es menor o igual a 0.05, los residuos no tienen varianzas constantes (heterocedasticidad).
        _, homo_p = stats.levene(residuals, np.ones_like(residuals))

        # Autocorrelación (Durbin-Watson): Evaluamos si los residuos están autocorrelacionados.
        # Si el valor de Durbin-Watson está entre 1.5 y 2.5, no hay autocorrelación significativa.
        dw_stat = durbin_watson(residuals)

        return {
            'normality_pvalue': normality_p,
            'homoscedasticity_pvalue': homo_p,
            'durbin_watson': dw_stat,
            'passes_normality': 0 if normality_p > 0.05 else 1,
            # Si el valor p de la homocedasticidad es mayor a 0.05, se acepta homocedasticidad (0).
            # Si el valor p es menor o igual a 0.05, se rechaza homocedasticidad (1).
            'passes_homoscedasticity': 0 if homo_p > 0.05 else 1,
            # Si el valor de Durbin-Watson está fuera del rango (1.5, 2.5), no hay autocorrelación (1).
            # cuanto mas cecano a 2 mejor
            'passes_independence': 1 if not (1.5 < dw_stat < 2.5) else 0
        }

    @classmethod
    def get_outliers(self, residuals_list):
        residuals_df = pd.concat(residuals_list, ignore_index=True)
        q1 = residuals_df['residuals'].quantile(0.25)
        q3 = residuals_df['residuals'].quantile(0.75)
        iqr = q3 - q1
        outliers = residuals_df[(residuals_df['residuals'] < (q1 - 1.5 * iqr)) | (residuals_df['residuals'] > (q3 + 1.5 * iqr))].tolist()

        return outliers