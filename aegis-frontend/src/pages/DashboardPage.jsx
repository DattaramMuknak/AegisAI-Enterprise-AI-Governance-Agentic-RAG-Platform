import { useEffect, useState } from 'react';
import { dashboardAPI } from '../api/client';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, BarChart, Bar, Legend,
} from 'recharts';
import {
  Activity, ShieldX, UserX, AlertTriangle,
  Scale, Gauge, Clock, TrendingUp, RefreshCw
} from 'lucide-react';
import toast from 'react-hot-toast';

function StatCard({ icon: Icon, label, value, accent, sub }) {
  return (
    <div className="stat-card" style={{ '--accent': accent }}>
      <div className="stat-icon"><Icon size={22} /></div>
      <div className="stat-body">
        <span className="stat-value">{value}</span>
        <span className="stat-label">{label}</span>
        {sub && <span className="stat-sub">{sub}</span>}
      </div>
    </div>
  );
}

const COLORS = {
  teal:   '#22d3a5',
  red:    '#ef4444',
  amber:  '#f59e0b',
  violet: '#8b5cf6',
  blue:   '#3b82f6',
  rose:   '#f43f5e',
  sky:    '#0ea5e9',
  green:  '#22c55e',
};

export default function DashboardPage() {
  const [stats, setStats]         = useState(null);
  const [series, setSeries]       = useState([]);
  const [loadingStats, setLS]     = useState(true);
  const [loadingSeries, setLSer]  = useState(true);

  const fetchData = () => {
    setLS(true);
    setLSer(true);
    dashboardAPI.stats()
      .then(r => setStats(r.data))
      .catch(() => toast.error('Could not load stats'))
      .finally(() => setLS(false));

    dashboardAPI.timeseries(14)
      .then(r => setSeries(r.data))
      .catch(() => toast.error('Could not load timeseries'))
      .finally(() => setLSer(false));
  };

  useEffect(() => {
    fetchData();
  }, []);

  const cards = stats ? [
    { icon: Activity,     label: 'Total Requests',      value: stats.total_requests,         accent: COLORS.teal,   sub: 'all time' },
    { icon: ShieldX,      label: 'Blocked',              value: stats.blocked_requests,       accent: COLORS.red,    sub: 'governance blocked' },
    { icon: UserX,        label: 'PII Incidents',        value: stats.pii_incidents,          accent: COLORS.amber,  sub: 'detected & redacted' },
    { icon: AlertTriangle,label: 'Hallucination Flags',  value: stats.hallucination_flags,    accent: COLORS.violet, sub: 'low grounding' },
    { icon: Scale,        label: 'Policy Violations',    value: stats.policy_violations,      accent: COLORS.rose,   sub: 'rule triggered' },
    { icon: Gauge,        label: 'Avg Risk Score',       value: stats.average_risk_score,     accent: COLORS.sky,    sub: '0 – 100 scale' },
    { icon: Clock,        label: 'Avg Latency',          value: `${stats.average_latency_ms}ms`, accent: COLORS.green, sub: 'pipeline end-to-end' },
    { icon: TrendingUp,   label: 'Avg Grounding',        value: (stats.average_grounding_score * 100).toFixed(1) + '%', accent: COLORS.blue, sub: 'lexical overlap' },
  ] : [];

  const CustomTooltip = ({ active, payload, label }) => {
    if (!active || !payload?.length) return null;
    return (
      <div className="chart-tooltip">
        <p className="chart-tooltip-label">{label}</p>
        {payload.map((p) => (
          <p key={p.name} style={{ color: p.color }}>
            {p.name}: <strong>{typeof p.value === 'number' ? p.value.toFixed(p.name === 'avg_risk' || p.name === 'avg_risk_score' ? 1 : 0) : p.value}</strong>
          </p>
        ))}
      </div>
    );
  };

  return (
    <div className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Governance Dashboard</h1>
          <p className="page-sub">Real-time AI request health &amp; compliance metrics</p>
        </div>
        <button className="btn-ghost" onClick={fetchData}>
          <RefreshCw size={16} /> Refresh
        </button>
      </div>

      {/* Stat cards */}
      <div className="stats-grid">
        {loadingStats
          ? Array.from({ length: 8 }).map((_, i) => <div key={i} className="stat-card skeleton" />)
          : cards.map((c) => <StatCard key={c.label} {...c} />)
        }
      </div>

      {/* Charts */}
      <div className="charts-grid">
        {/* Area chart — requests over time */}
        <div className="chart-card">
          <h2 className="chart-title">Daily Request Volume</h2>
          {loadingSeries ? (
            <div className="chart-skeleton" />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <AreaChart data={series} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="cReq" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor={COLORS.teal}  stopOpacity={0.35} />
                    <stop offset="95%" stopColor={COLORS.teal}  stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="cBlk" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor={COLORS.red} stopOpacity={0.35} />
                    <stop offset="95%" stopColor={COLORS.red} stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.07)" />
                <XAxis dataKey="day" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
                <Tooltip content={<CustomTooltip />} />
                <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 12 }} />
                <Area type="monotone" dataKey="requests" name="Requests"  stroke={COLORS.teal} fill="url(#cReq)" strokeWidth={2} dot={false} />
                <Area type="monotone" dataKey="blocked"  name="Blocked"   stroke={COLORS.red}  fill="url(#cBlk)" strokeWidth={2} dot={false} />
              </AreaChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* Bar chart — avg risk score over time */}
        <div className="chart-card">
          <h2 className="chart-title">Average Risk Score / Day</h2>
          {loadingSeries ? (
            <div className="chart-skeleton" />
          ) : (
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={series} margin={{ top: 10, right: 20, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,.07)" />
                <XAxis dataKey="day" tick={{ fill: '#9ca3af', fontSize: 11 }} />
                <YAxis domain={[0, 100]} tick={{ fill: '#9ca3af', fontSize: 11 }} />
                <Tooltip content={<CustomTooltip />} />
                <Bar dataKey="avg_risk_score" name="Avg Risk" fill={COLORS.violet} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}
