import network_netpyne
import numpy as np
from sklearn.model_selection import ParameterGrid

config_name = 'default_config'

paramGrid = {'sim_name': ['in_to_fusi'],
             'in_amp': [0],
             'sf_exc_gmax': [0],
             'fin_exc_gmax': [0],
             'fic_exc_gmax': [0],
             'icf_exc_gmax': [0],
             'icin_exc_gmax': [0],
             'inf_inh_gmax': [0.0045],
             'enable_loss': [False],
             'enable_IC': [True]}
batchParamsList = list(ParameterGrid(paramGrid))

thresh_params = []
for batchParams in batchParamsList:
    pop_msfs = network_netpyne.run_sim(config_name, batchParams)

    if pop_msfs['Fusi_pop'] > 70:
        thresh_params.append(batchParams['sf_exc_gmax'])

print(thresh_params)
