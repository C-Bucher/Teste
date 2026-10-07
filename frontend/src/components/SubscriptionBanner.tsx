import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import api from '../api';

interface Access { allowed: boolean; status: string; trial_ends_at: string | null }

/** Thin bar under the top nav while on trial or with an overdue payment. */
export default function SubscriptionBanner() {
  const [access, setAccess] = useState<Access | null>(null);

  useEffect(() => {
    api.get('/payments/access').then((res) => setAccess(res.data)).catch(() => setAccess(null));
  }, []);

  if (!access || !access.allowed) return null;
  if (access.status === 'TRIAL' && access.trial_ends_at) {
    const days = Math.max(0, Math.ceil((new Date(`${access.trial_ends_at}Z`).getTime() - Date.now()) / 86400000));
    return (
      <div className="mb-md px-md py-2 rounded-xl bg-primary/10 border border-primary/20 text-body-sm text-on-surface flex flex-wrap items-center justify-between gap-sm">
        <span>Período de teste: {days === 0 ? 'termina hoje' : `${days} dia(s) restante(s)`}.</span>
        <Link to="/planos" className="text-primary font-label-md hover:underline">Escolher plano</Link>
      </div>
    );
  }
  if (access.status === 'PAST_DUE') {
    return (
      <div className="mb-md px-md py-2 rounded-xl bg-error/10 border border-error/30 text-body-sm text-on-surface flex flex-wrap items-center justify-between gap-sm">
        <span>Há um pagamento em atraso. Regularize para não ter o acesso suspenso.</span>
        <Link to="/assinatura" className="text-error font-label-md hover:underline">Ver cobrança</Link>
      </div>
    );
  }
  return null;
}
