import { apiFetch } from './api.ts';
import { UserProfile } from '../types.ts';

export const authApi = {
  getProfile: async (): Promise<{ user: UserProfile; authenticated: boolean }> => {
    return apiFetch<{ user: UserProfile; authenticated: boolean }>('/api/auth/me');
  },

  login: async (email: string, password?: string): Promise<{ user: UserProfile; token: string }> => {
    const res = await apiFetch<any>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    const token = res.access_token || res.token;
    if (token) {
      localStorage.setItem('astra_token', token);
    }
    return res;
  },

  register: async (name: string, email: string, password?: string): Promise<{ user: UserProfile; token: string }> => {
    const res = await apiFetch<any>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ name, email, password }),
    });
    const token = res.access_token || res.token;
    if (token) {
      localStorage.setItem('astra_token', token);
    }
    return res;
  },

  verifyEmail: async (email: string, code?: string): Promise<{ success: boolean; user: UserProfile }> => {
    return apiFetch<{ success: boolean; user: UserProfile }>('/api/auth/verify-email', {
      method: 'POST',
      body: JSON.stringify({ email, code }),
    });
  },

  completeOnboarding: async (currency: string): Promise<{ success: boolean; user: UserProfile }> => {
    return apiFetch<{ success: boolean; user: UserProfile }>('/api/auth/onboarding', {
      method: 'POST',
      body: JSON.stringify({ currency }),
    });
  },

  logout: () => {
    localStorage.removeItem('astra_token');
  },
};
