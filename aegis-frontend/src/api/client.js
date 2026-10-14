import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: BASE_URL,
  headers: { 'Content-Type': 'application/json' },
});

// Inject JWT token on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('aegis_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-logout on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('aegis_token');
      localStorage.removeItem('aegis_role');
      window.location.href = '/login';
    }
    return Promise.reject(err);
  }
);

export default api;

// ─── Auth ────────────────────────────────────────────────────────────────────
export const authAPI = {
  login: (email, password) => {
    const form = new URLSearchParams();
    form.append('username', email);
    form.append('password', password);
    return api.post('/api/v1/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  },
  register: (email, password, role = 'viewer') =>
    api.post('/api/v1/auth/register', { email, password, role }),
};

// ─── Chat ─────────────────────────────────────────────────────────────────────
export const chatAPI = {
  send: (prompt, top_k = 4) =>
    api.post('/api/v1/chat', { prompt, top_k }),
};

// ─── Dashboard ───────────────────────────────────────────────────────────────
export const dashboardAPI = {
  stats: () => api.get('/api/v1/dashboard/stats'),
  timeseries: (days = 14) => api.get(`/api/v1/dashboard/timeseries?days=${days}`),
};

// ─── Audit ───────────────────────────────────────────────────────────────────
export const auditAPI = {
  list: (params = {}) => api.get('/api/v1/audit', { params }),
  detail: (traceId) => api.get(`/api/v1/audit/${traceId}`),
};

// ─── Documents ───────────────────────────────────────────────────────────────
export const documentsAPI = {
  list: () => api.get('/api/v1/documents'),
  upload: (file, sourceType = 'policy') => {
    const fd = new FormData();
    fd.append('file', file);
    fd.append('source_type', sourceType);
    return api.post('/api/v1/documents/upload', fd, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  },
};
