import { useState, useCallback, useMemo } from 'react';
import type { FC, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ToastContext, type Toast, type ToastType } from './ToastContext';

const ICONS: Record<ToastType, string> = {
  success: 'check_circle',
  error: 'error',
  warning: 'warning',
  info: 'info',
};

const STYLES: Record<ToastType, { border: string; bg: string; iconColor: string }> = {
  success: {
    border: 'border-success/30',
    bg: 'bg-[#121f1d]/90',
    iconColor: 'text-success',
  },
  error: {
    border: 'border-error/30',
    bg: 'bg-[#261318]/90',
    iconColor: 'text-error',
  },
  warning: {
    border: 'border-warning/30',
    bg: 'bg-[#241c10]/90',
    iconColor: 'text-warning',
  },
  info: {
    border: 'border-primary/30',
    bg: 'bg-[#101827]/90',
    iconColor: 'text-primary',
  },
};

export const ToastProvider: FC<{ children: ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const removeToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const showToast = useCallback(
    ({ type, title, message, duration = 4000 }: Omit<Toast, 'id'>) => {
      const id = Math.random().toString(36).substring(2, 9);
      const newToast: Toast = { id, type, title, message, duration };

      setToasts((prev) => [...prev, newToast]);

      if (duration > 0) {
        setTimeout(() => {
          removeToast(id);
        }, duration);
      }
    },
    [removeToast]
  );

  const success = useCallback((message: string, title?: string) => showToast({ type: 'success', message, title }), [showToast]);
  const error = useCallback((message: string, title?: string) => showToast({ type: 'error', message, title }), [showToast]);
  const info = useCallback((message: string, title?: string) => showToast({ type: 'info', message, title }), [showToast]);
  const warning = useCallback((message: string, title?: string) => showToast({ type: 'warning', message, title }), [showToast]);

  const actions = useMemo(() => ({ showToast, removeToast, success, error, info, warning }), [showToast, removeToast, success, error, info, warning]);

  return (
    <ToastContext.Provider value={actions}>
      {children}
      {/* Toast Render Container */}
      <div className="fixed bottom-5 right-5 z-[9999] flex flex-col gap-2.5 max-w-sm w-full pointer-events-none px-3 sm:px-0">
        <AnimatePresence>
          {toasts.map((t) => {
            const style = STYLES[t.type];
            const icon = ICONS[t.type];
            return (
              <motion.div
                key={t.id}
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, scale: 0.9, transition: { duration: 0.15 } }}
                layout
                className={`pointer-events-auto flex items-start gap-3 p-4 rounded-xl border ${style.border} ${style.bg} backdrop-blur-xl shadow-2xl text-on-surface`}
              >
                <span className={`material-symbols-outlined text-[22px] shrink-0 mt-0.5 ${style.iconColor}`}>
                  {icon}
                </span>
                <div className="flex-1 min-w-0">
                  {t.title && <h4 className="font-bold text-sm text-white mb-0.5">{t.title}</h4>}
                  <p className="text-xs text-slate-300 leading-relaxed break-words">{t.message}</p>
                </div>
                <button
                  onClick={() => removeToast(t.id)}
                  className="text-slate-400 hover:text-white p-1 -mr-1 -mt-1 rounded-lg hover:bg-white/10 transition-colors"
                >
                  <span className="material-symbols-outlined text-[16px]">close</span>
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
};
