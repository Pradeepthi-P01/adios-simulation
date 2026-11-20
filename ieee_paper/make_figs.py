import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd, numpy as np
R = "results_repo/"
plt.rcParams.update({"font.family": "serif", "font.serif": ["Liberation Serif", "DejaVu Serif"],
    "font.size": 8, "axes.labelsize": 8, "legend.fontsize": 7, "xtick.labelsize": 7, "ytick.labelsize": 7,
    "axes.linewidth": 0.6, "lines.linewidth": 1.1, "lines.markersize": 3.5, "pdf.fonttype": 42,
    "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.4})
BW, RR, PF = "#0072B2", "#D55E00", "#009E73"   # Okabe-Ito, colour-blind safe
W1 = (3.45, 2.35)
def save(fig, n): fig.tight_layout(pad=0.4); fig.savefig(f"figs/{n}.pdf"); plt.close(fig)

c = pd.read_csv(R+"compare.csv")
g = {s: d for s, d in c.groupby("system")}

# throughput
fig, ax = plt.subplots(figsize=W1)
ax.plot([0,3],[0,3],":",color="gray",label="Ideal (carried = offered)")
ax.plot(g["busywait"].offered_mrps, g["busywait"].throughput_mrps, "-o", color=BW, label="Busy-wait")
ax.plot(g["yield_rr"].offered_mrps, g["yield_rr"].throughput_mrps, "-s", color=RR, label="Yield, round-robin")
ax.plot(g["yield_pf"].offered_mrps, g["yield_pf"].throughput_mrps, "--^", color=PF, markersize=3, label="Yield, PF-aware")
ax.set_xlabel("Offered load (MRPS)"); ax.set_ylabel("Achieved throughput (MRPS)")
ax.annotate("1.77", (2.6,1.77), textcoords="offset points", xytext=(0,-10), fontsize=7, ha="center")
ax.annotate("2.50", (2.6,2.5), textcoords="offset points", xytext=(0,5), fontsize=7, ha="center")
ax.legend(loc="upper left", frameon=False); save(fig, "tput")

# p999
fig, ax = plt.subplots(figsize=W1)
for k,col,m,ls,l in [("busywait",BW,"o","-","Busy-wait"),("yield_rr",RR,"s","-","Yield, round-robin"),("yield_pf",PF,"^","--","Yield, PF-aware")]:
    ax.plot(g[k].offered_mrps, g[k].p999_us, ls, marker=m, color=col, label=l, markersize=3 if k=="yield_pf" else 3.5)
ax.set_yscale("log"); ax.set_xlabel("Offered load (MRPS)"); ax.set_ylabel("P99.9 latency ($\\mu$s)")
ax.legend(loc="lower right", frameon=False); save(fig, "p999")

# percentile bars at 1.5 and 1.8
fig, axs = plt.subplots(1, 2, figsize=W1, sharey=False)
for ax, load in zip(axs, [1.5, 1.0]):
    d = c[c.offered_mrps==load].set_index("system")
    x = np.arange(3); w = 0.26
    for i,(k,col,h,l) in enumerate([("busywait",BW,"//","Busy-wait"),("yield_rr",RR,"..","Yield RR"),("yield_pf",PF,"xx","Yield PF")]):
        ax.bar(x+(i-1)*w, [d.loc[k,"p50_us"],d.loc[k,"p99_us"],d.loc[k,"p999_us"]], w, color="white", edgecolor=col, hatch=h, linewidth=0.8, label=l)
    ax.set_xticks(x); ax.set_xticklabels(["P50","P99","P99.9"]); ax.set_title(f"{load} MRPS", fontsize=8)
axs[0].set_ylabel("Latency ($\\mu$s)"); axs[0].legend(frameon=False, loc="upper left", fontsize=6)
save(fig, "bars")

# PF gain
p = pd.read_csv(R+"pf_vs_rr.csv")
fig, ax = plt.subplots(figsize=W1)
for (s,d),col,m in zip(p.groupby("setting"),[BW,RR],["o","s"]):
    ax.plot(d.offered_mrps, d.p999_gain_pct, "-"+m, color=col, label=s)
ax.axhline(0,color="k",linewidth=0.5)
ax.set_xlabel("Offered load (MRPS)"); ax.set_ylabel("P99.9 gain of PF-aware (%)"); ax.legend(frameon=False); save(fig, "pfgain")

# hit rate
h = pd.read_csv(R+"hitrate_sweep.csv"); hb=h[h.system=="busywait"]; hy=h[h.system=="yield"]
fig, ax = plt.subplots(figsize=W1)
ax.plot(hb.hit_rate*100, hb.throughput_mrps, "-o", color=BW, label="Busy-wait")
ax.plot(hy.hit_rate*100, hy.throughput_mrps, "-s", color=RR, label="Yield")
ax.axhline(4.0, color="gray", linestyle=":", linewidth=0.8); ax.text(12, 4.07, "offered load (4.0 MRPS)", fontsize=6.5, color="gray")
ax.set_xlabel("Local-memory hit rate (%)"); ax.set_ylabel("Peak throughput (MRPS)"); ax.set_ylim(1.2,4.5)
ax.legend(frameon=False, loc="upper left"); save(fig, "hit")

# switch cost
s = pd.read_csv(R+"switchcost_sweep.csv")
bw_peak, bw_tail = 1.7716, 17.2186
fig, axs = plt.subplots(1, 2, figsize=(7.1, 2.3))
axs[0].plot(s.switch_us, s.yield_peak_mrps, "-s", color=RR, label="Yield"); axs[0].axhline(bw_peak, color=BW, linestyle="--", label="Busy-wait (1.77)")
axs[0].set_xscale("log"); axs[0].set_xlabel("Context-switch cost ($\\mu$s, log)"); axs[0].set_ylabel("Peak throughput (MRPS)"); axs[0].legend(frameon=False)
axs[1].plot(s.switch_us, s.yield_p999_us, "-s", color=RR, label="Yield"); axs[1].axhline(bw_tail, color=BW, linestyle="--", label="Busy-wait (17.2 $\\mu$s)")
axs[1].set_xscale("log"); axs[1].set_yscale("log"); axs[1].set_xlabel("Context-switch cost ($\\mu$s, log)"); axs[1].set_ylabel("P99.9 at 1.5 MRPS ($\\mu$s, log)"); axs[1].legend(frameon=False, loc="upper left")
save(fig, "switch")

# cache
k = pd.read_csv(R+"cache_sweep.csv"); C = k[k.part=="C"]; B = k[k.part=="B"]
fig, axs = plt.subplots(1, 2, figsize=(7.1, 2.3))
axs[0].plot(C.cache_frac*100, C.hit_rate*100, "-o", color=BW, label="LRU, Zipf skew 0.8")
axs[0].plot(C.cache_frac*100, C.cache_frac*100, ":", color="gray", label="Uniform access (hit rate = size)")
axs[0].set_xlabel("Local cache size (% of pages)"); axs[0].set_ylabel("Measured hit rate (%)"); axs[0].legend(frameon=False)
axs[1].plot(C.cache_frac*100, C.busywait_mrps, "-o", color=BW, label="Busy-wait"); axs[1].plot(C.cache_frac*100, C.yield_mrps, "-s", color=RR, label="Yield")
axs[1].axhline(5.0, color="gray", linestyle=":", linewidth=0.8); axs[1].text(8, 5.08, "offered load (5.0 MRPS)", fontsize=6.5, color="gray")
axs[1].set_ylim(1.5,5.6); axs[1].set_xlabel("Local cache size (% of pages)"); axs[1].set_ylabel("Peak throughput (MRPS)"); axs[1].legend(frameon=False, loc="center right")
save(fig, "cache")

# skew
fig, ax = plt.subplots(figsize=W1); ax2 = ax.twiny() if False else None
ax.plot(B.zipf_s, B.busywait_mrps, "-o", color=BW, label="Busy-wait"); ax.plot(B.zipf_s, B.yield_mrps, "-s", color=RR, label="Yield")
for x,hh in zip(B.zipf_s, B.hit_rate): ax.annotate(f"{hh*100:.0f}%", (x, 1.0), ha="center", fontsize=6.5, color="gray")
ax.axhline(5.0, color="gray", linestyle=":", linewidth=0.8)
ax.set_ylim(0.7,5.5); ax.set_xlabel("Zipf skew $s$ (grey: measured hit rate)"); ax.set_ylabel("Peak throughput (MRPS)"); ax.legend(frameon=False, loc="center left")
save(fig, "skew")
print("ok")

# ---- analytical extrapolation (model equations only, no simulation) ----
tL,tc,ts_,h_,tl_,tq_ = 0.85,2.3,0.02,0.20,0.5,1.0
def S_bw(tf): return h_*tL+(1-h_)*(tc+tf)
def S_y(): return h_*tL+(1-h_)*(tc+2*ts_)
LINK = 1/((1-h_)*tl_)
def cap_bw(N,tf=3.0): return min(N/S_bw(tf), LINK)
def cap_y(N): return min(N/S_y(), LINK, N/((1-h_)*tq_))
fig, axs = plt.subplots(1, 2, figsize=(7.1, 2.3))
Ns = np.arange(1, 17)
axs[0].plot(Ns, [cap_bw(n) for n in Ns], "-o", color=BW, label="Busy-wait")
axs[0].plot(Ns, [cap_y(n) for n in Ns], "-s", color=RR, label="Yield")
axs[0].axvline(8, color="gray", linestyle=":", linewidth=0.8); axs[0].text(8.2, 0.3, "N = 8\n(simulated)", fontsize=6.5, color="gray")
axs[0].set_xlabel("Worker threads $N$"); axs[0].set_ylabel("Capacity bound (MRPS)"); axs[0].legend(frameon=False, loc="upper left")
tfs = np.linspace(2, 6, 41)
axs[1].plot(tfs, [min(cap_y(8),LINK)/cap_bw(8,t) for t in tfs], "-", color=RR)
axs[1].plot([3.0],[cap_y(8)/cap_bw(8,3.0)], "ko", markersize=4); axs[1].annotate("default 3.0 $\\mu$s: 1.38", (3.0, 1.38), textcoords="offset points", xytext=(8,-12), fontsize=6.5)
axs[1].set_xlabel("Unloaded fetch time $t_f$ ($\\mu$s)"); axs[1].set_ylabel("Yield / busy-wait capacity")
save(fig, "scale")
print("scale ok", [round(cap_bw(n),3) for n in (4,8,11,12)], [round(cap_y(n),3) for n in (4,8,11,12)],
      [round(cap_y(8)/cap_bw(8,t),3) for t in (2,3,4,5,6)], round(LINK*S_bw(3.0),2), round(LINK*S_y(),2))

# ---- Adaptive Hybrid Evaluation ----
import os
if os.path.exists(R+"adaptive_load_sweep.csv") and os.path.exists(R+"adaptive_cost_sweep.csv"):
    al = pd.read_csv(R+"adaptive_load_sweep.csv")
    ac = pd.read_csv(R+"adaptive_cost_sweep.csv")
    AD = "#009E73"
    fig, axs = plt.subplots(1, 2, figsize=(7.1, 2.3))
    for k,col,m,ls,l in [("busywait",BW,"o","--","Busy-wait"),("yield_rr",RR,"s","-","Pure Yield (RR)"),("yield_adaptive",AD,"^","-.","Adaptive Hybrid")]:
        sub = al[al.system == k]
        axs[0].plot(sub.offered_mrps, sub.p50_us, ls, marker=m, color=col, label=l, markersize=3.5)
    axs[0].set_yscale("log")
    axs[0].set_xlabel("Offered load (MRPS)")
    axs[0].set_ylabel("P50 latency ($\\mu$s, log)")
    axs[0].legend(frameon=False, loc="upper left", fontsize=6.5)

    axs[1].plot(ac.switch_cost_us, ac.yield_rr_p50, "-s", color=RR, label="Pure Yield (RR)")
    axs[1].plot(ac.switch_cost_us, ac.adaptive_p50, "-^", color=AD, label="Adaptive Hybrid")
    axs[1].axhline(ac.busywait_p50.iloc[0], color=BW, linestyle="--", label="Busy-wait (5.30 $\\mu$s)")
    axs[1].set_xlabel("Context-switch cost $t_s$ ($\\mu$s)")
    axs[1].set_ylabel("P50 at 0.5 MRPS ($\\mu$s)")
    axs[1].legend(frameon=False, loc="upper left", fontsize=6.5)
    save(fig, "adaptive")
    print("adaptive ok")

