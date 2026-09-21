import { motion, AnimatePresence } from 'framer-motion';

interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  isDestructive?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmModal({
  isOpen,
  title,
  message,
  confirmLabel = 'Confirmar',
  cancelLabel = 'Cancelar',
  isDestructive = false,
  onConfirm,
  onCancel,
}: ConfirmModalProps) {
  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[9990] flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/70 backdrop-blur-sm"
            onClick={onCancel}
          />
          <motion.div
            initial={{ opacity: 0, scale: 0.95, y: 15 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 15 }}
            className="relative bg-surface-container-high border border-border-subtle p-6 sm:p-8 rounded-2xl shadow-2xl w-[90vw] max-w-[440px] z-10"
          >
            <div className="flex items-start gap-4 mb-5">
              <div
                className={`w-12 h-12 rounded-xl flex items-center justify-center shrink-0 ${
                  isDestructive
                    ? 'bg-error/15 text-error border border-error/30'
                    : 'bg-primary/15 text-primary border border-primary/30'
                }`}
              >
                <span className="material-symbols-outlined text-[24px]">
                  {isDestructive ? 'warning' : 'help'}
                </span>
              </div>
              <div>
                <h3 className="font-headline-sm text-headline-sm text-on-surface mb-1">{title}</h3>
                <p className="text-body-sm text-on-surface-variant leading-relaxed">{message}</p>
              </div>
            </div>

            <div className="flex justify-end gap-3 pt-4 border-t border-border-subtle">
              <button
                type="button"
                onClick={onCancel}
                className="px-5 py-2.5 rounded-xl font-label-md text-on-surface hover:bg-surface-container-highest transition-colors"
              >
                {cancelLabel}
              </button>
              <button
                type="button"
                onClick={onConfirm}
                className={`px-5 py-2.5 rounded-xl font-label-md text-white font-semibold transition-all shadow-lg ${
                  isDestructive
                    ? 'bg-error hover:bg-error/90 shadow-error/20'
                    : 'bg-primary hover:bg-primary/90 text-on-primary shadow-primary/20'
                }`}
              >
                {confirmLabel}
              </button>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
