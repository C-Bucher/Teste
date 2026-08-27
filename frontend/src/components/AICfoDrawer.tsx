import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X, Send, Bot, User, Sparkles, Loader2, ArrowRight } from 'lucide-react';
import api from '../api';

interface AICfoDrawerProps {
  isOpen: boolean;
  onClose: () => void;
}

interface Message {
  sender: 'ai' | 'user';
  text: string;
  timestamp: string;
}

export default function AICfoDrawer({ isOpen, onClose }: AICfoDrawerProps) {
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'ai',
      text: 'Olá! Sou o seu CFO Virtual IA. Como posso ajudar com a gestão financeira e estratégias da sua empresa hoje?',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const quickPrompts = [
    'Como está o saldo e fluxo de caixa?',
    'Qual a margem do meu DRE?',
    'Análise de custos de equipe'
  ];

  const handleSend = async (textToSend?: string) => {
    const messageText = textToSend || input;
    if (!messageText.trim() || loading) return;

    const userMsg: Message = {
      sender: 'user',
      text: messageText,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages((prev) => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const response = await api.post('/ai/chat', { message: messageText });
      const aiMsg: Message = {
        sender: 'ai',
        text: response.data.response || 'Desculpe, não consegui processar a informação no momento.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, aiMsg]);
    } catch (err) {
      const errorMsg: Message = {
        sender: 'ai',
        text: 'Ocorreu um erro ao conectar com o CFO Virtual. Por favor, tente novamente.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages((prev) => [...prev, errorMsg]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-[100] flex justify-end">
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 bg-black/60 backdrop-blur-sm"
            onClick={onClose}
          />

          {/* Drawer Sidebar */}
          <motion.div
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ type: 'spring', damping: 25, stiffness: 200 }}
            className="relative w-full max-w-[28rem] bg-[#131722] border-l border-white/10 shadow-2xl flex flex-col h-full z-10"
          >
            {/* Header */}
            <div className="p-4 border-b border-white/10 flex items-center justify-between bg-[#171b26]">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-purple-600 flex items-center justify-center shadow-lg shadow-blue-500/20">
                  <Sparkles className="w-5 h-5 text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-white text-base">CFO Virtual IA</h3>
                  <p className="text-xs text-blue-400 font-medium">Assistente Financeiro Inteligente</p>
                </div>
              </div>
              <button
                onClick={onClose}
                className="p-2 text-slate-400 hover:text-white rounded-lg hover:bg-white/5 transition-colors"
              >
                <X size={20} />
              </button>
            </div>

            {/* Chat Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-4 custom-scrollbar">
              {messages.map((msg, idx) => (
                <div
                  key={idx}
                  className={`flex gap-3 ${msg.sender === 'user' ? 'flex-row-reverse' : ''}`}
                >
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${
                      msg.sender === 'user'
                        ? 'bg-blue-600 text-white'
                        : 'bg-gradient-to-tr from-purple-600 to-blue-600 text-white'
                    }`}
                  >
                    {msg.sender === 'user' ? <User size={16} /> : <Bot size={16} />}
                  </div>

                  <div
                    className={`max-w-[80%] rounded-2xl p-3.5 text-sm ${
                      msg.sender === 'user'
                        ? 'bg-blue-600 text-white rounded-tr-none'
                        : 'bg-[#1c2130] text-slate-200 border border-white/10 rounded-tl-none'
                    }`}
                  >
                    <p className="leading-relaxed whitespace-pre-wrap">{msg.text}</p>
                    <span
                      className={`block text-[10px] mt-1.5 text-right ${
                        msg.sender === 'user' ? 'text-blue-200' : 'text-slate-500'
                      }`}
                    >
                      {msg.timestamp}
                    </span>
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex gap-3 items-center text-slate-400 text-sm italic bg-[#1c2130]/50 p-3 rounded-xl w-fit border border-white/5">
                  <Loader2 className="animate-spin text-blue-400" size={18} />
                  <span>CFO Virtual está analisando seus dados...</span>
                </div>
              )}
            </div>

            {/* Quick Prompts */}
            <div className="p-3 border-t border-white/5 bg-[#171b26]/50">
              <p className="text-[11px] font-semibold text-slate-400 mb-2 uppercase tracking-wider">
                Sugestões de Análise:
              </p>
              <div className="flex flex-wrap gap-2">
                {quickPrompts.map((prompt, i) => (
                  <button
                    key={i}
                    onClick={() => handleSend(prompt)}
                    className="text-xs bg-[#222736] hover:bg-blue-600/20 text-slate-300 hover:text-blue-300 border border-white/10 hover:border-blue-500/30 rounded-lg px-2.5 py-1.5 transition-all flex items-center gap-1"
                  >
                    {prompt}
                    <ArrowRight size={12} />
                  </button>
                ))}
              </div>
            </div>

            {/* Input Box */}
            <div className="p-4 border-t border-white/10 bg-[#171b26]">
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  handleSend();
                }}
                className="flex items-center gap-2"
              >
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Pergunte ao CFO Virtual..."
                  className="flex-1 bg-[#1c2130] border border-white/10 rounded-xl px-4 py-2.5 text-sm text-white placeholder:text-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <button
                  type="submit"
                  disabled={!input.trim() || loading}
                  className="p-2.5 rounded-xl bg-gradient-to-r from-blue-500 to-purple-500 text-white disabled:opacity-50 disabled:cursor-not-allowed hover:opacity-90 transition-all shadow-md shadow-blue-500/20"
                >
                  <Send size={18} />
                </button>
              </form>
            </div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
