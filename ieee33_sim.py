"""IEEE‑33 micro‑grid time‑series demo

*   Runs a 24‑hour profile (1‑h step) with simple sinusoidal load scaling.
*   Results (bus voltages) are streamed to InfluxDB so you can build live
    Grafana plots (see dashboard JSON below).

Dependencies inside the grid‑core container:
    pip install pandapower influxdb numpy
"""
import time
import numpy as np
from influxdb import InfluxDBClient
import pandapower as pp
import pandapower.networks as pn
import pandapower.plotting as pp_plot
# ---------------------------------------------------------------------------
# 1) Build base network and store original load for re‑scaling
# ---------------------------------------------------------------------------
net = pn.case_ieee33()
orig_p = net.load.p_mw.copy()
orig_q = net.load.q_mvar.copy()

# ---------------------------------------------------------------------------
# 2) Connect to InfluxDB (service name "influx" inside Compose network)
# ---------------------------------------------------------------------------
cli = InfluxDBClient(host="influx", port=8086, database="grid")
print("Connected to InfluxDB …")
hist_vm = [] 
# ---------------------------------------------------------------------------
# 3) 24‑hour simulation loop (Δt = 1 h)
# ---------------------------------------------------------------------------
for hour in range(24):
    pp.runpp(net)
    hist_vm.append(net.res_bus.vm_pu.values.copy())
    scale = 0.7 + 0.4 * np.sin(2 * np.pi * hour / 24)  # simple daily profile
    # Apply new load
    net.load["p_mw"] = orig_p * scale
    net.load["q_mvar"] = orig_q * scale

    pp.runpp(net)  # power‑flow calculation

    # Write every bus voltage to InfluxDB
    points = [{
        "measurement": "bus_voltage",
        "tags": {"bus": int(bus)},
        "fields": {"vm_pu": float(net.res_bus.vm_pu.at[bus])},
        "time": int(time.time()*1_000_000_000)  # use current epoch time  # nanoseconds since start
    } for bus in net.bus.index]
    cli.write_points(points)

    print(f"hour {hour:02d}: scale={scale:.2f} min V pu={net.res_bus.vm_pu.min():.3f}")
    time.sleep(0.2)  # throttle so the loop is human‑readable in logs


pp_plot.simple_plot(net, show_plot=False, 
                    bus_size=1.2, 
                    bus_color=net.res_bus.vm_pu, 
                    cmap='viridis')
plt.title("IEEE-33 Voltage Profile – hour 23")
plt.savefig("ieee33_topology_h23.png", dpi=300)

import numpy as np, matplotlib.pyplot as plt
hist_vm = np.vstack(hist_vm)          # shape = (24, 33)

plt.figure(figsize=(10,4))
for bus in range(hist_vm.shape[1]):
    plt.plot(hist_vm[:, bus], label=f"bus {bus}")
plt.xlabel("Hour"); plt.ylabel("V (p.u.)")
plt.title("Voltage profile – 24 h"); plt.legend(ncol=4, fontsize=6)
plt.tight_layout(); plt.savefig("voltages_24h.png", dpi=300)
