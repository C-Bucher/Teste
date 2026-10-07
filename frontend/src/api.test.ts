import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import axios, { type AxiosAdapter, type InternalAxiosRequestConfig } from 'axios';
import api, { clearSession, saveSession } from './api';

type Reply = { status: number; data?: unknown; headers?: Record<string, string> };

/** Routes every request (the api instance and the bare axios used for refresh) through `handler`. */
function mockAdapter(handler: (config: InternalAxiosRequestConfig) => Reply) {
  const adapter: AxiosAdapter = async (config) => {
    const r = handler(config);
    const response = { data: r.data ?? {}, status: r.status, statusText: '', headers: r.headers ?? {}, config };
    if (r.status >= 400) {
      throw new axios.AxiosError('erro', String(r.status), config, null, response);
    }
    return response;
  };
  api.defaults.adapter = adapter;
  axios.defaults.adapter = adapter;
}

describe('api client', () => {
  const assign = vi.fn();

  beforeEach(() => {
    assign.mockReset();
    Object.defineProperty(window, 'location', { value: { pathname: '/financeiro', assign }, writable: true });
  });

  afterEach(() => {
    clearSession();
  });

  it('sends the access token', async () => {
    saveSession({ access_token: 'a1', refresh_token: 'r1' });
    let auth: unknown;
    mockAdapter((config) => { auth = config.headers?.Authorization; return { status: 200 }; });
    await api.get('/plans/');
    expect(auth).toBe('Bearer a1');
  });

  it('renews an expired session once and retries the request', async () => {
    saveSession({ access_token: 'velho', refresh_token: 'r1' });
    const seen: string[] = [];
    mockAdapter((config) => {
      if (config.url?.endsWith('/auth/refresh')) return { status: 200, data: { access_token: 'novo', refresh_token: 'r2' } };
      seen.push(String(config.headers?.Authorization));
      return config.headers?.Authorization === 'Bearer novo' ? { status: 200, data: { ok: true } } : { status: 401 };
    });
    const res = await api.get('/suppliers/');
    expect(res.data).toEqual({ ok: true });
    expect(seen).toEqual(['Bearer velho', 'Bearer novo']);
    expect(localStorage.getItem('refresh_token')).toBe('r2');
  });

  it('logs out when the session cannot be renewed', async () => {
    saveSession({ access_token: 'velho', refresh_token: 'r1' });
    localStorage.setItem('user', '{}');
    mockAdapter(() => ({ status: 401 }));
    await expect(api.get('/suppliers/')).rejects.toBeTruthy();
    expect(localStorage.getItem('token')).toBeNull();
    expect(localStorage.getItem('user')).toBeNull();
    expect(assign).toHaveBeenCalledWith('/');
  });

  it('does not try to renew on a wrong password at login', async () => {
    const urls: string[] = [];
    mockAdapter((config) => { urls.push(String(config.url)); return { status: 401, data: { detail: 'Credenciais invalidas' } }; });
    await expect(api.post('/auth/login', {})).rejects.toBeTruthy();
    expect(urls).toEqual(['/auth/login']);
    expect(assign).not.toHaveBeenCalled();
  });

  it('sends the person to billing when the subscription is blocked', async () => {
    saveSession({ access_token: 'a1', refresh_token: 'r1' });
    mockAdapter(() => ({ status: 402, headers: { 'x-subscription': 'blocked' } }));
    await expect(api.get('/suppliers/')).rejects.toBeTruthy();
    expect(assign).toHaveBeenCalledWith('/assinatura?bloqueado=1');
  });

  it('leaves other 402s (plan limits) to the screen', async () => {
    saveSession({ access_token: 'a1', refresh_token: 'r1' });
    mockAdapter(() => ({ status: 402, data: { detail: 'Faça upgrade' } }));
    await expect(api.post('/bank/connect-token', {})).rejects.toBeTruthy();
    expect(assign).not.toHaveBeenCalled();
  });
});
