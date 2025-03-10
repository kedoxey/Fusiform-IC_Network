import matplotlib.pyplot as plt
import os
import yaml
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

    sim_label = f'{params.num_cells}cells-SF{params.sf_exc_gmax}-FInt{params.fin_exc_gmax}-FIC{params.fic_exc_gmax}-ICF{params.icf_exc_gmax}-ICInt{params.icin_exc_gmax}-IntF{params.inf_inh_gmax}-{params.in_amp}nA-full_network'
    sim_label += '-loss' if params.enable_loss else '-normal'
    if not params.enable_IC: sim_label += '-no_IC'

    output_dir, sim_dir = mh.get_output_dir(params.sim_name, sim_label)
    mh.write_config(params,sim_dir,sim_label,config_name)

    cfg = specs.SimConfig()	
    cfg.duration = params.sim_dur				                 
    cfg.dt = 0.05								                # Internal integration timestep to use
    cfg.verbose = True	
    cfg.recordCells = ['Fusi_pop']						                # Show detailed messages
    cfg.recordTraces = {'V_soma': {'sec': 'soma', 'loc': 0.5, 'var': 'v'}}
    cfg.recordStep = 0.1
    # cfg.recordStim = True
    cfg.filename = os.path.join(sim_dir, f'{sim_label}-tinnitus_small_net') 	# Set file output name
    cfg.savePickle = params.save_data
    # cfg.analysis['plotTraces'] = {'include': ['all'], 'saveFig': False, 'showFig': False}  # Plot recorded traces for this list of cells
    # cfg.analysis['plotSpikeFreq'] = {'include': ['all'], 'saveFig': True, 'showFig': True}
    cfg.hParams['celsius'] = 34.0 
    cfg.hParams['v_init'] = -60

    ### Define cells and network ###
    netParams = specs.NetParams()

    IzhCell = {'secs': {}}
    IzhCell['secs']['soma'] = {'geom': {}, 'pointps': {}}                        # soma params dict
    IzhCell['secs']['soma']['geom'] = {'diam': params.diam, 'L': params.diam, 'cm': 1}    # soma geometry, cm = 31.831
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
        'weight': params.sf_exc_gmax,
        'connList': recip_conn_list
    }

    netParams.connParams['Fusi->Int'] = {
        'preConds': {'pop': 'Fusi_pop'},
        'postConds': {'pop': 'Int_pop'},
        'synsPerConn': 1,
        'synMech': 'exc',
        'weight': params.fin_exc_gmax,
        'connList': recip_conn_list
    }

    for scale, conns in i2f_conn_list.items():
        netParams.connParams[f'Int{scale}->Fusi'] = {
            'preConds': {'pop': 'Int_pop'},
            'postConds': {'pop': 'Fusi_pop'},
            'synsPerConn': 1,
            'synMech': 'inh',
            'weight': params.inf_inh_gmax*scale,
            'connList': conns
        }

    netParams.connParams['Fusi->IC'] = {
        'preConds': {'pop': 'Fusi_pop'},
        'postConds': {'pop': 'IC_pop'},
        'synsPerConn': 1,
        'synMech': 'exc',
        'weight': params.fic_exc_gmax,
        'connList': recip_conn_list
    }

    if params.enable_IC:
        netParams.connParams['IC->Fusi'] = {
            'preConds': {'pop': 'IC_pop'},
            'postConds': {'pop': 'Fusi_pop'},
            'synsPerConn': 1,
            'synMech': 'exc',
            'weight': params.icf_exc_gmax,
            'connList': recip_conn_list
        }

        netParams.connParams['IC->Int'] = {
            'preConds': {'pop': 'IC_pop'},
            'postConds': {'pop': 'Int_pop'},
            'synsPerConn': 1,
            'synMech': 'exc',
            'weight': params.icin_exc_gmax,
            'connList': recip_conn_list
        }

    ### Input ###
    netParams.stimSourceParams['bkg'] = {'type': 'NetStim', 'rate': params.bkg_rate, 'noise': 1}
    netParams.stimTargetParams['bkg->ALL'] = {'source': 'bkg', 'conds': {'cellType': ['IzhCell']}, 'weight': params.bkg_weight, 'delay': 0, 'synMech': 'exc'}

    netParams.stimSourceParams['IClamp0'] = {'type': 'IClamp', 'del': 0, 'dur': params.sim_dur, 'amp': 0.1625}
    netParams.stimTargetParams['IClamp->allSGN'] = {'source': 'IClamp0', 'sec': 'soma', 'loc': 0.5, 'conds': {'pop': 'SGN_pop'}}

    center_in = (params.num_cells // 2) - 20
    netParams.stimSourceParams['IClamp1'] = {'type': 'IClamp', 'del': 0, 'dur': params.sim_dur, 'amp': params.in_amp}
    netParams.stimTargetParams['IClamp->SGNmid'] = {'source': 'IClamp1', 'sec': 'soma', 'loc': 0.5, 'conds': {'pop': 'SGN_pop', 'cellList': [center_in]}}

    netParams.stimSourceParams['IClamp2'] = {'type': 'IClamp', 'del': 0, 'dur': params.sim_dur, 'amp': params.in_amp/2}  # -0.3}
    netParams.stimTargetParams['IClamp->SGNside'] = {'source': 'IClamp2', 'sec': 'soma', 'loc': 0.5, 'conds': {'pop': 'SGN_pop', 'cellList': [center_in-1, center_in+1]}}

    num_sgn_high = 40
    sgn_high_ids = [i for i in range(params.num_cells-num_sgn_high-1,params.num_cells)]
    if params.enable_loss:
        netParams.stimSourceParams['IClamp3'] = {'type': 'IClamp', 'del': 0, 'dur': params.sim_dur, 'amp': -(params.in_amp/2)}  # -0.3)}
        netParams.stimTargetParams['IClamp->SGNhigh'] = {'source': 'IClamp3', 'sec': 'soma', 'loc': 0.5, 'conds': {'pop': 'SGN_pop', 'cellList': sgn_high_ids}}

    ### Run simulation ###
    (pops, cells, conns, stims, simData) = sim.createSimulateAnalyze(netParams=netParams, simConfig=cfg, output=True)

    times = np.array(simData['spkt'])
    spikes = np.array(simData['spkid'])

    colors = {'SGN_pop': 'tab:red', 'Int_pop': 'tab:green', 'Fusi_pop': 'tab:purple','IC_pop': 'tab:orange'}

    ### Plot spike frequencies ###
    pop_msfs = {}
    for pop_label, pop in pops.items():
        pop_msf = mh.plot_spike_frequency(times, spikes, pop, pop_label, sim_dir, sim_label, colors)
        pop_msfs[pop_label] = float(pop_msf)

    with open(os.path.join(sim_dir, f'{sim_label}-pop_msfs.yml'), 'w') as outfile:
        yaml.dump(pop_msfs, outfile)

    ### Plot spike times ###
    mh.plot_spike_times(params.num_cells, times, spikes, pops, sim_dir, sim_label, colors)

    return pop_msfs

