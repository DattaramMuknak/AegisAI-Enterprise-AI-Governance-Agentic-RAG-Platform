/**
 * RiskMeter — circular gauge for risk score (0–100)
 */
export default function RiskMeter({ score }) {
  const pct = Math.min(100, Math.max(0, score));
  const color =
    pct < 30 ? '#22d3a5'
    : pct < 60 ? '#f59e0b'
    : '#ef4444';

  const r = 40;
  const circ = 2 * Math.PI * r;
  const dash = circ * (1 - pct / 100);

  return (
    <div className="risk-meter">
      <svg width={100} height={100} viewBox="0 0 100 100">
        <circle cx={50} cy={50} r={r} fill="none" stroke="rgba(255,255,255,.08)" strokeWidth={10} />
        <circle
          cx={50} cy={50} r={r}
          fill="none"
          stroke={color}
          strokeWidth={10}
          strokeDasharray={circ}
          strokeDashoffset={dash}
          strokeLinecap="round"
          transform="rotate(-90 50 50)"
          style={{ transition: 'stroke-dashoffset .6s ease, stroke .4s ease' }}
        />
        <text x={50} y={55} textAnchor="middle" fill="#fff" fontSize={18} fontWeight={700}>
          {pct}
        </text>
      </svg>
      <span className="risk-label" style={{ color }}>Risk Score</span>
    </div>
  );
}
