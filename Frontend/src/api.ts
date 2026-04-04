const API_URL = import.meta.env.VITE_API_URL || 'https://whitea.ru/api';

// --- Определение контекста ---

export function isInsideMax(): boolean {
  return !!window.WebApp?.initData;
}

// --- Вход по почте ---

export async function requestOtp(email: string) {
  const res = await fetch(`${API_URL}/auth/request-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function verifyOtp(email: string, code: string) {
  const res = await fetch(`${API_URL}/auth/verify-otp`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, code }),
  });
  if (!res.ok) throw await res.json();
  const data = await res.json();
  localStorage.setItem('token', data.token);
  localStorage.setItem('role', data.role);
  return data;
}

// --- Гостевой вход (только из MAX) ---

export async function guestLogin() {
  const initData = window.WebApp?.initData;
  if (!initData) throw new Error('Гостевой вход доступен только из MAX');
  const res = await fetch(`${API_URL}/auth/guest`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ init_data: initData }),
  });
  if (!res.ok) throw await res.json();
  const data = await res.json();
  localStorage.setItem('token', data.token);
  localStorage.setItem('role', data.role);
  return data;
}

// --- Выход ---

export async function logout() {
  const token = localStorage.getItem('token');
  if (token) {
    await fetch(`${API_URL}/auth/logout`, {
      method: 'POST',
      headers: { 'Authorization': `Bearer ${token}` },
    }).catch(() => {});
  }
  localStorage.removeItem('token');
  localStorage.removeItem('role');
}

// --- Обновление токена ---

export async function refreshToken() {
  const token = localStorage.getItem('token');
  if (!token) throw new Error('Нет токена');
  const res = await fetch(`${API_URL}/auth/refresh`, {
    method: 'POST',
    headers: { 'Authorization': `Bearer ${token}` },
  });
  if (!res.ok) throw await res.json();
  const data = await res.json();
  localStorage.setItem('token', data.token);
  return data;
}

// --- Хелперы ---

export function getRole(): string {
  return localStorage.getItem('role') || '';
}

export function isStaff(): boolean {
  return getRole() === 'staff';
}

export function isGuest(): boolean {
  return getRole() === 'guest';
}

export function isLoggedIn(): boolean {
  return !!localStorage.getItem('token');
}

export async function authFetch(url: string, options: RequestInit = {}) {
  const token = localStorage.getItem('token');
  const res = await fetch(`${API_URL}${url}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...options.headers,
    },
  });
  if (res.status === 401) {
    localStorage.removeItem('token');
    localStorage.removeItem('role');
    // Очистить cookie с токеном (если есть)
    document.cookie.split(';').forEach((c) => {
      const name = c.split('=')[0].trim();
      if (name === 'token' || name === 'role') {
        document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
      }
    });
    window.location.reload();
  }
  return res;
}

// --- Источники ---

export async function getSources() {
  const res = await authFetch('/sources');
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function getPendingSources() {
  const res = await authFetch('/sources/pending');
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function addRssSource(url: string) {
  const res = await authFetch('/sources/rss', {
    method: 'POST',
    body: JSON.stringify({ url }),
  });
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function createSource(data: {
  platform: 'max' | 'telegram';
  name: string;
  description?: string;
  source_id: string;
}) {
  const res = await authFetch('/sources', {
    method: 'POST',
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function updateSource(id: number, data: {
  is_active?: boolean;
  name?: string;
  description?: string;
}) {
  const res = await authFetch(`/sources/${id}`, {
    method: 'PATCH',
    body: JSON.stringify(data),
  });
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function approveSource(id: number) {
  const res = await authFetch(`/sources/${id}/approve`, { method: 'POST' });
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function rejectSource(id: number) {
  const res = await authFetch(`/sources/${id}/reject`, { method: 'POST' });
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function deleteSource(id: number) {
  const res = await authFetch(`/sources/${id}`, { method: 'DELETE' });
  if (!res.ok) throw await res.json();
  return res.json();
}

// --- Дашборд ---

export async function getTopics(period?: string, industry?: string) {
  const params = new URLSearchParams();
  if (period) params.set('period', period);
  if (industry) params.set('industry', industry);
  const qs = params.toString();
  const res = await authFetch(`/dashboard/topics${qs ? '?' + qs : ''}`);
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function getTopicDetail(topicId: number) {
  const res = await authFetch(`/dashboard/topics/${topicId}`);
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function sendTopicPdf(topicId: number) {
  const res = await authFetch(`/dashboard/topics/${topicId}/send-pdf`, { method: 'POST' });
  if (!res.ok) throw await res.json();
  return res.json();
}

export async function getDashboardStats() {
  const res = await authFetch('/dashboard/stats');
  if (!res.ok) throw await res.json();
  return res.json();
}
