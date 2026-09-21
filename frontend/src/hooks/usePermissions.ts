import { useEffect, useState } from 'react';
import api from '../api';

export const ALL_MODULES = ['dashboard', 'kanban', 'equipe', 'financeiro', 'fornecedores', 'configuracoes', 'exportacao', 'ia'];
const FALLBACK_MODULES = ['dashboard', 'kanban'];

// Cache compartilhado (chave = token atual) para que Layout + guard da página façam UMA requisição.
const cache = new Map<string, Promise<string[]>>();

export function clearPermissionsCache() {
  cache.clear();
}

function getRole(): string {
  try {
    return JSON.parse(localStorage.getItem('user') || '{}').role || '';
  } catch {
    return '';
  }
}

function fetchModules(token: string): Promise<string[]> {
  let p = cache.get(token);
  if (!p) {
    p = api
      .get('/permissions/mine')
      .then((res) => res.data.modules as string[])
      .catch((err) => {
        console.error('Erro ao carregar permissões', err);
        cache.delete(token); // não cacheia falha: um próximo mount tenta de novo
        return FALLBACK_MODULES;
      });
    cache.set(token, p);
  }
  return p;
}

export function usePermissions() {
  const isAdmin = getRole() === 'ADMIN';
  const token = localStorage.getItem('token') || '';
  const [modules, setModules] = useState<string[] | null>(null);

  useEffect(() => {
    if (isAdmin) return;
    let active = true;
    fetchModules(token).then((m) => {
      if (active) setModules(m);
    });
    return () => {
      active = false;
    };
  }, [isAdmin, token]);

  const list = isAdmin ? ALL_MODULES : modules ?? [];
  const loading = !isAdmin && modules === null;
  return { modules: list, loading, can: (m: string) => list.includes(m) };
}
