import matplotlib.pyplot as plt
import os
import numpy as np
import model_helpers as mh
from neuron import h, load_mechanisms
from netpyne import specs, sim, cell, support

h.load_file("stdrun.hoc")

cwd = os.getcwd()
mod_dir = os.path.join(cwd, 'mod')
load_mechanisms(mod_dir)

# current = 0.008
# inh_gmaxs = [0.001, 0.002]  #  np.arange(0.005, 0.4, 0.001)

# for inh_gmax in inh_gmaxs:
#     inh_gmax = round(inh_gmax,3)
### Simulation configuration ###
num_cells = 200
sim_label = f'{num_cells}_all_cells'
sim_dir = mh.get_output_dir(sim_label)

sim_dur = 500

cfg = specs.SimConfig()					                    # object of class SimConfig to store simulation configuration
cfg.duration = sim_dur 						                # Duration of the simulation, in ms
cfg.dt = 0.05								                # Internal integration timestep to use
cfg.verbose = True							                # Show detailed messages
cfg.recordTraces = {'V_soma': {'sec': 'soma', 'loc': 0.5, 'var': 'v'}}
cfg.recordStep = 0.1
# cfg.recordStim = True
cfg.filename = os.path.join(sim_dir, f'{sim_label}-tinnitus_small-net') 	# Set file output name
cfg.savePickle = False
cfg.analysis['plotTraces'] = {'include': ['all'], 'saveFig': False, 'showFig': False}  # Plot recorded traces for this list of cells
# cfg.analysis['plotSpikeFreq'] = {'include': ['all'], 'saveFig': True, 'showFig': True}
cfg.hParams['celsius'] = 34.0 
cfg.hParams['v_init'] = -60

### Define cells and network ###
netParams = specs.NetParams()

IzhCell = {'secs': {}}
IzhCell['secs']['soma'] = {'geom': {}, 'pointps': {}}                        # soma params dict
IzhCell['secs']['soma']['geom'] = {'diam': 10.0, 'L': 10.0, 'cm': 31.831}    # soma geometry, cm = 31.831
IzhCell['secs']['soma']['pointps']['Izhi'] = {                               # soma Izhikevich properties
    'mod':'Izhi2007b',
    'C':1,
    'k': 0.7,
    'vr':-60,
    'vt':-40,
    'vpeak':35,
    'a':0.03,
    'b':-2,
    'c':-50,
    'd':100,
    'celltype':1}
IzhCell['secs']['soma']['threshold'] = -20
netParams.cellParams['IzhCell'] = IzhCell                                   # add dict to list of cell parameters                                  # add dict to list of cell parameters

pop_labels_nums = {'Int': num_cells,
                'Fusi': num_cells,
                'SGN': num_cells}

for pop_label, pop_num in pop_labels_nums.items():
    netParams.popParams[f'{pop_label}_pop'] = {'cellType': 'IzhCell',
                                            'numCells': pop_num}


### Synapses ###
netParams.synMechParams['exc'] = {'mod': 'ExpSyn', 'tau': 3, 'e': -10}
netParams.synMechParams['inh'] = {'mod': 'ExpSyn', 'tau': 10, 'e': -70}

### Connections ###
i2f_conn_list = mh.define_int_conns(num_cells)
pops_conn_list = [[i,i] for i in range(num_cells)]

exc_gmax = 0.15
inh_gmax = 0.003

netParams.connParams['SGN->Fusi'] = {
    'preConds': {'pop': 'SGN_pop'},
    'postConds': {'pop': 'Fusi_pop'},
    'synsPerConn': 1,
    'synMech': 'exc',
    'weight': exc_gmax,
    'connList': pops_conn_list
}

netParams.connParams['Fusi->Int'] = {
    'preConds': {'pop': 'Fusi_pop'},
    'postConds': {'pop': 'Int_pop'},
    'synsPerConn': 1,
    'synMech': 'exc',
    'weight': exc_gmax,
    'connList': pops_conn_list
}

for scale, conns in i2f_conn_list.items():
    netParams.connParams[f'Int{scale}->Fusi'] = {
        'preConds': {'pop': 'Int_pop'},
        'postConds': {'pop': 'Fusi_pop'},
        'synsPerConn': 1,
        'synMech': 'inh',
        'weight': inh_gmax*scale,
        'connList': conns
    }

### Input ###
netParams.stimSourceParams['bkg'] = {'type': 'NetStim', 'rate': 100, 'noise': 1}
netParams.stimTargetParams['bkg->ALL'] = {'source': 'bkg', 'conds': {'cellType': ['IzhCell']}, 'weight': 0.015, 'delay': 0, 'synMech': 'exc'}

center_in = num_cells // 2
netParams.stimSourceParams['IClamp0'] = {'type': 'IClamp', 'del': 50, 'dur': sim_dur, 'amp': 0.95}
netParams.stimTargetParams['IClamp->SGNmid'] = {'source': 'IClamp0', 'sec': 'soma', 'loc': 0.5, 'conds': {'pop': 'SGN_pop', 'cellList': [center_in]}}

netParams.stimSourceParams['IClamp1'] = {'type': 'IClamp', 'del': 50, 'dur': sim_dur, 'amp': 0.65}
netParams.stimTargetParams['IClamp->SGNside'] = {'source': 'IClamp1', 'sec': 'soma', 'loc': 0.5, 'conds': {'pop': 'SGN_pop', 'cellList': [center_in-1, center_in+1]}}

# netParams.stimSourceParams['IClamp1'] = {'type': 'IClamp', 'del': 50, 'dur': sim_dur, 'amp': 0.35}
# netParams.stimTargetParams['IClamp->SGNside'] = {'source': 'IClamp1', 'sec': 'soma', 'loc': 0.5, 'conds': {'pop': 'SGN_pop', 'cellList': [center_in-2, center_in+2]}}

### Run simulation ###
(pops, cells, conns, stims, simData) = sim.createSimulateAnalyze(netParams=netParams, simConfig=cfg, output=True)

times = np.array(simData['spkt'])
spikes = np.array(simData['spkid'])

colors = {'SGN_pop': 'tab:red', 'Int_pop': 'tab:green', 'Fusi_pop': 'tab:purple'}

### Plot spike frequencies ###
fusi_pop = pops['Fusi_pop']
sgn_pop = pops['SGN_pop']
int_pop = pops['Int_pop']
mh.plot_spike_frequency(times, spikes, fusi_pop, 'Fusi_pop', sim_dir, colors)
mh.plot_spike_frequency(times, spikes, sgn_pop, 'SGN_pop', sim_dir, colors)
mh.plot_spike_frequency(times, spikes, int_pop, 'Int_pop', sim_dir, colors)

### Plot spike times ###
mh.plot_spike_times(num_cells, times, spikes, pops, sim_dir, colors)

