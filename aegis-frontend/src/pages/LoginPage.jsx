import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Shield, Eye, EyeOff, Loader } from 'lucide-react';
import toast from 'react-hot-toast';

export default function LoginPage() {
  const { login } = useAuth();
  const navigate   = useNavigate();
  const [email, setEmail]       = useState('');
  const [password, setPassword] = useState('');
  const [show, setShow]         = useState(false);
  const [loading, setLoading]   = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success('Welcome back!');
      navigate('/dashboard');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-glow" />
      <div className="auth-card">
        <div className="auth-logo">
          <Shield size={40} />
        </div>
        <h1 className="auth-title">AegisAI</h1>
        <p className="auth-subtitle">Enterprise AI Governance Platform</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="analyst@company.com"
              required
            />
          </div>

          <div className="form-group">
            <label htmlFor="password">Password</label>
            <div className="input-pw-wrap">
              <input
                id="password"
                type={show ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                required
              />
              <button type="button" className="pw-toggle" onClick={() => setShow(s => !s)}>
                {show ? <EyeOff size={16} /> : <Eye size={16} />}
              </button>
            </div>
          </div>

          <button className="btn-primary" type="submit" disabled={loading}>
            {loading ? <Loader size={18} className="spin" /> : 'Sign in'}
          </button>
        </form>

        <p className="auth-switch">
          No account?{' '}
          <Link to="/register">Register</Link>
        </p>
      </div>
    </div>
  );
}
