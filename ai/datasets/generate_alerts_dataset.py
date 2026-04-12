"""
AegisCore Enterprise — Alert Priority Training Dataset Generator
================================================================
10,000 rows | 4 classes: critical / high / medium / low
Features designed for production generalisation — no synthetic IP/username/hostname.

Label distribution target:
  critical ~12%  high ~28%  medium ~38%  low ~22%
"""
from __future__ import annotations
import csv, random
from pathlib import Path
from collections import Counter

SEED = 42
random.seed(SEED)

LABEL_RANGES = {"critical":(85,100),"high":(70,84.9),"medium":(45,69.9),"low":(0,44.9)}
PRIORITY_THRESHOLDS = [(85,"critical"),(70,"high"),(45,"medium"),(0,"low")]

# Mirrors production scoring
DET_W  = {"unauthorized_user_creation":28,"file_integrity":24,"brute_force":18,"port_scan":12,"normal":0}
SRC_W  = {"wazuh":6,"suricata":3}
CRIT_W = {"critical":18,"high":12,"medium":6,"low":0}
IC_W   = {"critical":12,"important":7,"minor":3,"none":0}
SENS_P = {22,3389,3306,5432,5985,5986}

def calc_score(d):
    s = 10
    s += DET_W.get(d["threat_type"], 0)
    s += SRC_W.get(d["source_type"], 0)
    s += CRIT_W.get(d["asset_criticality"], 0)
    s += IC_W.get(d["integrity_change"], 0)
    s += min(d["wazuh_rule_level"] * 0.9, 13)
    s += min(d["suricata_severity"] * 2.5, 10)
    s += min(d["failed_logins_1m"] * 0.4, 6)
    s += min(d["failed_logins_5m"] * 0.2, 6)
    s += min(d["unique_ports_1m"] * 0.15, 6)
    s += min(d["repeated_event_count"] * 0.4, 5)
    s += min(d["time_window_density"] * 0.3, 4)
    s += min(d["recurrence_history"] * 0.5, 3)
    if d["privileged_account"]: s += 5
    if d["blacklisted_ip"]:     s += 6
    if d["off_hours"]:          s += 3
    if d["new_user_created"]:   s += 4
    return min(s, 100.0)

def get_label(sc):
    for t, l in PRIORITY_THRESHOLDS:
        if sc >= t: return l
    return "low"

R = random.randint
C = random.choice

FIELDS = [
    "source_type","threat_type","asset_criticality","integrity_change",
    "wazuh_rule_level","suricata_severity",
    "failed_logins_1m","failed_logins_5m","unique_ports_1m",
    "repeated_event_count","time_window_density","recurrence_history",
    "new_user_created","off_hours","privileged_account","blacklisted_ip",
    "label",
]

def mk(src,det,crit,ic,wrl,suri,fl1,fl5,up,rc,td,rh,nu,oh,priv,bl):
    return {"source_type":src,"threat_type":det,"asset_criticality":crit,
            "integrity_change":ic,"wazuh_rule_level":wrl,"suricata_severity":suri,
            "failed_logins_1m":fl1,"failed_logins_5m":fl5,"unique_ports_1m":up,
            "repeated_event_count":rc,"time_window_density":td,"recurrence_history":rh,
            "new_user_created":nu,"off_hours":oh,"privileged_account":priv,"blacklisted_ip":bl}

# ── brute_force ────────────────────────────────────────────────────────────
def bf_critical(): return mk("wazuh","brute_force",C(["critical","critical","high"]),  "none",R(12,15),0, R(30,60),R(50,120),R(0,2),  R(8,20),R(6,10),R(4,8), 0,C([0,1]),1,C([0,0,1]))
def bf_high():     return mk("wazuh","brute_force",C(["high","high","critical","medium"]),"none",R(8,13),0, R(10,35),R(18,60), R(0,2),  R(4,10),R(3,7), R(1,4), 0,C([0,1]),C([0,1]),C([0,1]))
def bf_medium():   return mk("wazuh","brute_force",C(["medium","medium","low","high"]),  "none",R(5,9), 0, R(3,12), R(5,20),  R(0,2),  R(2,6), R(1,4), R(0,2), 0,C([0,1]),0,0)
def bf_low():      return mk("wazuh","brute_force",C(["low","low","medium"]),            "none",R(1,6), 0, R(1,5),  R(1,8),   0,        R(1,3), R(0,2), 0,      0,0,       0,0)

# ── file_integrity ─────────────────────────────────────────────────────────
def fi_critical(): return mk("wazuh","file_integrity",C(["critical","critical","high"]),  C(["critical","critical","important"]),R(11,15),0, 0,0,0, R(3,8), R(3,6), R(4,8), 0,C([0,1]),C([0,1]),0)
def fi_high():     return mk("wazuh","file_integrity",C(["high","high","critical","medium"]),C(["important","important","critical"]),R(7,12),0, 0,0,0, R(2,5), R(2,4), R(1,4), 0,C([0,1]),0,0)
def fi_medium():   return mk("wazuh","file_integrity",C(["medium","medium","low","high"]),  C(["important","minor","important"]),   R(4,9), 0, 0,0,0, R(1,3), R(1,3), R(0,2), 0,C([0,1]),0,0)
def fi_low():      return mk("wazuh","file_integrity",C(["low","low","medium"]),            C(["minor","none","minor"]),            R(1,6), 0, 0,0,0, R(1,2), R(0,2), 0,      0,0,       0,0)

