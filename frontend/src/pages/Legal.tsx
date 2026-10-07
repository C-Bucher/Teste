import { useState, type ReactNode } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import axios from 'axios';
import api from '../api';
import { TERMS_VERSION } from '../legal';
import { useToast } from '../context/ToastContext';

const fmtVersion = TERMS_VERSION.split('-').reverse().join('/');

function LegalPage({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-on-surface px-4 py-10">
      <article className="max-w-3xl mx-auto space-y-md text-body-base leading-relaxed">
        <Link to="/" className="text-primary text-sm hover:underline">← Voltar</Link>
        <h1 className="font-display-lg text-display-lg">{title}</h1>
        <p className="text-sm text-outline">Versão de {fmtVersion}</p>
        <p className="p-md rounded-xl border border-warning/40 bg-warning/5 text-sm">
          Minuta para revisão jurídica. Este texto descreve como o sistema funciona hoje e ainda precisa ser validado por um advogado antes do lançamento comercial.
        </p>
        {children}
      </article>
    </div>
  );
}

const H = ({ children }: { children: ReactNode }) => <h2 className="font-headline-sm text-headline-sm pt-md">{children}</h2>;

export function Termos() {
  return (
    <LegalPage title="Termos de Uso">
      <H>1. O serviço</H>
      <p>O TechConnect é um software de gestão financeira e operacional oferecido por assinatura, nos planos descritos na página de planos. O Hub Empresarial atende empresas; o Hub Pessoal, pessoas físicas.</p>
      <H>2. Conta e acesso</H>
      <p>Você é responsável pelas credenciais da sua conta e pelos acessos que criar para sua equipe. Recomendamos ativar a verificação em duas etapas. O administrador da empresa define o que cada cargo pode acessar.</p>
      <H>3. Assinatura e pagamento</H>
      <p>A cobrança é recorrente, mensal ou anual, conforme o plano escolhido, e processada por um intermediador de pagamentos. Contas com pagamento em atraso há mais de 5 dias têm os módulos bloqueados até a regularização; os dados não são apagados por atraso.</p>
      <H>4. Conexões bancárias e inteligência artificial</H>
      <p>A conexão automática com bancos só acontece com sua autorização expressa, feita na tela do agregador de Open Finance, e pode ser removida a qualquer momento em Bancos. As análises de IA são sugestões baseadas nos seus dados e não substituem um contador ou consultor.</p>
      <H>5. Uso aceitável</H>
      <p>É proibido usar o serviço para atividades ilícitas, tentar acessar dados de outras contas ou sobrecarregar a infraestrutura.</p>
      <H>6. Cancelamento</H>
      <p>Você pode cancelar a assinatura e excluir a conta em Minha Conta. A exclusão apaga seus dados pessoais e, se você for a única pessoa da empresa, todos os dados da empresa.</p>
      <H>7. Privacidade</H>
      <p>O tratamento de dados pessoais segue a <Link to="/privacidade" className="text-primary hover:underline">Política de Privacidade</Link>.</p>
    </LegalPage>
  );
}

export function Privacidade() {
  return (
    <LegalPage title="Política de Privacidade">
      <H>1. Quais dados tratamos</H>
      <p>Dados de cadastro (nome, e-mail, empresa, CNPJ/CPF), dados que você registra (lançamentos, colaboradores, projetos, finanças pessoais), movimentações bancárias que você importar ou autorizar e registros de acesso (data, IP e ação), para segurança e auditoria.</p>
      <H>2. Para que usamos</H>
      <p>Para prestar o serviço contratado, cobrar a assinatura, proteger a conta e gerar as análises que você pedir. Não vendemos dados.</p>
      <H>3. Com quem compartilhamos (operadores)</H>
      <ul className="list-disc pl-6 space-y-xs">
        <li>Hospedagem e banco de dados (Supabase / provedor de nuvem).</li>
        <li>Google (Gemini): resumo agregado dos números da conta, quando você usa a IA.</li>
        <li>Pluggy: conexão com o banco, só quando você autoriza.</li>
        <li>Asaas: processamento dos pagamentos da assinatura. Os dados do cartão são digitados diretamente na página deles.</li>
        <li>Provedor de e-mail: envio de avisos e recuperação de senha.</li>
      </ul>
      <H>4. Seus direitos (LGPD, art. 18)</H>
      <p>Em Minha Conta você baixa uma cópia dos seus dados e pode excluir a conta a qualquer momento. Para correções ou dúvidas, fale com o encarregado pelo e-mail de contato do produto.</p>
      <H>5. Retenção</H>
      <p>Os dados ficam guardados enquanto a conta existir. Após a exclusão, são apagados da base ativa; os registros de auditoria da empresa seguem a política de retenção a ser definida na revisão jurídica.</p>
      <H>6. Segurança</H>
      <p>Senhas com hash bcrypt, segredos de verificação em duas etapas criptografados, conexões cifradas, isolamento de dados por empresa e por pessoa, e arquivos servidos apenas a quem tem acesso.</p>
    </LegalPage>
  );
}

/** Shown to anyone who has not accepted the current version yet (members created by an admin, older accounts). */
export function AceiteTermos() {
  const [checked, setChecked] = useState(false);
  const [busy, setBusy] = useState(false);
  const navigate = useNavigate();
  const toast = useToast();

  const accept = async () => {
    setBusy(true);
    try {
      const { data } = await api.post('/auth/accept-terms', { version: TERMS_VERSION });
      const user = JSON.parse(localStorage.getItem('user') || '{}');
      localStorage.setItem('user', JSON.stringify({ ...user, ...data }));
      navigate('/dashboard', { replace: true });
    } catch (err) {
      toast.error(axios.isAxiosError(err) ? err.response?.data?.detail || 'Erro ao registrar o aceite.' : 'Erro ao registrar o aceite.');
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center px-4">
      <div className="glass-card rounded-2xl p-lg max-w-md w-full space-y-md">
        <h1 className="font-headline-sm text-headline-sm text-on-surface">Antes de continuar</h1>
        <p className="text-body-sm text-on-surface-variant">
          Para usar o TechConnect, leia e aceite os <Link to="/termos" target="_blank" className="text-primary hover:underline">Termos de Uso</Link> e
          a <Link to="/privacidade" target="_blank" className="text-primary hover:underline">Política de Privacidade</Link> (versão de {fmtVersion}).
        </p>
        <label className="flex items-start gap-sm text-body-sm text-on-surface cursor-pointer">
          <input type="checkbox" checked={checked} onChange={(e) => setChecked(e.target.checked)} className="mt-1" />
          Li e aceito os Termos de Uso e a Política de Privacidade.
        </label>
        <button onClick={accept} disabled={!checked || busy}
          className="w-full py-3 rounded-xl bg-gradient-to-r from-primary to-secondary text-on-primary font-label-md disabled:opacity-50">
          Continuar
        </button>
      </div>
    </div>
  );
}
