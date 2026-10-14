import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { auditAPI } from '../api/client';
import GovernanceBadge from '../components/GovernanceBadge';
import RiskMeter from '../components/RiskMeter';
import { ArrowLeft, Loader } from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

function InfoRow({ label, value, danger, warn }) {
  return (
    <div className="info-row">
      <span className="info-label">{label}</span>
      <span className={`info-value ${danger ? 'danger' : warn ? 'warn' : ''}`}>
        {value ?? '—'}
      </span>
    </div>
  );
}

export default function AuditDetailPage() {
  const { traceId } = useParams();
  const [rec, setRec]       = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    auditAPI.detail(traceId)
      .then(r => setRec(r.data))
      .catch(() => toast.error('Trace not found'))
      .finally(() => setLoading(false));
  }, [traceId]);

  if (loading) return (
    <div className="page center-page">
      <Loader size={32} className="spin" />
      <p>Loading audit record…</p>
    </div>
  );

  if (!rec) return (
    <div className="page center-page">
      <p className="muted-text">Trace not found.</p>
      <Link to="/audit" className="btn-ghost">← Back to Audit</Link>
    </div>
  );

  const g = rec.governance;
  return (
    <div className="page">
      <div className="page-header">
        <div>
          <Link to="/audit" className="back-link"><ArrowLeft size={16} /> Audit Trail</Link>
          <h1 className="page-title">Trace Detail</h1>
          <p className="page-sub mono">{rec.trace_id}</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <GovernanceBadge decision={g.governance_decision} />
          <RiskMeter score={g.risk_score} />
        </div>
      </div>

      <div className="detail-grid">
        {/* Prompt / Response */}
        <div className="detail-card span2">
          <h2 className="detail-section-title">Prompt &amp; Response</h2>
          <div className="qa-block">
            <div className="qa-label">Original Prompt</div>
            <div className="qa-text">{rec.prompt}</div>
          </div>
          {rec.sanitized_prompt && rec.sanitized_prompt !== rec.prompt && (
            <div className="qa-block">
              <div className="qa-label warn">Sanitized Prompt <span className="qa-note">(PII redacted)</span></div>
              <div className="qa-text">{rec.sanitized_prompt}</div>
            </div>
          )}
          <div className="qa-block">
            <div className="qa-label">AI Response</div>
            <div className="qa-text">{rec.response || <em className="muted-text">Blocked — no response generated</em>}</div>
          </div>
        </div>

        {/* Governance report */}
        <div className="detail-card">
          <h2 className="detail-section-title">Governance Report</h2>
          <InfoRow label="Decision"       value={g.governance_decision} />
          <InfoRow label="Risk Score"     value={g.risk_score} />
          <InfoRow label="Grounding"      value={(g.grounding_score * 100).toFixed(1) + '%'} />
          <InfoRow label="Toxicity"       value={(g.toxicity_score * 100).toFixed(1) + '%'} />
          <InfoRow label="Confidence"     value={g.confidence} />
          <InfoRow label="PII Detected"   value={g.pii_detected ? '⚠ Yes' : 'No'} warn={g.pii_detected} />
          {g.pii_entities?.length > 0 && (
            <InfoRow label="PII Entities" value={g.pii_entities.join(', ')} warn />
          )}
          <InfoRow label="Prompt Injection" value={g.prompt_injection_detected ? '⚠ Yes' : 'No'} warn={g.prompt_injection_detected} />
          <InfoRow label="Hallucination"    value={g.hallucination_flag ? '⚠ Yes' : 'No'} warn={g.hallucination_flag} />
          <InfoRow label="Policy Violation" value={g.policy_violation ? '⚠ Yes' : 'No'} warn={g.policy_violation} />
          {g.policy_violation_reason && <InfoRow label="Policy Reason" value={g.policy_violation_reason} warn />}
          {g.block_reason && <InfoRow label="Block Reason" value={g.block_reason} danger />}
        </div>

        {/* Pipeline info */}
        <div className="detail-card">
          <h2 className="detail-section-title">Pipeline Info</h2>
          {rec.agent_path && (
            <div className="agent-path">
              {rec.agent_path.map((step, i) => (
                <span key={i} className="agent-step">
                  {step}{i < rec.agent_path.length - 1 && <span className="agent-arrow">→</span>}
                </span>
              ))}
            </div>
          )}
          <InfoRow label="Latency"       value={`${rec.latency_ms} ms`} />
          {rec.token_usage && (
            <>
              <InfoRow label="Prompt Tokens"     value={rec.token_usage.prompt_tokens} />
              <InfoRow label="Completion Tokens" value={rec.token_usage.completion_tokens} />
              <InfoRow label="Total Tokens"      value={rec.token_usage.total_tokens} />
            </>
          )}
          <InfoRow label="Timestamp"     value={rec.timestamp ? format(new Date(rec.timestamp), 'PPpp') : '—'} />
        </div>

        {/* Retrieved documents */}
        {rec.retrieved_documents?.length > 0 && (
          <div className="detail-card span2">
            <h2 className="detail-section-title">Retrieved Sources ({rec.retrieved_documents.length})</h2>
            {rec.retrieved_documents.map((s, i) => (
              <div key={i} className="source-item">
                <div className="source-header">
                  <span className="source-name">{s.filename || s.doc_id}</span>
                  <span className="source-score">score {typeof s.score === 'number' ? s.score.toFixed(3) : s.score}</span>
                </div>
                <p className="source-chunk">{s.chunk}</p>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
