import random, numpy as np, json, os
from datetime import datetime, timedelta

random.seed(42); np.random.seed(42)
BASE_DIR         = os.path.dirname(os.path.abspath(__file__))
OUTPUT_SHIPMENTS = os.path.join(BASE_DIR, "extended_shipments.json")
OUTPUT_SERIES    = os.path.join(BASE_DIR, "carrier_daily_series.json")

START_DATE=datetime(2025,9,1); NUM_DAYS=180; SHIPMENTS_PER_DAY=175
DEGRADED_THRESHOLD=0.80
CITIES=["North Anthony","Kellyland","South Kathryntown","Haleview","Port Elizabeth","North Sandraberg","Reedchester","Johnsonfort","West Kevintown","Staceybury","Cruzmouth","Lake Joanton","Port Michael","New Ryanchester","Steelestad","West Jeffreyton","Sandraville","Kevinport","Michaelton","Ryanchester"]

CARRIER_PROFILES={
    "DHL":      dict(baseline=0.87,degradation=0.0003,shock_resist=0.78,recovery=0.06,cycle_period=45,capacity=35,base_delay=0.18),
    "FedEx":    dict(baseline=0.85,degradation=0.0005,shock_resist=0.68,recovery=0.05,cycle_period=38,capacity=32,base_delay=0.22),
    "UPS":      dict(baseline=0.83,degradation=0.0007,shock_resist=0.62,recovery=0.04,cycle_period=42,capacity=38,base_delay=0.25),
    "BlueDart": dict(baseline=0.83,degradation=0.0006,shock_resist=0.65,recovery=0.04,cycle_period=35,capacity=28,base_delay=0.28),
    "Maersk":   dict(baseline=0.85,degradation=0.0004,shock_resist=0.65,recovery=0.045,cycle_period=40,capacity=30,base_delay=0.23),
}
CARRIERS=list(CARRIER_PROFILES.keys())

def build_shock_schedule():
    schedule={d:{} for d in range(NUM_DAYS)}
    rng=np.random.default_rng(seed=77)
    for carrier in CARRIERS:
        n=int(rng.integers(4,7)); days=rng.choice(range(15,NUM_DAYS-10),n,replace=False)
        for day in days:
            dur=int(rng.integers(2,7)); mag=float(rng.uniform(0.06,0.16))
            for offset in range(dur):
                d=int(day)+offset
                if d<NUM_DAYS:
                    schedule[d][carrier]=schedule[d].get(carrier,0.0)+mag*(1.0-offset/dur)
    for _ in range(3):
        day=int(rng.integers(25,NUM_DAYS-25)); mag=float(rng.uniform(0.04,0.09)); dur=int(rng.integers(3,6))
        for offset in range(dur):
            d=day+offset
            if d<NUM_DAYS:
                for c in CARRIERS: schedule[d][c]=schedule[d].get(c,0.0)+mag*(1.0-offset/dur)
    return schedule

class CarrierState:
    def __init__(self,name,profile):
        self.name=name; self.p=profile; self.rel=profile["baseline"]; self.delay=profile["base_delay"]
    def step(self,day_idx,shock):
        p=self.p
        self.rel-=p["degradation"]
        self.rel+=0.010*np.sin(2*np.pi*day_idx/p["cycle_period"])
        if (START_DATE+timedelta(days=day_idx)).weekday()>=5: self.rel+=0.003; self.delay-=0.005
        if shock>0:
            eff=shock*(1.0-p["shock_resist"]); self.rel-=eff; self.delay+=eff*1.3
        target=p["baseline"]-p["degradation"]*day_idx*0.30
        self.rel+=(target-self.rel)*0.08; self.delay+=(p["base_delay"]-self.delay)*0.06
        if day_idx%60==59:
            boost=min(0.06,(p["baseline"]-self.rel)*0.45); self.rel+=boost; self.delay=max(p["base_delay"],self.delay-boost*0.8)
        self.rel=float(np.clip(self.rel+np.random.normal(0,0.007),0.52,0.99))
        self.delay=float(np.clip(self.delay+np.random.normal(0,0.009),0.04,0.88))

