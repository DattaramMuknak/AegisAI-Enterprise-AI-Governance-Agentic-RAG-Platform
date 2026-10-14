import { useState, useRef, useEffect } from 'react';
import { chatAPI } from '../api/client';
import RiskMeter from '../components/RiskMeter';
import GovernanceBadge from '../components/GovernanceBadge';
import { Send, Bot, User, ChevronDown, ChevronUp, Loader, Zap } from 'lucide-react';
import toast from 'react-hot-toast';

function Message({ msg }) {
  const [expanded, setExpanded] = useState(false);
  const isUser = msg.role === 'user';

  return (
    <div className={`msg-row ${isUser ? 'msg-user' : 'msg-ai'}`}>
      <div className="msg-avatar">
        {isUser ? <User size={16} /> : <Bot size={16} />}
      </div>
      <div className="msg-bubble-wrap">
        <div className="msg-bubble">
          <p className="msg-text">{msg.content}</p>
        </div>

        {msg.governance && (
          <div className="gov-panel">
            <div className="gov-row">
              <GovernanceBadge decision={msg.governance.governance_decision} />
              <span className="gov-chip">Risk {msg.governance.risk_score}</span>
              <span className="gov-chip">Grounding {(msg.governance.grounding_score * 100).toFixed(0)}%</span>
              {msg.governance.pii_detected && <span className="gov-chip warn">PII</span>}
              {msg.governance.hallucination_flag && <span className="gov-chip warn">Hallucination</span>}
              {msg.governance.prompt_injection_detected && <span className="gov-chip danger">Injection</span>}
              <span className="gov-chip muted">{msg.latency_ms}ms</span>
              <button className="gov-expand" onClick={() => setExpanded(e => !e)}>
                {expanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                {expanded ? 'Less' : 'Details'}
              </button>
            </div>

            {expanded && (
              <div className="gov-detail">
                <div className="gov-detail-grid">
                  <div>
                    <span className="gd-label">Confidence</span>
                    <span className="gd-val">{msg.governance.confidence}</span>
                  </div>
                  <div>
                    <span className="gd-label">Toxicity</span>
                    <span className="gd-val">{(msg.governance.toxicity_score * 100).toFixed(1)}%</span>
                  </div>
                  <div>
                    <span className="gd-label">Policy Violation</span>
                    <span className="gd-val">{msg.governance.policy_violation ? '⚠ Yes' : 'No'}</span>
                  </div>
                  <div>
                    <span className="gd-label">Agent Path</span>
                    <span className="gd-val">{msg.agent_path?.join(' → ')}</span>
                  </div>
                  {msg.governance.block_reason && (
                    <div className="gd-full">
                      <span className="gd-label">Block Reason</span>
                      <span className="gd-val danger">{msg.governance.block_reason}</span>
                    </div>
                  )}
                  {msg.governance.policy_violation_reason && (
                    <div className="gd-full">
                      <span className="gd-label">Policy Reason</span>
                      <span className="gd-val warn">{msg.governance.policy_violation_reason}</span>
                    </div>
                  )}
                </div>

                {msg.sources?.length > 0 && (
                  <div className="sources-wrap">
                    <p className="sources-title">Retrieved Sources ({msg.sources.length})</p>
                    {msg.sources.map((s, i) => (
                      <div key={i} className="source-item">
                        <span className="source-name">{s.filename || s.doc_id}</span>
                        <span className="source-score">score {s.score.toFixed(3)}</span>
                        <p className="source-chunk">{s.chunk}</p>
                      </div>
                    ))}
                  </div>
                )}

                <div className="trace-id">trace: {msg.trace_id}</div>
              </div>
            )}
          </div>
        )}
      </div>
      {!isUser && msg.governance && (
        <div className="msg-risk">
          <RiskMeter score={msg.governance.risk_score} />
        </div>
      )}
    </div>
  );
}

export default function ChatPage() {
  const [messages, setMessages] = useState([
    { role: 'ai', content: 'Hello! I am AegisAI — your governed enterprise AI copilot. Ask me anything about your policies, SOPs, or compliance documents. Every response is risk-scored, PII-checked, and fully audited.' }
  ]);
  const [prompt, setPrompt]   = useState('');
  const [topK, setTopK]       = useState(4);
  const [loading, setLoading] = useState(false);
  const bottomRef             = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const send = async () => {
    const text = prompt.trim();
    if (!text || loading) return;
    setPrompt('');
    setMessages(m => [...m, { role: 'user', content: text }]);
    setLoading(true);
    try {
      const { data } = await chatAPI.send(text, topK);
      setMessages(m => [...m, {
        role: 'ai',
        content: data.answer || '(Response blocked by governance policy)',
        governance: data.governance,
        sources:    data.sources,
        agent_path: data.agent_path,
        latency_ms: data.latency_ms,
        trace_id:   data.trace_id,
      }]);
    } catch (err) {
      toast.error('Request failed: ' + (err.response?.data?.detail || err.message));
      setMessages(m => [...m, { role: 'ai', content: '⚠ Error contacting the AI gateway. Please retry.' }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); send(); }
  };

  return (
    <div className="page chat-page">
      <div className="page-header">
        <div>
          <h1 className="page-title">AI Governance Copilot</h1>
          <p className="page-sub">Every query runs through the full agentic governance pipeline</p>
        </div>
        <div className="chat-topk">
          <label htmlFor="topk-sel">Sources (top-k)</label>
          <select id="topk-sel" value={topK} onChange={e => setTopK(+e.target.value)}>
            {[1,2,4,6,8,10].map(n => <option key={n} value={n}>{n}</option>)}
          </select>
        </div>
      </div>

      <div className="chat-messages">
        {messages.map((m, i) => <Message key={i} msg={m} />)}
        {loading && (
          <div className="msg-row msg-ai">
            <div className="msg-avatar"><Bot size={16} /></div>
            <div className="msg-bubble typing">
              <Loader size={16} className="spin" />
              <span>Processing through governance pipeline…</span>
            </div>
          </div>
        )}
        <div ref={bottomRef} />
      </div>

      <div className="chat-input-bar">
        <textarea
          id="chat-input"
          className="chat-textarea"
          rows={2}
          value={prompt}
          onChange={e => setPrompt(e.target.value)}
          onKeyDown={handleKey}
          placeholder="Ask about policies, SOPs, compliance… (Enter to send)"
          disabled={loading}
        />
        <button id="chat-send" className="btn-send" onClick={send} disabled={loading || !prompt.trim()}>
          {loading ? <Loader size={20} className="spin" /> : <><Zap size={16} /> Send</>}
        </button>
      </div>
    </div>
  );
}
