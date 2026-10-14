import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { auditAPI } from '../api/client';
import GovernanceBadge from '../components/GovernanceBadge';
import { RefreshCw, Search, Filter } from 'lucide-react';
import toast from 'react-hot-toast';
import { format } from 'date-fns';

export default function AuditPage() {
  const [logs, setLogs]         = useState([]);
  const [total, setTotal]       = useState(0);
  const [loading, setLoading]   = useState(true);
  const [offset, setOffset]     = useState(0);
  const [filters, setFilters]   = useState({
    governance_decision: '',
    pii_only: false,
    policy_violation_only: false,
  });
  const LIMIT = 25;

  const fetchLogs = (off = 0, f = filters) => {
    setLoading(true);
    const params = { limit: LIMIT, offset: off };
    if (f.governance_decision) params.governance_decision = f.governance_decision;
    if (f.pii_only) params.pii_only = true;
    if (f.policy_violation_only) params.policy_violation_only = true;

    auditAPI.list(params)
      .then(r => { setLogs(r.data.results); setTotal(r.data.total); })
      .catch(() => toast.error('Failed to load audit logs'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { fetchLogs(0, filters); }, []);

  const applyFilters = () => { setOffset(0); fetchLogs(0, filters); };
  const resetFilters = () => {
    const f = { governance_decision: '', pii_only: false, policy_violation_only: false };
    setFilters(f); setOffset(0); fetchLogs(0, f);
  };

  const prevPage = () => { const o = Math.max(0, offset - LIMIT); setOffset(o); fetchLogs(o); };
  const nextPage = () => { const o = offset + LIMIT; setOffset(o); fetchLogs(o); };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Audit Trail</h1>
          <p className="page-sub">Full "why did the AI produce this answer?" record for every request</p>
        </div>
        <button className="btn-ghost" onClick={() => fetchLogs(offset)}>
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* Filter bar */}
      <div className="filter-bar">
        <Filter size={16} className="filter-icon" />
        <select
          id="gov-decision-filter"
          value={filters.governance_decision}
          onChange={e => setFilters(f => ({ ...f, governance_decision: e.target.value }))}
        >
          <option value="">All decisions</option>
          <option value="allowed">Allowed</option>
          <option value="blocked">Blocked</option>
          <option value="flagged">Flagged</option>
        </select>
        <label className="filter-check">
          <input type="checkbox" checked={filters.pii_only}
            onChange={e => setFilters(f => ({ ...f, pii_only: e.target.checked }))} />
          PII only
        </label>
        <label className="filter-check">
          <input type="checkbox" checked={filters.policy_violation_only}
            onChange={e => setFilters(f => ({ ...f, policy_violation_only: e.target.checked }))} />
          Policy violations
        </label>
        <button className="btn-ghost" onClick={applyFilters}>
          <Search size={14} /> Apply
        </button>
        <button className="btn-ghost muted" onClick={resetFilters}>Reset</button>
        <span className="filter-total">{total} records</span>
      </div>

      {/* Table */}
      <div className="table-card">
        <table className="data-table">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Prompt</th>
              <th>Decision</th>
              <th>Risk</th>
              <th>Grounding</th>
              <th>PII</th>
              <th>Latency</th>
              <th>Trace</th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <tr key={i}><td colSpan={8}><div className="row-skeleton" /></td></tr>
              ))
            ) : logs.length === 0 ? (
              <tr><td colSpan={8} className="empty-row">No audit logs match the current filters.</td></tr>
            ) : (
              logs.map(r => (
                <tr key={r.id} className="audit-row">
                  <td className="td-date">{format(new Date(r.timestamp), 'MMM d HH:mm:ss')}</td>
                  <td className="td-prompt" title={r.prompt}>
                    {r.prompt.length > 60 ? r.prompt.slice(0, 60) + '…' : r.prompt}
                  </td>
                  <td><GovernanceBadge decision={r.governance_decision} /></td>
                  <td>
                    <span className={`risk-chip ${r.risk_score >= 75 ? 'high' : r.risk_score >= 40 ? 'med' : 'low'}`}>
                      {r.risk_score}
                    </span>
                  </td>
                  <td>{(r.grounding_score * 100).toFixed(0)}%</td>
                  <td>{r.pii_detected ? <span className="badge-flagged">Yes</span> : <span className="muted-text">No</span>}</td>
                  <td>{r.latency_ms}ms</td>
                  <td>
                    <Link to={`/audit/${r.trace_id}`} className="trace-link">
                      {r.trace_id.slice(0, 8)}…
                    </Link>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="pagination">
        <button className="btn-ghost" onClick={prevPage} disabled={offset === 0}>← Prev</button>
        <span className="page-info">
          {offset + 1}–{Math.min(offset + LIMIT, total)} of {total}
        </span>
        <button className="btn-ghost" onClick={nextPage} disabled={offset + LIMIT >= total}>Next →</button>
      </div>
    </div>
  );
}
