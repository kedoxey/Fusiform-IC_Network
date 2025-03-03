import network_netpyne
import numpy as np
from sklearn.model_selection import ParameterGrid

config_name = 'default_config'

paramGrid = {'sim_name': ['fully_connected-data'],
             'in_amp': [0.55],
             'sf_exc_gmax': [0.19],
             'fin_exc_gmax': [0.016],
             'fic_exc_gmax': [0.05],
             'icf_exc_gmax': [0.07],
             'icin_exc_gmax': [0.05],
             'inf_inh_gmax': [0.0045],
             'enable_loss': [True, False],
             'enable_IC': [True, False],
             'save_data': [True]}
batchParamsList = list(ParameterGrid(paramGrid))

thresh_params = []
for batchParams in batchParamsList:
    pop_msfs = network_netpyne.run_sim(config_name, batchParams)

    if pop_msfs['Fusi_pop'] > 70:
        thresh_params.append(batchParams['sf_exc_gmax'])

print(thresh_params)