def run():
    print("🔧 AtlasAI Extended Simulator — 180-day LSTM training dataset")
    shocks=build_shock_schedule(); states={n:CarrierState(n,p) for n,p in CARRIER_PROFILES.items()}
    series={n:[] for n in CARRIERS}; all_shipments=[]; sid=10000
    for day_idx in range(NUM_DAYS):
        date=START_DATE+timedelta(days=day_idx); weekday=date.weekday()
        volume=int(SHIPMENTS_PER_DAY*(0.65 if weekday>=5 else 1.0))
        for name in CARRIERS: states[name].step(day_idx,shocks[day_idx].get(name,0.0))
        day_buckets={n:[] for n in CARRIERS}
        for _ in range(volume):
            carrier=random.choice(CARRIERS); st=states[carrier]; load=len(day_buckets[carrier])
            s_delay=float(np.clip(st.delay+load/50*0.02+np.random.normal(0,0.04),0.02,0.92))
            s_rel=float(np.clip(st.rel+np.random.normal(0,0.010),0.50,0.99))
            distance=random.randint(50,2000); weight=round(random.uniform(1.0,100.0),2)
            cost=round(distance*random.uniform(2.5,7.5)+weight*random.uniform(10,40),2)
            rand=random.random()
            if rand<0.34: status,eta="Delivered",0
            elif rand<0.34+s_delay*0.6: status,eta="Delayed",random.randint(12,96)
            elif rand<0.68: status,eta="In Transit",random.randint(4,72)
            else: status,eta="At Warehouse",random.randint(6,48)
            sid+=1
            shipment={"shipment_id":f"SHP-EXT-{sid:06d}","origin":random.choice(CITIES),"destination":random.choice(CITIES),"carrier":carrier,"weight_kg":weight,"distance_km":distance,"eta_hours":eta,"status":status,"delay_probability":round(s_delay,3),"operational_cost":cost,"partner_reliability":round(s_rel,3),"timestamp":(date+timedelta(hours=random.randint(0,23),minutes=random.randint(0,59))).isoformat()}
            all_shipments.append(shipment); day_buckets[carrier].append(shipment)
        for name in CARRIERS:
            bucket=day_buckets[name]; n=len(bucket)
            if n==0:
                if series[name]:
                    prev=dict(series[name][-1]); prev.update(date=date.strftime("%Y-%m-%d"),day_index=day_idx,weekday=weekday,n_shipments=0); series[name].append(prev)
                continue
            rels=[s["partner_reliability"] for s in bucket]; delays=[s["delay_probability"] for s in bucket]
            costs=[s["operational_cost"] for s in bucket]; dists=[s["distance_km"] for s in bucket]
            n_del=sum(1 for s in bucket if s["status"]=="Delayed"); n_dlv=sum(1 for s in bucket if s["status"]=="Delivered")
            avg_rel=float(np.mean(rels)); avg_dly=float(np.mean(delays))
            dly_rate=n_del/n; ont_rate=n_dlv/n
            cpkm=float(np.mean([c/max(d,1) for c,d in zip(costs,dists)]))
            lnorm=n/CARRIER_PROFILES[name]["capacity"]; is_deg=1 if avg_rel<DEGRADED_THRESHOLD else 0
            series[name].append({"carrier":name,"date":date.strftime("%Y-%m-%d"),"day_index":day_idx,"weekday":weekday,"n_shipments":n,"avg_reliability":round(avg_rel,4),"avg_delay_prob":round(avg_dly,4),"delay_rate":round(dly_rate,4),"on_time_rate":round(ont_rate,4),"cost_per_km":round(cpkm,4),"carrier_load_norm":round(lnorm,4),"is_degraded":is_deg})
    for name in CARRIERS:
        rows=series[name]
        for i,row in enumerate(rows):
            past3=[rows[j]["avg_reliability"] for j in range(max(0,i-3),i)] or [row["avg_reliability"]]
            past7=[rows[j]["avg_reliability"] for j in range(max(0,i-7),i)] or [row["avg_reliability"]]
            row["rolling_3d"]=round(float(np.mean(past3)),4); row["rolling_7d"]=round(float(np.mean(past7)),4)
            row["trend_3d"]=round(row["avg_reliability"]-past3[0],4); row["trend_7d"]=round(row["avg_reliability"]-past7[0],4)
    with open(OUTPUT_SHIPMENTS,"w") as f: json.dump(all_shipments,f,indent=2)
    print(f"✅ {len(all_shipments):,} shipments → {OUTPUT_SHIPMENTS}")
    with open(OUTPUT_SERIES,"w") as f: json.dump(series,f,indent=2)
    total_rows=sum(len(v) for v in series.values())
    print(f"✅ {total_rows} daily rows → {OUTPUT_SERIES}")
    print("\n📊 Carrier reliability distribution:")
    total_deg=0
    for name,rows in series.items():
        rels=[r["avg_reliability"] for r in rows]; deg=sum(r["is_degraded"] for r in rows); total_deg+=deg
        print(f"  {name:<10}  mean={np.mean(rels):.3f}  min={np.min(rels):.3f}  max={np.max(rels):.3f}  degraded={deg:3d}/180 ({deg/180*100:.0f}%)")
    print(f"\n  Total: {total_deg}/{total_rows} = {total_deg/total_rows*100:.1f}% degraded")
    return series

if __name__=="__main__":
    run()
    print("\n✅ Done. Run  python backend/ml/train.py  next.")