# ── port_scan ──────────────────────────────────────────────────────────────
def ps_critical(): return mk("suricata","port_scan",C(["critical","critical","high"]),   "none",0,C([3,4]),0,0,R(80,200),R(15,40),R(10,20),R(4,8), 0,C([0,1]),0,C([0,1]))
def ps_high():     return mk("suricata","port_scan",C(["high","high","critical","medium"]),"none",0,C([2,3]),0,0,R(25,90), R(8,20), R(6,12), R(1,4), 0,C([0,1]),0,C([0,1]))
def ps_medium():   return mk("suricata","port_scan",C(["medium","medium","low","high"]),  "none",0,C([1,2]),0,0,R(8,30),  R(3,10), R(2,7),  R(0,2), 0,0,       0,0)
def ps_low():      return mk("suricata","port_scan",C(["low","low","medium"]),            "none",0,C([1,2]),0,0,R(2,10),  R(1,5),  R(1,4),  0,      0,0,       0,0)

# ── unauthorized_user_creation ─────────────────────────────────────────────
def uu_critical(): return mk("wazuh","unauthorized_user_creation",C(["critical","critical","high"]),   "none",R(12,15),0, 0,0,0, R(3,6), R(2,5), R(4,8), 1,C([0,1]),1,C([0,1]))
def uu_high():     return mk("wazuh","unauthorized_user_creation",C(["high","high","critical","medium"]),"none",R(8,13),0, 0,0,0, R(2,4), R(1,4), R(1,4), 1,C([0,1]),C([0,1]),C([0,1]))
def uu_medium():   return mk("wazuh","unauthorized_user_creation",C(["medium","medium","low","high"]),  "none",R(5,9), 0, 0,0,0, R(1,3), R(0,3), R(0,2), 1,C([0,1]),0,0)
def uu_low():      return mk("wazuh","unauthorized_user_creation",C(["low","low","medium"]),            "none",R(2,6), 0, 0,0,0, 1,      0,      0,      1,0,       0,0)

# ── normal traffic (noise class) ──────────────────────────────────────────
def nm_low():    return mk(C(["wazuh","suricata"]),"normal",C(["low","low","medium"]),     "none",R(0,3),C([0,1]),R(0,2),R(0,3), R(0,5), R(0,3), R(0,2), 0,0,0,0,0)
def nm_medium(): return mk(C(["wazuh","suricata"]),"normal",C(["medium","high","critical"]),"none",R(3,7),C([1,2]),R(0,3),R(0,5), R(0,10),R(1,4), R(0,2), 0,C([0,1]),C([0,1]),0,0)

# ── generation plan (fn, intended_label, count) ───────────────────────────
PLAN = [
    # brute_force: 2500
    (bf_critical,"critical",350),(bf_high,"high",700),(bf_medium,"medium",900),(bf_low,"low",550),
    # file_integrity: 2500
    (fi_critical,"critical",350),(fi_high,"high",700),(fi_medium,"medium",900),(fi_low,"low",550),
    # port_scan: 2500
    (ps_critical,"critical",300),(ps_high,"high",700),(ps_medium,"medium",1000),(ps_low,"low",500),
    # unauthorized_user_creation: 2000
    (uu_critical,"critical",300),(uu_high,"high",600),(uu_medium,"medium",750),(uu_low,"low",350),
    # normal traffic noise: 500
    (nm_low,"low",350),(nm_medium,"medium",150),
]

def gen_row(fn, intended, max_tries=500):
    lo, hi = LABEL_RANGES[intended]
    for _ in range(max_tries):
        d = fn()
        sc = calc_score(d)
        if lo <= sc <= hi:
            if random.random() < 0.06:
                sc = max(0, min(100, sc + random.uniform(-5, 5)))
            d["label"] = get_label(sc)
            return d
    d = fn(); d["label"] = get_label(calc_score(d)); return d

rows = []
for fn, intended, n in PLAN:
    for _ in range(n):
        rows.append(gen_row(fn, intended))
random.shuffle(rows)

labels = Counter(r["label"] for r in rows)
dets   = Counter(r["threat_type"] for r in rows)
total  = len(rows)
print(f"Total rows        : {total}")
print("Label distribution:")
for l in ["critical","high","medium","low"]:
    c = labels.get(l,0)
    print(f"  {l:10s}: {c:5d}  ({c/total*100:.1f}%)")
print(f"Threat type dist  : {dict(sorted(dets.items()))}")

out = Path("/home/claude/enterprise_alerts_dataset.csv")
with open(out,"w",newline="") as f:
    w = csv.DictWriter(f, fieldnames=FIELDS); w.writeheader(); w.writerows(rows)
print(f"\nWritten: {out}")
