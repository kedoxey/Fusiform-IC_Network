import network_netpyne
from sklearn.model_selection import ParameterGrid

config_name = 'default_config'

paramGrid = {'sim_name': ['ic_scale'],
             'exc_gmax': [0.07],
             'fusi_scale': [2],
             'ic_scale': [0.25, 0.5, 0.75],
             'enable_loss': [True, False],
             'enable_IC': [True, False]}
batchParamsList = list(ParameterGrid(paramGrid))

for batchParams in batchParamsList:
    network_netpyne.run_sim(config_name, batchParams)