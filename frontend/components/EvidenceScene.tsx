import { Check, FileText, Mic2, ShieldCheck } from "lucide-react";

/** Decorative, code-native artwork; no API data or additional graphics runtime. */
export function EvidenceScene({ className = "" }: { className?: string }) {
  return <div className={`evidence-scene ${className}`} aria-hidden="true">
    <div className="evidence-halo evidence-halo-mint" />
    <div className="evidence-halo evidence-halo-coral" />
    <div className="evidence-orbit evidence-orbit-one" />
    <div className="evidence-orbit evidence-orbit-two" />
    <div className="evidence-core"><ShieldCheck size={42} strokeWidth={1.2} /><span>Your financial memory</span></div>
    <div className="evidence-card evidence-card-voice">
      <div className="evidence-card-label"><Mic2 size={15} /><span>01 · Capture</span></div>
      <div className="evidence-wave">{[18, 30, 15, 42, 24, 48, 20, 34, 16, 29, 12].map((height, index) => <i key={index} style={{height, animationDelay: `${index * -.13}s`}} />)}</div>
      <p>Speak naturally.</p>
    </div>
    <div className="evidence-card evidence-card-receipt">
      <div className="evidence-card-label"><FileText size={15} /><span>02 · Review</span></div>
      <div className="evidence-receipt-lines"><i /><i /><i /></div>
      <div className="evidence-receipt-total"><span>Check the details</span><Check size={15} /></div>
      <p>You confirm every entry.</p>
    </div>
    <div className="evidence-card evidence-card-ledger">
      <div className="evidence-card-label"><ShieldCheck size={15} /><span>03 · Build proof</span></div>
      <div className="evidence-ledger-bars"><i /><i /><i /><i /><i /></div>
      <p>A ledger you can explain.</p>
    </div>
    <span className="evidence-particle evidence-particle-one" />
    <span className="evidence-particle evidence-particle-two" />
    <span className="evidence-particle evidence-particle-three" />
  </div>;
}
