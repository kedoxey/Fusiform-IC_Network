import matplotlib.pyplot as plt
import os
import numpy as np
import model_helpers as mh
import argparse as ap
from neuron import h, load_mechanisms
from netpyne import specs, sim


def run_sim(config_name, *batch_params):
    h.load_file("stdrun.hoc")

    cwd = os.getcwd()
    mod_dir = os.path.join(cwd, 'mod')
    load_mechanisms(mod_dir)
    ### Simulation configuration ###

    ### Import simulation config ###
    params = ap.Namespace(**mh.load_config(config_name))

    for batch_param, batch_value in batch_params[0].items():
        setattr(params, batch_param, batch_value)

    ## E/I Ratio ##
    params.inh_gmax = round(params.exc_gmax/10 - params.inh_shift,3) if params.inh_shift > 0 else params.inh_gmax

    sim_label = f'E{params.exc_gmax}-I{params.inh_gmax}-IC{params.ic_scale}xF{params.fusi_scale}xS{params.sgn_scale}_full-network'
    sim_label += '_loss' if params.enable_loss else '_normal'
    if not params.enable_IC: sim_label += '_no-IC'

    output_dir, sim_dir = mh.get_output_dir(params.sim_name, sim_label)
    mh.write_config(params,sim_dir,sim_label,config_name)

    sim_dur = 10000

    cfg = specs.SimConfig()					                    # object of class' []''n of the simulation, in ms
    cfg.dt = 0.05								                # Internal integration timestep to use
    cfg.verbose = True							                # Show detailed messages
    cfg.recordTraces = {'V_soma': {'sec': 'soma', 'loc': 0.5, 'var': 'v'}}
    cfg.recordStep = 0.1
    # cfg.recordStim = True
    cfg.filename = os.path.join(sim_dir, f'{sim_label}-tinnitus_small-net') 	# Set file output name
    cfg.savePickle = False
    # cfg.analysis['plotTraces'] = {'include': ['all'], 'saveFig': False, 'showFig': False}  # Plot recorded traces for this list of cells
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

    pop_labels_nums = {'IC': params.num_cells,
                    'Int': params.num_cells,
                    'Fusi': params.num_cells,
                    'SGN': params.num_cells}

    for pop_label, pop_num in pop_labels_nums.items():
        netParams.popParams[f'{pop_label}_pop'] = {'cellType': 'IzhCell',
                                                'numCells': pop_num}


    ### Synapses ###

    netParams.synMechParams['exc'] = {'mod': 'ExpSyn', 'tau': 3, 'e': -10}
    netParams.synMechParams['inh'] = {'mod': 'ExpSyn', 'tau': 10, 'e': -70}

    ### Connections ###
    i2f_conn_list = mh.define_int_conns(params.num_cells)
    recip_conn_list = [[i,i] for i in range(params.num_cells)]

    netParams.connParams['SGN->Fusi'] = {
        'preConds': {'pop': 'SGN_pop'},
        'postConds': {'pop': 'Fusi_pop'},
        'synsPerConn': 1,
        'synMech': 'exc',
        'weight': params.exc_gmax*params.sgn_scale,
        'connList': recip_conn_list
    }

    netParams.connParams['Fusi->Int'] = {
        'preConds': {'pop': 'Fusi_pop'},
        'postConds': {'pop': 'Int_pop'},
        'synsPerConn': 1,
        'synMech': 'exc',
        'weight': params.exc_gmax,
        'connList': recip_conn_list
    }

    for scale, conns in i2f_conn_list.items():
        netParams.connParams[f'Int{scale}->Fusi'] = {
            'preConds': {'pop': 'Int_pop'},
            'postConds': {'pop': 'Fusi_pop'},
            'synsPerConn': 1,
            'synMech': 'inh',
            'weight': params.inh_gmax*scale,
            'connList': conns
        }

    netParams.connParams['Fusi->IC'] = {
        'preConds': {'pop': 'Fusi_pop'},
        'postConds': {'pop': 'IC_pop'},
        'synsPerConn': 1,
        'synMech': 'exc',
        'weight': params.exc_gmax*params.fusi_scale,
        'connList': recip_conn_list
    }

    if params.enable_IC:
        netParams.connParams['IC->Fusi'] = {
            'preConds': {'pop': 'IC_pop'},
            'postConds': {'pop': 'Fusi_pop'},
            'synsPerConn': 1,
            'synMech': 'exc',
            'weight': params.exc_gmax*params.ic_scale,
            'connList': recip_conn_list
        }

        netParams.connParams['IC->Int'] = {
            'preConds': {'pop': 'IC_pop'},
            'postConds': {'pop': 'Int_pop'},
            'synsPerConn': 1,
            'synMech': 'exc',
            'weight': params.exc_gmax*params.ic_scale,
            'connList': recip_conn_list
        }

    ### Input ###
    in_amp = 0.95

    netParams.stimSourceParams['bkg'] = {'type': 'NetStim', 'rate': 100, 'noise': 1}
    netParams.stimTargetParams['bkg->ALL'] = {'source': 'bkg', 'conds': {'cellType': ['IzhCell']}, 'weight': 0.015, 'delay': 0, 'synMech': 'exc'}

    center_in = (params.num_cells // 2) - 20
    netParams.stimSourceParams['IClamp0'] = {'type': 'IClamp', 'del': 0, 'dur': params.sim_dur, 'amp': params.in_amp}
    netParams.stimTargetParams['IClamp->SGNmid'] = {'source': 'IClamp0', 'sec': 'soma', 'loc': 0.5, 'conds': {'pop': 'SGN_pop', 'cellList': [center_in]}}

    netParams.stimSourceParams['IClamp1'] = {'type': 'IClamp', 'del': 0, 'dur': params.sim_dur, 'amp': params.in_amp-0.3}
    netParams.stimTargetParams['IClamp->SGNside'] = {'source': 'IClamp1', 'sec': 'soma', 'loc': 0.5, 'conds': {'pop': 'SGN_pop', 'cellList': [center_in-1, center_in+1]}}

    num_sgn_high = 40
    sgn_high_ids = [i for i in range(params.num_cells-num_sgn_high-1,params.num_cells)]
    if params.enable_loss:
        netParams.stimSourceParams['IClamp2'] = {'type': 'IClamp', 'del': 0, 'dur': params.sim_dur, 'amp': -(params.in_amp-0.3)}
        netParams.stimTargetParams['IClamp->SGNhigh'] = {'source': 'IClamp2', 'sec': 'soma', 'loc': 0.5, 'conds': {'pop': 'SGN_pop', 'cellList': sgn_high_ids}}

    ### Run simulation ###
    (pops, cells, conns, stims, simData) = sim.createSimulateAnalyze(netParams=netParams, simConfig=cfg, output=True)

    times = np.array(simData['spkt'])
    spikes = np.array(simData['spkid'])

    colors = {'SGN_pop': 'tab:red', 'Int_pop': 'tab:green', 'Fusi_pop': 'tab:purple','IC_pop': 'tab:orange'}

    ### Plot spike frequencies ###
    for pop_label, pop in pops.items():
        mh.plot_spike_frequency(times, spikes, pop, pop_label, sim_dir, sim_label, colors)

    ### Plot spike times ###
    mh.plot_spike_times(params.num_cells, times, spikes, pops, sim_dir, sim_label, colors)

