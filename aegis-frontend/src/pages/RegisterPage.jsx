import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { authAPI } from '../api/client';
import { Shield, Loader } from 'lucide-react';
import toast from 'react-hot-toast';

export default function RegisterPage() {
  const navigate = useNavigate();
  const [form, setForm]     = useState({ email: '', password: '', role: 'viewer' });
  const [loading, setLoading] = useState(false);

  const change = (k) => (e) => setForm(f => ({ ...f, [k]: e.target.value }));

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await authAPI.register(form.email, form.password, form.role);
      toast.success('Account created — please sign in');
      navigate('/login');
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Registration failed');
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
        <h1 className="auth-title">Create Account</h1>
        <p className="auth-subtitle">AegisAI Governance Platform</p>

        <form className="auth-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="reg-email">Email</label>
            <input id="reg-email" type="email" value={form.email} onChange={change('email')}
              placeholder="you@company.com" required />
          </div>
          <div className="form-group">
            <label htmlFor="reg-pw">Password</label>
            <input id="reg-pw" type="password" value={form.password} onChange={change('password')}
              placeholder="min 8 characters" required minLength={8} />
          </div>
          <div className="form-group">
            <label htmlFor="reg-role">Role</label>
            <select id="reg-role" value={form.role} onChange={change('role')}>
              <option value="viewer">Viewer</option>
              <option value="analyst">Analyst</option>
              <option value="admin">Admin</option>
            </select>
          </div>

          <button className="btn-primary" type="submit" disabled={loading}>
            {loading ? <Loader size={18} className="spin" /> : 'Register'}
          </button>
        </form>

        <p className="auth-switch">
          Already have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
