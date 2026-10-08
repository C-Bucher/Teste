import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import axios from 'axios';
import type { ReactNode } from 'react';
import { ToastProvider } from '../context/ToastProvider';
import { errorMessage } from '../types';
import { TERMS_VERSION } from '../legal';

const { apiMock } = vi.hoisted(() => ({ apiMock: { get: vi.fn(), post: vi.fn() } }));
vi.mock('../api', () => ({ default: apiMock, saveSession: vi.fn(), clearSession: vi.fn() }));

import { EsqueciSenha, RedefinirSenha } from './RecuperarSenha';
import { AceiteTermos } from './Legal';
import SubscriptionBanner from '../components/SubscriptionBanner';

const wrap = (ui: ReactNode, path = '/') => render(
  <ToastProvider>
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="*" element={ui} />
      </Routes>
    </MemoryRouter>
  </ToastProvider>,
);

beforeEach(() => {
  apiMock.get.mockReset();
  apiMock.post.mockReset();
});

describe('errorMessage', () => {
  it('uses the server detail when there is one', () => {
    const err = new axios.AxiosError('x', '400', undefined, null, { data: { detail: 'Plano inválido' }, status: 400, statusText: '', headers: {}, config: {} as never });
    expect(errorMessage(err, 'padrão')).toBe('Plano inválido');
    expect(errorMessage(new Error('rede'), 'padrão')).toBe('padrão');
  });
});

describe('password recovery', () => {
  it('asks for the e-mail and always confirms the same way', async () => {
    apiMock.post.mockResolvedValue({ data: {} });
    wrap(<EsqueciSenha />);
    await userEvent.type(screen.getByPlaceholderText('voce@empresa.com.br'), 'ana@empresa.com.br');
    await userEvent.click(screen.getByRole('button', { name: 'Enviar link' }));
    expect(apiMock.post).toHaveBeenCalledWith('/auth/forgot-password', { email: 'ana@empresa.com.br' });
    expect(await screen.findByText(/vai receber um link/)).toBeInTheDocument();
  });

  it('refuses a confirmation that does not match, then sends the token', async () => {
    apiMock.post.mockResolvedValue({ data: {} });
    const { container } = wrap(<RedefinirSenha />, '/redefinir-senha?token=abc123');
    const [pwd, confirm] = Array.from(container.querySelectorAll('input[type="password"]')) as HTMLInputElement[];
    await userEvent.type(pwd, 'NovaSenha1');
    await userEvent.type(confirm, 'Diferente1');
    await userEvent.click(screen.getByRole('button', { name: 'Redefinir senha' }));
    expect(apiMock.post).not.toHaveBeenCalled();

    await userEvent.clear(confirm);
    await userEvent.type(confirm, 'NovaSenha1');
    await userEvent.click(screen.getByRole('button', { name: 'Redefinir senha' }));
    expect(apiMock.post).toHaveBeenCalledWith('/auth/reset-password', { token: 'abc123', new_password: 'NovaSenha1' });
  });

  it('explains an incomplete link', () => {
    wrap(<RedefinirSenha />, '/redefinir-senha');
    expect(screen.getByText(/Link incompleto/)).toBeInTheDocument();
  });
});

describe('terms acceptance', () => {
  it('only continues after the box is ticked, sending the current version', async () => {
    apiMock.post.mockResolvedValue({ data: { terms_version: TERMS_VERSION } });
    wrap(<AceiteTermos />);
    const button = screen.getByRole('button', { name: 'Continuar' });
    expect(button).toBeDisabled();
    await userEvent.click(screen.getByRole('checkbox'));
    await userEvent.click(button);
    expect(apiMock.post).toHaveBeenCalledWith('/auth/accept-terms', { version: TERMS_VERSION });
  });
});

describe('subscription banner', () => {
  it('counts the trial days left', async () => {
    const inThreeDays = new Date(Date.now() + 2.5 * 86400000).toISOString().replace('Z', '');
    apiMock.get.mockResolvedValue({ data: { allowed: true, status: 'TRIAL', trial_ends_at: inThreeDays } });
    wrap(<SubscriptionBanner />);
    expect(await screen.findByText(/3 dia\(s\) restante\(s\)/)).toBeInTheDocument();
  });

  it('warns about an overdue payment', async () => {
    apiMock.get.mockResolvedValue({ data: { allowed: true, status: 'PAST_DUE', trial_ends_at: null } });
    wrap(<SubscriptionBanner />);
    expect(await screen.findByText(/pagamento em atraso/)).toBeInTheDocument();
  });

  it('stays hidden for an active subscription', async () => {
    apiMock.get.mockResolvedValue({ data: { allowed: true, status: 'ACTIVE', trial_ends_at: null } });
    const { container } = wrap(<SubscriptionBanner />);
    await waitFor(() => expect(apiMock.get).toHaveBeenCalled());
    expect(container.textContent).toBe('');
  });
});
