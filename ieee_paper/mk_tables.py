import pandas as pd, numpy as np
R="results_repo/"
tL,tc,tf,ts,N=0.85,2.3,3.0,0.02,8
tlink,tqp=0.5,1.0
def Sbw(h): return h*tL+(1-h)*(tc+tf)
def Sy(h,s=ts): return h*tL+(1-h)*(tc+2*s)
def bw_b(h): return N/Sbw(h)
def y_b(h,s=ts,offered=None):
    cpu=N/Sy(h,s); link=1/((1-h)*tlink) if h<1 else 1e9; qp=N/((1-h)*tqp)
    return min(cpu,link,qp), cpu, link
out={}
# validation: hit-rate sweep
H=pd.read_csv(R+"hitrate_sweep.csv")
rows=[]
for h in [0.1,0.2,0.4,0.6,0.8]:
    b=H[(H.hit_rate==h)&(H.system=="busywait")].throughput_mrps.item()
    y=H[(H.hit_rate==h)&(H.system=="yield")].throughput_mrps.item()
    bb=bw_b(h); yb,cpu,link=y_b(h)
    cap = (h==0.8)
    bbcap=min(bb,4.0); ybcap=min(yb,4.0)
    ratio = f"{y/b:.2f}" if not cap and h!=0.6 else f"$\\geq${y/b:.2f}"
    if h==0.8: ratio="1.00$^{\\dagger}$"
    dg="$^{\\dagger}$"
    rows.append(f"{int(h*100)} & {bbcap:.3f}{dg if bb>4.0 else ''} & {b:.3f} & {100*b/bbcap:.1f} & {ybcap:.3f}{dg if yb>4.0 else ''} & {y:.3f} & {100*y/ybcap:.1f} & {ratio} \\\\")
    print(h, "BWbound",round(bb,3),"meas",round(b,3),"Ybound",round(yb,3),"cpu",round(cpu,3),"link",round(link,3),"meas",round(y,3))
open("tab_hit.tex","w").write("\n".join(rows).rstrip(" \\")+"\n")
# switch cost
S=pd.read_csv(R+"switchcost_sweep.csv")
rows=[]
for _,r in S.iterrows():
    s=r.switch_us; yb,cpu,link=y_b(0.2,s)
    rows.append(f"{s:g} & {yb:.3f} & {r.yield_peak_mrps:.3f} & {100*r.yield_peak_mrps/yb:.1f} & {r.yield_p999_us:.1f} \\\\")
    print("ts",s,"bound",round(yb,3),"meas",round(r.yield_peak_mrps,3),"p999",round(r.yield_p999_us,1))
open("tab_switch.tex","w").write("\n".join(rows).rstrip(" \\")+"\n")
# main
C=pd.read_csv(R+"compare.csv"); 
def f(x,d=1): 
    return f"{x:,.{d}f}".replace(",","{,}")
rows=[]
for load in sorted(C.offered_mrps.unique()):
    d=C[C.offered_mrps==load].set_index("system")
    def cells(k): 
        r=d.loc[k]; return f"{r.throughput_mrps:.2f} & {f(r.p50_us)} & {f(r.p99_us)} & {f(r.p999_us)}"
    rows.append(f"{load:.1f} & {cells('busywait')} & {cells('yield_rr')} & {f(d.loc['yield_pf'].p999_us)} \\\\")
open("tab_main.tex","w").write("\n".join(rows).rstrip(" \\")+"\n")
# pf table
P=pd.read_csv(R+"pf_vs_rr.csv")
rows=[]
for _,r in P.iterrows():
    rows.append(f"{r.setting.replace(' us','')} & {r.offered_mrps:.1f} & {r.rr_p999:.2f} & {r.pf_p999:.2f} & {r.p999_gain_pct:+.2f} \\\\")
open("tab_pf.tex","w").write("\n".join(rows).rstrip(" \\")+"\n")
print(P.groupby("setting").p999_gain_pct.agg(["mean","min","max"]))
# cache
K=pd.read_csv(R+"cache_sweep.csv")
rows=[]
for part,lab in [("B","Skew sweep (cache 20\\%)"),("C","Size sweep (skew 0.8)")]:
    d=K[K.part==part]
    if part=="C": rows.append(f"\\multicolumn{{5}}{{l}}{{\\textit{{{lab}}}}} \\\\")  # first label is written in sec7_results.tex
    for _,r in d.iterrows():
        capb = r.busywait_mrps>5.0
        capy = r.yield_mrps>5.0
        by = f"{r.yield_mrps:.2f}" + ("$^{\\ddagger}$" if capy else "")
        bb = f"{r.busywait_mrps:.2f}" + ("$^{\\ddagger}$" if capb else "")
        ratio = f"{r.yield_mrps/r.busywait_mrps:.2f}" if not capy else ("--" if capb else f"$\\geq${r.yield_mrps/r.busywait_mrps:.2f}")
        first = f"{r.zipf_s:g}" if part=="B" else f"{r.cache_frac*100:g}\\%"
        rows.append(f"{first} & {r.hit_rate*100:.1f} & {bb} & {by} & {ratio} \\\\")
open("tab_cache.tex","w").write("\n".join(rows).rstrip(" \\")+"\n")
# efficiency
print("Sbw",Sbw(.2),"Sy",Sy(.2),"useful bw",(0.2*tL+0.8*tc)/Sbw(.2),"workers to match",2.5/(1/Sbw(.2)),"util yield at 2.5",2.5*Sy(.2)/N,"util at 1.77",1.7716*Sy(.2)/N)
print("implied fetch under saturation", ((8/1.7716-0.17)/0.8)-2.3)
print("crossover thr", 1.5+0.5*(1.8127-1.7716)/(1.8127-1.5348), "tail", 1.0+0.5*(17.2186-11.3344)/(18.0274-11.3344))

# adaptive table
import os
if os.path.exists(R+"adaptive_load_sweep.csv"):
    al = pd.read_csv(R+"adaptive_load_sweep.csv")
    rows = []
    for load in sorted(al.offered_mrps.unique()):
        sub = al[al.offered_mrps == load].set_index("system")
        bw = sub.loc["busywait"]
        yr = sub.loc["yield_rr"]
        ad = sub.loc["yield_adaptive"]
        rows.append(f"{load:.1f} & {bw.throughput_mrps:.2f} & {f(bw.p50_us)} & {f(bw.p999_us)} & {yr.throughput_mrps:.2f} & {f(yr.p50_us)} & {f(yr.p999_us)} & {ad.throughput_mrps:.2f} & {f(ad.p50_us)} & {f(ad.p999_us)} \\\\")
    open("tab_adaptive.tex","w").write("\n".join(rows).rstrip(" \\")+"\n")
    print("tab_adaptive.tex ok")

