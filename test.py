# -*- coding: utf-8 -*-
"""IEEE‑33 bus micro‑grid – 24 h demo with interactive Plotly outputs.

Generates two HTML files in the current folder:
  • ieee33_topology.html   (voltage heat‑map for the last hour)
  • voltages_24h.html      (line plot of every bus voltage across 24 h)
"""
import time, numpy as np, pandapower as pp, pandapower.networks as pn
from pandapower.plotting import plotly as pp_plotly
import plotly.graph_objects as go

# ---------------------------------------------------------------------------
# 1) Build base network & keep original load values
# ---------------------------------------------------------------------------
# IEEE‑33 radial feeder is shipped in pandapower as `case33bw()`
net = pn.case33bw()
orig_p = net.load.p_mw.copy()
orig_q = net.load.q_mvar.copy()

hist_vm = []  # store voltage profile for all hours

# ---------------------------------------------------------------------------
# 2) 24‑hour time‑series loop (Δt = 1 h)
# ---------------------------------------------------------------------------
for hour in range(24):
    # basic daily load profile (0.7–1.1 pu)
    scale = 0.9 + 0.2 * np.sin(2 * np.pi * hour / 24)
    net.load["p_mw"] = orig_p * scale
    net.load["q_mvar"] = orig_q * scale

    pp.runpp(net)
    hist_vm.append(net.res_bus.vm_pu.values.copy())
    print(f"hour {hour:02d}: scale={scale:.2f}  min V={net.res_bus.vm_pu.min():.3f}")

# ---------------------------------------------------------------------------
# 3) Plotly topology (last hour)
# ---------------------------------------------------------------------------
fig_topo = pp_plotly.simple_plotly(
    net,
    bus_size=8,
    line_width=2,
    bus_color=net.res_bus.vm_pu  # colour = voltage magnitude
)
fig_topo.update_layout(title="IEEE‑33 Voltage Heat‑Map (hour 23)")
fig_topo.write_html("ieee33_topology.html")
print("✅ ieee33_topology.html saved.")

# ---------------------------------------------------------------------------
# 4) Plotly time‑series (24 h profile)
# ---------------------------------------------------------------------------
hist_vm = np.vstack(hist_vm)            # shape (24, 33)
hrs = np.arange(24)
fig_ts = go.Figure()
for bus in range(hist_vm.shape[1]):
    fig_ts.add_trace(go.Scatter(x=hrs, y=hist_vm[:, bus],
                                mode="lines", name=f"bus {bus}"))
fig_ts.update_layout(title="Voltage profile – 24 h",
                     xaxis_title="Hour of day",
                     yaxis_title="Voltage (p.u.)",
                     legend=dict(font_size=8))
fig_ts.write_html("voltages_24h.html")
print("✅ voltages_24h.html saved.")
