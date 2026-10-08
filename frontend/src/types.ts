// Shapes returned by the API, shared by the pages. Optional fields are the ones a list may omit.
import axios from 'axios';

/** Readable message from an API error (falls back when the server gave none). */
export const errorMessage = (err: unknown, fallback: string): string =>
  axios.isAxiosError(err) ? err.response?.data?.detail || fallback : fallback;

export interface Plan {
  id: string;
  name: string;
  scope: string;
  tagline: string;
  price_monthly: number;
  price_yearly: number;
  popular: boolean;
  features: string[];
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string | null;
  type: string;
  is_read: boolean;
  created_at?: string | null;
}

export interface FinancialEntryRow {
  id: string;
  type: 'RECEITA' | 'DESPESA';
  amount: number;
  description: string | null;
  category?: string | null;
  due_date?: string | null;
  status: string;
}

export interface Supplier {
  id: string;
  name: string;
  cnpj_cpf?: string | null;
  category?: string | null;
  email?: string | null;
  is_active: boolean;
}

export interface Employee {
  id: string;
  full_name: string;
  email: string;
  role: string;
  phone?: string | null;
  contract_type: string;
  base_salary: number;
  ctc_monthly?: number | null;
  hourly_rate?: number | null;
  is_active: boolean;
}

export interface SalaryHistoryItem {
  id: string;
  base_salary: number;
  ctc_monthly: number | null;
  changed_at: string;
  reason: string | null;
}

export interface Project {
  id: string;
  name: string;
  description?: string | null;
  client_id?: string | null;
}

export interface Client {
  id: string;
  name: string;
}

export interface CardComment {
  id: string;
  author: string;
  content: string;
  created_at: string;
}

export interface KanbanCard {
  id: string;
  title: string;
  description?: string | null;
  priority?: string | null;
  status?: string | null;
  assignee?: string | null;
  cost_per_task?: number | null;
  total_time_seconds?: number | null;
  column_id?: string;
  comments?: CardComment[];
}

export interface KanbanColumn {
  id: string;
  name: string;
  cards: KanbanCard[];
}

export interface Board {
  project: Project | null;
  client: Client | null;
  columns: KanbanColumn[];
}
