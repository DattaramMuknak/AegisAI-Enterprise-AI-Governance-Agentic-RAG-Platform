/**
 * GovernanceBadge — inline pill for governance_decision values.
 */
export default function GovernanceBadge({ decision }) {
  const map = {
    allowed: { label: 'Allowed', cls: 'badge-allowed' },
    blocked: { label: 'Blocked', cls: 'badge-blocked' },
    flagged: { label: 'Flagged', cls: 'badge-flagged' },
  };
  const d = map[decision?.toLowerCase()] || { label: decision || '—', cls: 'badge-neutral' };
  return <span className={`badge ${d.cls}`}>{d.label}</span>;
}
