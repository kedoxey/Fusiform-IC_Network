import matplotlib.pyplot as plt
import os
import numpy as np
from neuron import h, load_mechanisms
from netpyne import specs, sim, cell, support

h.load_file("stdrun.hoc")

cwd = os.getcwd()
mod_dir = os.path.join(cwd, 'mod')
load_mechanisms(mod_dir)

### Simulation configuration ###
sim_dur = 500

cfg = specs.SimConfig()					                    # object of class SimConfig to store simulation configuration
cfg.duration = sim_dur 						                # Duration of the simulation, in ms
cfg.dt = 0.025								                # Internal integration timestep to use
cfg.verbose = True							                # Show detailed messages
cfg.recordTraces = {'V_soma': {'sec': 'soma', 'loc': 0.5, 'var': 'v'}}
cfg.recordStep = 0.1
cfg.filename = os.path.join(cwd, 'output', 'tinnitus_small-net') 	# Set file output name
cfg.savePickle = True
cfg.analysis['plotTraces'] = {'include': ['all'], 'saveFig': True}  # Plot recorded traces for this list of cells
cfg.hParams['celsius'] = 34.0 
cfg.hParams['v_init'] = -60

### Define cells and network ###
netParams = specs.NetParams()

IzhCell = {'secs': {}}
IzhCell['secs']['soma'] = {'geom': {}, 'pointps': {}}                        # soma params dict
IzhCell['secs']['soma']['geom'] = {'diam': 10.0, 'L': 10.0, 'cm': 31.831}    # soma geometry
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
netParams.cellParams['IzhCell'] = IzhCell                                   # add dict to list of cell parameters

pop_labels = ['SGN', 'Int', 'IC', 'Fusi1', 'Fusi2']

for pop_label in pop_labels:
    netParams.popParams[f'{pop_label}_pop'] = {'cellType': 'IzhCell',
                                               'numCells': 1}

### Input ###
netParams.stimSourceParams['bkg'] = {'type': 'NetStim', 'rate': 100, 'noise': 0.5}
netParams.stimTargetParams['bkg->ALL'] = {'source': 'bkg', 'conds': {'cellType': ['IzhCell']}, 'weight': 0.01, 'delay': 0, 'synMech': 'exc'}

netParams.stimSourceParams['IClamp0'] = {'type': 'IClamp', 'del': 0, 'dur': sim_dur, 'amp': -0.1}
netParams.stimTargetParams['IClamp->SGN'] = {'source': 'IClamp0', 'sec': 'soma', 'loc': 0.5, 'conds': {'pop': 'SGN_pop'}}

### Synapses ###
netParams.synMechParams['exc'] = {'mod': 'ExpSyn', 'tau': 3, 'e': -10}
netParams.synMechParams['inh'] = {'mod': 'ExpSyn', 'tau': 10, 'e': -70}

### Connections ###
connections = [('SGN', 'Fusi1'), ('SGN', 'Fusi2'), 
               ('Fusi1', 'IC'), ('IC', 'Fusi1'), ('Fusi2', 'IC'), ('IC', 'Fusi2'),
               ('IC', 'Int'), ('Int', 'Fusi1'), ('Int', 'Fusi2')]

netParams.connParams[f'input->SGN'] = {
    'preConds': {'pop': 'input'},
    'postConds': {'pop': 'SGN_pop'},
    'synsPerConn': 1,
    'synMech': 'exc',
    'weight': 1
}

netParams.connParams[f'SGN->Fusi1'] = {
    'preConds': {'pop': 'SGN_pop'},
    'postConds': {'pop': 'Fusi1_pop'},
    'probability': 1,
    'synsPerConn': 1,
    'synMech': 'exc',
    'weight': 1
}

netParams.connParams[f'SGN->Fusi2'] = {
    'preConds': {'pop': 'SGN_pop'},
    'postConds': {'pop': 'Fusi2_pop'},
    'synsPerConn': 1,
    'synMech': 'exc',
    'weight': 1
}

netParams.connParams[f'Fusi1->IC'] = {
    'preConds': {'pop': 'Fusi1_pop'},
    'postConds': {'pop': 'IC_pop'},
    'synsPerConn': 1,
    'synMech': 'exc',
    'weight': 1
}

netParams.connParams[f'IC->Fusi1'] = {
    'preConds': {'pop': 'IC_pop'},
    'postConds': {'pop': 'Fusi1_pop'},
    'synsPerConn': 1,
    'synMech': 'exc',
    'weight': 1
}

netParams.connParams[f'Fusi2->IC'] = {
    'preConds': {'pop': 'Fusi2_pop'},
    'postConds': {'pop': 'IC_pop'},
    'synsPerConn': 1,
    'synMech': 'exc',
    'weight': 1
}

netParams.connParams[f'IC->Fusi2'] = {
    'preConds': {'pop': 'IC_pop'},
    'postConds': {'pop': 'Fusi2_pop'},
    'synsPerConn': 1,
    'synMech': 'exc',
    'weight': 1
}

netParams.connParams[f'IC->Int'] = {
    'preConds': {'pop': 'IC_pop'},
    'postConds': {'pop': 'Int_pop'},
    'synsPerConn': 1,
    'synMech': 'exc',
    'weight': 1
}

netParams.connParams[f'Int->Fusi2'] = {
    'preConds': {'pop': 'Int_pop'},
    'postConds': {'pop': 'Fusi2_pop'},
    'synsPerConn': 1,
    'synMech': 'inh',
    'weight': 1
}
netParams.connParams[f'Int->Fusi1'] = {
    'preConds': {'pop': 'Int_pop'},
    'postConds': {'pop': 'Fusi1_pop'},
    'synsPerConn': 1,
    'synMech': 'inh',
    'weight': 1
}

### Run simulation ###
(pops, cells, conns, stims, simData) = sim.createSimulateAnalyze(netParams=netParams, simConfig=cfg, output=True)

times = np.array(simData['spkt'])
spikes = np.array(simData['spkid'])

colors = {'SGN_pop': 'tab:green', 'Int_pop': 'tab:blue', 'IC_pop': 'tab:purple', 'Fusi1_pop': 'tab:red', 'Fusi2_pop': 'tab:red', 'input': 'tab:cyan'}

### Plot spike times ###
fig, axs = plt.subplots(1, 1, figsize=(8,8))

input_spike_t = []

for pop_label, pop in pops.items():
    for gid in pop.cellGids:
        cell = cells[gid]
        spike_times = times[np.where(spikes == gid)]
        if gid == 0:
            input_spike_t = spike_times

        # loc = -1 if gid == 5 else gid
        axs.vlines(spike_times, gid-0.25, gid+0.25, color=colors[pop_label], label=pop_label)

        print(f'{pop_label}: {spike_times.shape[0]} spikes')

axs.legend(loc='upper left', bbox_to_anchor=(1, 1))
axs.set_ylabel('Cells (gid)')
axs.set_xlabel('Time (ms)')
fig.tight_layout()
fig.savefig(os.path.join(cwd, 'output', 'spike_times.png'), dpi=300)


