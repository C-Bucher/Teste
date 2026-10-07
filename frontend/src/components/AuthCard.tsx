import type { ReactNode } from 'react';
import { motion } from 'framer-motion';

/** The centered glass card used by the public auth pages (login, password recovery, 2FA). */
export default function AuthCard({ subtitle, children }: { subtitle: string; children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background flex flex-col justify-center items-center relative overflow-hidden font-sans" style={{ width: '100vw' }}>
      <div className="absolute top-[-20%] left-[-10%] w-[50%] h-[50%] bg-primary/20 rounded-full blur-[150px] pointer-events-none" />
      <div className="absolute bottom-[-20%] right-[-10%] w-[50%] h-[50%] bg-secondary/20 rounded-full blur-[150px] pointer-events-none" />
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="z-10"
        style={{ width: '100%', maxWidth: '448px', minWidth: '320px', padding: '16px' }}
      >
        <div className="rounded-2xl shadow-2xl border border-border-subtle bg-glass-bg backdrop-blur-xl" style={{ padding: '32px', width: '100%' }}>
          <div className="text-center mb-8">
            <h1 className="text-4xl font-bold text-on-surface mb-2 tracking-tight" style={{ fontFamily: '"Outfit", sans-serif' }}>
              TechConnect <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary">Premium</span>
            </h1>
            <p className="text-on-surface-variant">{subtitle}</p>
          </div>
          {children}
        </div>
      </motion.div>
    </div>
  );
}

export const authInputClass =
  'block w-full px-4 py-3 border border-border-subtle rounded-xl bg-surface-container text-on-surface placeholder:text-outline focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent transition-all';

export const authButtonClass =
  'w-full flex justify-center items-center gap-2 py-3 px-4 rounded-xl shadow-lg shadow-primary/20 text-sm font-semibold text-on-primary bg-gradient-to-r from-primary to-secondary hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-all';
