import axios from 'axios';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: `${API_URL}/api/v1`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add auth token to requests if available
api.interceptors.request.use((config) => {
  if (typeof window !== 'undefined') {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
  }
  return config;
});

// Handle token refresh on 401
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      if (typeof window !== 'undefined') {
        const refreshToken = localStorage.getItem('refresh_token');

        if (refreshToken) {
          try {
            const response = await axios.post(`${API_URL}/api/v1/auth/refresh`, {
              refresh_token: refreshToken,
            });

            const { access_token, refresh_token } = response.data;
            localStorage.setItem('access_token', access_token);
            localStorage.setItem('refresh_token', refresh_token);

            originalRequest.headers.Authorization = `Bearer ${access_token}`;
            return api(originalRequest);
          } catch (refreshError) {
            localStorage.removeItem('access_token');
            localStorage.removeItem('refresh_token');
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }
      }
    }

    return Promise.reject(error);
  }
);

export default api;

// Auth API
export const authAPI = {
  register: (data: any) => api.post('/auth/register', data),
  login: (data: any) => api.post('/auth/login', data),
  loginBiometric: (data: any) => api.post('/auth/login/biometric', data),
  refresh: (data: any) => api.post('/auth/refresh', data),
  logout: (data: any) => api.post('/auth/logout', data),
};

// User API
export const userAPI = {
  getMe: () => api.get('/users/me'),
  updateMe: (data: any) => api.patch('/users/me', data),
  enrollBiometric: (data: any) => api.post('/users/enroll-biometric', data),
  deleteBiometric: () => api.delete('/users/enroll-biometric'),
  getWallet: () => api.get('/users/wallet'),
  getCredentials: () => api.get('/users/credentials'),
  getCredentialDetails: (id: string) => api.get(`/users/credentials/${id}`),
};

// Issuer API
export const issuerAPI = {
  registerIssuer: (data: any) => api.post('/issuers/register', data),
  getMe: () => api.get('/issuers/me'),
  issueCredential: (data: any) => api.post('/issuers/issue-credential', data),
  getIssuedCredentials: () => api.get('/issuers/issued-credentials'),
  getStats: () => api.get('/issuers/stats'),
  revokeCredential: (id: string) => api.patch(`/issuers/revoke-credential/${id}`),
};

// Credential API
export const credentialAPI = {
  createShareLink: (data: any) => api.post('/credentials/share', data),
  getSharedCredentials: () => api.get('/credentials/shared'),
  revokeShareLink: (tokenId: string) => api.delete(`/credentials/share/${tokenId}`),
  downloadDocument: (id: string) => api.get(`/credentials/${id}/document`, { responseType: 'blob' }),
  getCredentialById: (id: string) => api.get(`/credentials/${id}`),
};

// Verification API (public)
export const verificationAPI = {
  verifyCredential: (shareToken: string) => api.get(`/verify/${shareToken}`),
  verifyAttribute: (shareToken: string, data: any) => api.post(`/verify/${shareToken}/verify-attribute`, data),
  getDetails: (shareToken: string) => api.get(`/verify/${shareToken}/details`),
  getAuditLogs: (credentialId: string) => api.get(`/verify/audit/${credentialId}`),
};
