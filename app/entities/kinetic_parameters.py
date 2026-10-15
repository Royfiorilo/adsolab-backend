# Parameters that must stay strictly positive: Elovich divides by beta_elo and is flat when alpha_elo is 0.
STRICTLY_POSITIVE_PARAMS = ('alpha_elo', 'beta_elo')
# Their lower bound: far below any physical value (the reference thesis fits alpha_elo = 1.35e-4 mmol/g/min).
POSITIVE_PARAM_MIN = 1e-12
