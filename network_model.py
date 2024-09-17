import pandas
import matplotlib.pyplot as plt
from neuron import h

def xrun(ifx):
    mvec = h.Vector(0)
    h.finitialize()

    while h.t < h.tstop:
        mvec.append(ifx.M())
        h.fadvance()
    mvec.append(ifx.M())

    return mvec

h.load_file("stdrun.hoc")

conn_df = pandas.read_excel('Connectivity.xlsx')

if1 = h.IntFire1()
if1.tau = 10  # ms - time constant
if1.refrac = 3  # ms - refractory period (AHP time constant)

h.cvode_active(0)
h.tstop = 50  # ms
h.celsius = 34
h.steps_per_ms = 100
h.dt = 1.0 / h.steps_per_ms
h.v_init = -60

ns = h.NetStim()
ns.interval = 5
ns.number = 100
ns.start = 0
ns.noise = 0

nc = h.NetCon(ns, if1, -10, 0, 1)

# h.finitialize()

# t = h.Vector().record(h._ref_t)
# m = h.Vector().record(if1(0.5)._ref_M)

# g = h.Graph()
# g.size(0,h.tstop,0,1) # sets x and y axis ranges
# g.addexpr("IntFire1[0].M") # specify hoc name of variable used for y coordinates
# h.graphList[2].append(g) # x coordinates are h.t, updated automatically during a run

m = xrun(if1)

plt.plot(list(m))

temp = 5