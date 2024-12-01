import numpy as np
from sklearn.metrics import r2_score, mean_squared_error
from scipy.stats import chisquare

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
        #chi_squared, pvalue = chisquare(y_exp, y_pred)
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
        n = len(y_exp)
        hybrid = None
        if n > 1:
            hybrid = (100 / (n - num_params)) * np.sum((y_exp - y_pred) ** 2 / (y_exp + 1e-10))
        return hybrid

    @classmethod
    def all_statistics(cls, y_exp, y_pred, num_params):

        stats = {
            "r_squared": round_number(cls.r_squared(y_exp, y_pred)),
            "adjust_r_squared": round_number(cls.adjust_r_squared(y_exp, y_pred, num_params)),
            "chi_squared": round_number(cls.chi_squared(y_exp, y_pred)),
            "adjust_chi_squeared": round_number(cls.adjust_chi_squared(y_exp, y_pred, num_params)),
            "RMSE": round_number(cls.rmse(y_exp, y_pred)),
            "SSE": round_number(cls.sse(y_exp, y_pred)),
            "HYBRID": round_number(cls.hybrid(y_exp, y_pred, num_params))
        }

        return stats
