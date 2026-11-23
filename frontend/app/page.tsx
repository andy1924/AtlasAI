import Image from "next/image";
import Link from "next/link";
import DecisionPreview from "./decision-preview";
import styles from "./landing.module.css";

const repository = "https://github.com/andy1924/AtlasAI";

function AtlasMark() {
  return (
    <svg width="30" height="32" viewBox="0 0 30 32" fill="none" aria-hidden="true">
      <path d="M3 28 15 3l12 25M8 18h14M5 25h20M15 3v25" stroke="currentColor" strokeWidth="1.5" />
      <path d="M3 28h24" stroke="currentColor" strokeWidth="3" />
    </svg>
  );
}

export default function LandingPage() {
  return (
    <div className={styles.site}>
      <a className={styles.skipLink} href="#main">Skip to content</a>
      <header className={styles.header}>
        <Link href="/" className={styles.wordmark} aria-label="AtlasAI home"><AtlasMark />atlas<span>AI</span></Link>
        <nav aria-label="Main navigation" className={styles.navigation}>
          <a href="#approach">The approach</a>
          <a href="#in-action">In action</a>
          <a href={repository} target="_blank" rel="noreferrer">Source code</a>
        </nav>
        <Link href="/dashboard" className={styles.headerCta}>Explore the demo</Link>
      </header>

      <main id="main">
        <section className={styles.hero} aria-labelledby="hero-title">
          <div className={styles.heroTop}>
            <p className={styles.eyebrow}><span className={styles.cross}>✳</span> LOGISTICS, WITH FORESIGHT.</p>
            <span className={styles.heroIndex}>Built for the unexpected.</span>
          </div>
          <div className={styles.heroContent}>
            <h1 id="hero-title">Keep your<br /><span className={styles.heroSecondLine}>world <em>moving.</em></span></h1>
            <div className={styles.heroAside}>
              <p>Disruptions travel fast.<br />Your decisions should, too.</p>
              <p className={styles.heroDescription}>AtlasAI connects disruption signals, carrier forecasts, and past decisions to help you find your next move.</p>
              <Link href="/dashboard" className={styles.primaryButton}>Step inside AtlasAI</Link>
              <span className={styles.smallNote}>An open-source logistics prototype.</span>
            </div>
          </div>
          <div className={styles.heroVisual}>
            <Image src="/images/atlas-port.png" alt="Container cranes, cargo ships, and rows of containers along an industrial harbor" fill priority sizes="(max-width: 720px) 100vw, 92vw" className={styles.portImage} />
            <div className={styles.imageTopline}><span>THE WORLD DOESN’T WAIT.</span><span>NEITHER SHOULD YOUR NEXT MOVE.</span></div>
            <div className={styles.imageCaption}>
              <span className={styles.captionLine} />
              <p>Every route tells a story.<br /><strong>See what’s coming next.</strong></p>
            </div>
            <div className={styles.signalNote}><span className={styles.signalSymbol}>⌁</span><div><span>FROM SIGNAL TO DECISION</span><p>A clearer view of what comes next.</p></div></div>
          </div>
          <div className={styles.heroFootnote}><span>SUPPLY CHAINS ARE CONNECTED. YOUR INTELLIGENCE SHOULD BE, TOO.</span><span>Observe / Reason / Decide / Act</span></div>
        </section>

        <section id="approach" className={styles.approach} aria-labelledby="approach-title">
          <div className={styles.sectionHeading}><span className={styles.eyebrow}>THE APPROACH</span><p>Less noise. A better next move.</p></div>
          <div className={styles.approachBody}>
            <h2 id="approach-title">See the ripple.<br /><em>Before the wave.</em></h2>
            <div className={styles.approachText}><p>A delayed carrier rarely stays one carrier’s problem. Routes shift. Costs climb. The knock-on effects keep moving.</p><p>AtlasAI brings those signals into one decision loop. It looks ahead, checks what worked before, and proposes a response—with an operator in control when the stakes are high.</p><a href="#in-action" className={styles.textLink}>See how a decision takes shape</a></div>
          </div>
          <div className={styles.capabilities}>
            <article><span className={styles.capabilityIcon} aria-hidden="true">◎</span><h3>Look ahead.</h3><p>Carrier reliability forecasts help flag emerging risks alongside shipment delays and tight delivery windows.</p><span className={styles.capabilityTag}>CARRIER INTELLIGENCE</span></article>
            <article><span className={styles.capabilityIcon} aria-hidden="true">≋</span><h3>Remember what worked.</h3><p>Historical plans of action give each new disruption context, with successful precedents prioritized in retrieval.</p><span className={styles.capabilityTag}>RETRIEVAL MEMORY</span></article>
            <article><span className={styles.capabilityIcon} aria-hidden="true">⊞</span><h3>Keep the final say.</h3><p>High-severity events and uncertain decisions pause for review. The action history makes the reasoning visible.</p><span className={styles.capabilityTag}>OPERATOR OVERSIGHT</span></article>
          </div>
        </section>

        <section id="in-action" className={styles.actionSection} aria-labelledby="action-title">
          <div className={styles.actionIntro}><span className={styles.eyebrow}>INSIDE THE DECISION</span><h2 id="action-title">A signal.<br />A considered response.</h2><p>Follow a disruption through the loop. Select a scenario to see how the response changes.</p><span className={styles.exampleNote}>ILLUSTRATIVE SCENARIOS · NO LIVE OPERATIONS</span></div>
          <DecisionPreview />
        </section>

        <section className={styles.systemSection} aria-labelledby="system-title">
          <div><span className={styles.eyebrow}>OPEN BY DESIGN</span><h2 id="system-title">The reasoning<br />is part of the product.</h2></div>
          <div className={styles.systemText}><p>This is a working prototype, built to make logistics decisions easier to inspect—not just easier to automate. Explore the agent, test a disruption, and follow the decision from signal to review.</p><div className={styles.technologyList}><span>LangGraph agent</span><span>Carrier forecasting</span><span>Vector memory</span><span>Decision audit trail</span></div><a href={repository} className={styles.textLink} target="_blank" rel="noreferrer">Explore the code on GitHub</a></div>
        </section>

        <section className={styles.closing} aria-labelledby="closing-title"><div className={styles.closingTop}><span className={styles.eyebrow}>YOUR NEXT MOVE</span><AtlasMark /></div><div className={styles.closingContent}><h2 id="closing-title">Less firefighting.<br /><em>More forward motion.</em></h2><div><p>Put the decision loop to the test.<br />Trigger a disruption. Follow the response.</p><Link href="/dashboard" className={styles.lightButton}>Explore the working demo</Link></div></div><div className={styles.closingNote}>SIMULATED SHIPMENTS. REAL REASONING TO EXPLORE.</div></section>
      </main>

      <footer className={styles.footer}><Link href="/" className={styles.wordmark}><AtlasMark />atlas<span>AI</span></Link><p>Logistics intelligence, in motion.</p><div><a href={repository} target="_blank" rel="noreferrer">GitHub</a><Link href="/dashboard">Dashboard</Link><a href="#main">Back to top</a></div></footer>
    </div>
  );
}
