"use client";

import { useState } from "react";
import styles from "./landing.module.css";

const scenarios = [
  { name: "Port closure", category: "ROUTE DISRUPTION", signal: "Loading has stopped at the destination port.", reasoning: "Inbound shipments face a growing delay. Alternative routes need a cost and capacity review.", action: "Escalate for operator review", detail: "High severity keeps execution paused until an operator approves the mitigation.", status: "AWAITING APPROVAL" },
  { name: "Carrier slowdown", category: "CARRIER DEGRADATION", signal: "The carrier forecast points to declining reliability.", reasoning: "A carrier issue can affect more than one route. Switching partners may address the cause more directly than rerouting.", action: "Consider a carrier switch", detail: "The agent weighs the forecast and historical plans before proposing a response.", status: "RECOMMENDATION" },
  { name: "Tight delivery", category: "DELIVERY WINDOW", signal: "An at-risk shipment is approaching its delivery deadline.", reasoning: "An express lane may recover time, but the extra operating cost needs to be weighed against the delivery window.", action: "Consider expediting", detail: "The simulated express action shortens ETA and adds 15% to the shipment’s operating cost.", status: "RECOMMENDATION" },
];

export default function DecisionPreview() {
  const [selected, setSelected] = useState(0);
  const scenario = scenarios[selected];
  return (
    <div className={styles.decisionPreview}>
      <div className={styles.scenarioTabs} role="tablist" aria-label="Example disruption">
        {scenarios.map((item, index) => <button key={item.name} role="tab" id={`scenario-${index}`} aria-controls="scenario-panel" aria-selected={selected === index} tabIndex={selected === index ? 0 : -1} onClick={() => setSelected(index)} onKeyDown={event => {
          if (!["ArrowLeft", "ArrowRight", "Home", "End"].includes(event.key)) return;
          event.preventDefault();
          const next = event.key === "Home" ? 0 : event.key === "End" ? scenarios.length - 1 : (index + (event.key === "ArrowRight" ? 1 : -1) + scenarios.length) % scenarios.length;
          setSelected(next);
          document.getElementById(`scenario-${next}`)?.focus();
        }}>{item.name}</button>)}
      </div>
      <div id="scenario-panel" role="tabpanel" aria-labelledby={`scenario-${selected}`} aria-live="polite" className={styles.scenarioPanel}>
        <div className={styles.scenarioMeta}><span>{scenario.category}</span><span>ILLUSTRATIVE EXAMPLE</span></div>
        <div className={styles.decisionStep}><span className={styles.stepNode} /><div><span className={styles.stepLabel}>OBSERVE</span><h3>{scenario.signal}</h3></div></div>
        <div className={styles.decisionStep}><span className={styles.stepNode} /><div><span className={styles.stepLabel}>REASON</span><p>{scenario.reasoning}</p></div></div>
        <div className={styles.decisionResult}><div><span className={styles.stepLabel}>NEXT MOVE</span><span className={styles.reviewBadge}>{scenario.status}</span></div><h3>{scenario.action}</h3><p>{scenario.detail}</p></div>
      </div>
      <div className={styles.previewFooter}><span className={styles.previewMark}>A</span>Every decision has a trail. Every critical action has a checkpoint.</div>
    </div>
  );
}
