for pre, post in connections:
    temp = 5
    synMech = 'inh' if 'Int' in pre else 'exc'

    netParams.connParams[f'{pre}->{post}'] = {
        'preConds': {'pop': f'{pre}_pop'},
        'postConds': {'pop': f'{post}_pop'},
        'synsPerConn': 1,
        'synMech': synMech,
        'weight': 1
    }


### Plot voltage traces ###
fig, axs = plt.subplots(5, 1, figsize=(8,13))
axs.ravel()

t = simData['t']

for cell_id, v_soma in simData['V_soma'].items():
    if 'dict' not in cell_id:
        gid = int(cell_id.split('_')[1])
        cell_pop = cells[gid].tags['pop']
        axs[gid].plot(t, v_soma, label=cell_pop, color=colors[cell_pop])
        axs[gid].set_title(f'{cell_pop}')
    axs[gid].set_ylim([-75,45])
    axs[gid].set_yticks([-60, -30, 0, 30])
    axs[gid].set_ylabel('Voltage (mV)')

axs[-1].set_xlabel('Time (ms)')

fig.tight_layout()
fig.savefig(os.path.join(cwd, 'output', 'voltage_traces.png'), dpi=300)
