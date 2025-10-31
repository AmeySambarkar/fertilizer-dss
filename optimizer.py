# ... (Full optimizer.py content from previous correct version) ...
import numpy as np; import pandas as pd; from scipy.optimize import minimize, Bounds, LinearConstraint; import os; import logging
logging.basicConfig(level=logging.INFO); logger = logging.getLogger(__name__)
def get_float_env(var_name, default_value): value_str = os.getenv(var_name); if value_str is None or value_str.strip() == "": return default_value; try: return float(value_str); except ValueError: logger.warning(f"Env var '{var_name}' invalid ('{value_str}'), using default: {default_value}"); return default_value
CROP_PRICE_PER_KG = get_float_env('CROP_PRICE_PER_KG_INR', 20.0); COST_PER_KG_N = get_float_env('COST_PER_KG_N_INR', 40.0); COST_PER_KG_P = get_float_env('COST_PER_KG_P_INR', 80.0); COST_PER_KG_K = get_float_env('COST_PER_KG_K_INR', 30.0)
def mock_yield_model(n, p, k, base_features_dict): soil_n = base_features_dict.get('soil_n', 25.0); total_rainfall = base_features_dict.get('total_rainfall', 500.0); gdd = base_features_dict.get('gdd', 1500.0); base_yield_potential = 100.0 + (soil_n * 0.2) + (total_rainfall * 0.05) + (gdd * 0.01); logger.debug(f"Base yield potential: {base_yield_potential:.1f}"); yield_n = 1.5 * n - 0.005 * n**2; yield_p = 0.8 * p; yield_k = 0.5 * k; total_yield = base_yield_potential + yield_n + yield_p + yield_k; return max(0, total_yield)
def optimize_npk_safety_first(budget: float, base_features_dict: dict) -> dict:
    logger.info(f"[Optimizer] Starting: budget={budget}, features={list(base_features_dict.keys())}"); logger.info(f"[Optimizer] Costs - N:{COST_PER_KG_N}, P:{COST_PER_KG_P}, K:{COST_PER_KG_K}, Price:{CROP_PRICE_PER_KG}")
    def objective_function(npk):
        n, p, k = npk; cost = n * COST_PER_KG_N + p * COST_PER_KG_P + k * COST_PER_KG_K; mean_yield = mock_yield_model(n, p, k, base_features_dict); std_dev = 0
        if mean_yield > 0: base_uncert = 0.10; n_risk = (n / 150.0) * 0.10; std_dev = mean_yield * (base_uncert + n_risk)
        else: mean_yield = 0
        yield_5th = mean_yield - 1.645 * std_dev; profit_5th = (yield_5th * CROP_PRICE_PER_KG) - cost; return -profit_5th
    budget_constraint = LinearConstraint([[COST_PER_KG_N, COST_PER_KG_P, COST_PER_KG_K]], [0], [budget]); bounds = Bounds(lb=[0, 0, 0], ub=[250, 150, 150])
    init_n = max(0.1, min(bounds.ub[0], (budget*0.4)/COST_PER_KG_N if COST_PER_KG_N > 0 else 0)); init_p = max(0.1, min(bounds.ub[1], (budget*0.3)/COST_PER_KG_P if COST_PER_KG_P > 0 else 0)); init_k = max(0.1, min(bounds.ub[2], (budget*0.3)/COST_PER_KG_K if COST_PER_KG_K > 0 else 0)); initial_cost = init_n*COST_PER_KG_N + init_p*COST_PER_KG_P + init_k*COST_PER_KG_K
    if initial_cost > budget: scale = budget / initial_cost * 0.95; initial_guess = [init_n*scale, init_p*scale, init_k*scale]
    else: initial_guess = [init_n, init_p, init_k]
    logger.info(f"[Optimizer] Initial Guess: {initial_guess}"); result = minimize(objective_function, initial_guess, method='SLSQP', bounds=bounds, constraints=[budget_constraint], options={'disp': False, 'maxiter': 100, 'ftol': 1e-7})
    if result.success:
        opt_n, opt_p, opt_k = result.x; opt_n=max(0, opt_n); opt_p=max(0, opt_p); opt_k=max(0, opt_k); logger.info(f"[Optimizer] Success! NPK: ({opt_n:.1f}, {opt_p:.1f}, {opt_k:.1f})"); final_mean = mock_yield_model(opt_n, opt_p, opt_k, base_features_dict); final_std = 0
        if final_mean > 0: base_uncert = 0.10; n_risk = (opt_n / 150.0) * 0.10; final_std = final_mean * (base_uncert + n_risk)
        return {"N": round(opt_n, 2), "P": round(opt_p, 2), "K": round(opt_k, 2), "yield_mean_at_optimum": round(max(0, final_mean), 2), "yield_std_dev_at_optimum": round(max(0, final_std), 2), "optimizer_status": result.message}
    else: logger.warning(f"[Optimizer] Failed! {result.message}. Fallback..."); result_zero = minimize(objective_function, [0,0,0], method='SLSQP', bounds=bounds, constraints=[budget_constraint], options={'disp': False, 'maxiter': 50, 'ftol': 1e-7})
        if result_zero.success: opt_n, opt_p, opt_k = result_zero.x; opt_n=max(0, opt_n); opt_p=max(0, opt_p); opt_k=max(0, opt_k); logger.info(f"[Optimizer] Fallback success! NPK: ({opt_n:.1f}, {opt_p:.1f}, {opt_k:.1f})"); final_mean = mock_yield_model(opt_n, opt_p, opt_k, base_features_dict); final_std = 0; if final_mean > 0: base_uncert = 0.10; n_risk = (opt_n / 150.0) * 0.10; final_std = final_mean * (base_uncert + n_risk); return {"N": round(opt_n, 2), "P": round(opt_p, 2), "K": round(opt_k, 2), "yield_mean_at_optimum": round(max(0, final_mean), 2), "yield_std_dev_at_optimum": round(max(0, final_std), 2), "optimizer_status": f"Fallback success: {result_zero.message}"}
        else: logger.error(f"[Optimizer] Fallback failed! {result_zero.message}"); return {"N": 0, "P": 0, "K": 0, "yield_mean_at_optimum": 0, "yield_std_dev_at_optimum": 0, "optimizer_status": f"Failed: {result.message}; Fallback failed: {result_zero.message}"}
