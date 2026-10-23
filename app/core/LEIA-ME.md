# Nota da pasta app/core

**Função:** Regras usadas por várias rotas: segurança (tokens, senhas, permissões), assinatura/cobrança, plano e limites, e-mail e notificações, alertas diários, auditoria e armazenamento de arquivos.

## O que tem aqui

- `__init__.py`: Arquivo vazio. Faz o Python tratar a pasta app/core como pacote.
- `alerts.py`: Alertas diários: contas a pagar que vencem em breve, recebíveis atrasados e prazos do Kanban. Cada alerta é criado no máximo uma vez por empresa por dia.
- `audit.py`: Registra a trilha de auditoria (quem fez qual ação, em qual dado e de qual IP). O registro é salvo junto com a própria mudança.
- `billing.py`: Regras de acesso por assinatura: define quem pode usar o produto (teste de 7 dias, ativo, em atraso com 5 dias de tolerância, cancelado). Bloqueia com erro 402 quando não há acesso.
- `config.py`: Configurações lidas do ambiente: ambiente (dev/produção), SECRET_KEY, validade dos tokens (60 min e 7 dias) e endereços CORS permitidos.
- `crypto.py`: Criptografia de segredos guardados no banco (ex.: o código do 2FA), com a chave ENCRYPTION_KEY.
- `ctc.py`: Calcula o CTC (custo total do colaborador) e o custo por hora a partir do salário, do tipo de contrato e dos multiplicadores da empresa.
- `legal.py`: Guarda a versão dos termos de uso e da política de privacidade. Ao mudar o texto, muda a versão e todos precisam aceitar de novo.
- `mailer.py`: Envia e-mails por SMTP. Sem SMTP configurado, só registra no log e na lista OUTBOX (usada em desenvolvimento e testes).
- `notify.py`: Cria a notificação dentro do sistema e envia e-mail aos administradores que mantêm o aviso por e-mail ligado.
- `passwords.py`: Regras e criptografia de senha: mínimo de 8 caracteres com letras e números, hash bcrypt e verificação.
- `permissions.py`: Controle de acesso por cargo e plano: define os módulos padrão de Gerente e Funcionário e bloqueia a rota quando o usuário não tem o módulo.
- `plans.py`: Descobre o plano atual da empresa e calcula o quanto dos limites já foi usado (ex.: conexões bancárias).
- `rate_limit.py`: Limite de tentativas por IP (20 por minuto) nas rotas de login, cadastro, recuperação de senha e renovação.
- `readiness.py`: Relatório do que está configurado e do que falta para produção (IA, pagamentos, e-mail, bancos, armazenamento etc.). Alimenta a aba Conexões em Configurações e o aviso de inicialização.
- `security.py`: Tokens de login (JWT): cria e valida os tokens de acesso, renovação e do passo do 2FA. Descobre o usuário logado em cada requisição. Trocar a senha invalida os tokens antigos.
- `storage.py`: Armazenamento privado de comprovantes e relatórios: em disco local ou em serviço compatível com S3. Os arquivos nunca são públicos; só saem por rotas que conferem o dono.
