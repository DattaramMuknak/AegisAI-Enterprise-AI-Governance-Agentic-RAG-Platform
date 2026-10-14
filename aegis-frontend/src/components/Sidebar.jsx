import { NavLink, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import {
  LayoutDashboard,
  MessageSquare,
  FileText,
  ClipboardList,
  LogOut,
  Shield,
  ChevronRight,
} from 'lucide-react';

const navItems = [
  { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/chat',      label: 'AI Copilot',  icon: MessageSquare },
  { to: '/documents', label: 'Documents',   icon: FileText },
  { to: '/audit',     label: 'Audit Trail', icon: ClipboardList },
];

export default function Sidebar() {
  const { role, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <Shield size={28} className="brand-icon" />
        <span className="brand-text">AegisAI</span>
      </div>
      <div className="sidebar-role-badge">
        <span className="role-label">{role.toUpperCase()}</span>
      </div>

      <nav className="sidebar-nav">
        {navItems.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} className={({ isActive }) =>
            `nav-item ${isActive ? 'active' : ''}`
          }>
            <Icon size={18} />
            <span>{label}</span>
            <ChevronRight size={14} className="nav-arrow" />
          </NavLink>
        ))}
      </nav>

      <button className="sidebar-logout" onClick={handleLogout}>
        <LogOut size={18} />
        <span>Log out</span>
      </button>
    </aside>
  );
}
