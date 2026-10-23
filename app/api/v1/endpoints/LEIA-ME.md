# Nota da pasta app/api/v1/endpoints

**Função:** As rotas da API, um arquivo por assunto (login, financeiro, kanban, bancos, pagamentos etc.). Cada rota valida o usuário, usa as regras de core e lê/grava no banco por db.

## O que tem aqui

- `__init__.py`: Arquivo vazio. Faz o Python tratar a pasta endpoints como pacote.
- `account.py`: Rotas /account: o próprio usuário exporta seus dados (direito da LGPD) e exclui a própria conta.
- `ai.py`: Rotas /ai: CFO Virtual (chat e histórico), conciliação por IA e gerador de orçamento. Usa o Gemini sobre os dados reais da empresa; sem Gemini, responde por regras (app/integrations/ai).
- `audit.py`: Rota /audit: lista a trilha de auditoria (quem fez o quê e quando). Só o administrador acessa.
- `auth.py`: Rotas /auth: cadastro, login (com 2FA), renovação e logout, dados do usuário logado, troca e recuperação de senha, gestão de usuários da empresa, ativar/desativar 2FA e aceite dos termos.
- `bank.py`: Rotas /bank: contas bancárias, importação de extrato (OFX/CSV), lista de transações, conciliação com lançamentos, regras de categoria, conexão com o agregador (Pluggy) e uso do plano.
- `bank_hooks.py`: Rotas de máquina para máquina: webhook do Pluggy e /sync-all (sincroniza todas as contas, chamado pelo agendador).
- `clients.py`: Rotas /clients: cadastro de clientes da empresa (listar, criar, editar, excluir).
- `company.py`: Rotas /company: dados da empresa, conclusão do onboarding, centros de custo, categorias (plano de contas), calendário de trabalho, parâmetros do CTC e logo.
- `employees.py`: Rotas /employees: colaboradores (listar, criar, editar, excluir, desligar) e histórico de salário. Calcula o CTC e o custo por hora de cada um.
- `exports.py`: Rotas /exports: gera relatórios em CSV, JSON, XLSX ou PDF com os dados reais, lista o histórico e baixa o arquivo.
- `financial.py`: Rotas /financial: lançamentos (criar, editar, baixar/pagar), comprovante anexo, DRE, fluxo de caixa e resumo mensal, incluindo as versões usadas pelo Dashboard.
- `jobs.py`: Rota /jobs/daily: tarefa diária chamada por um agendador externo (exige o cabeçalho X-Cron-Secret). Gera os alertas e sincroniza os bancos.
- `kanban.py`: Rotas /kanban: projetos, colunas, cartões (criar, mover, editar, excluir), cronômetro de tempo por cartão, comentários, modelos de projeto e clientes.
- `notifications.py`: Rotas /notifications: lista, marca como lida, arquiva, contador de não lidas e preferências de e-mail.
- `payments.py`: Rotas /payments: abre o checkout no Asaas, recebe o webhook de confirmação, consulta assinatura, acesso, faturas e uso, e cancela a assinatura.
- `permissions.py`: Rotas /permissions: matriz de permissões por cargo (ler e salvar) e os módulos liberados para o usuário atual.
- `personal.py`: Rotas /personal (Hub Pessoal): lançamentos, contas, orçamentos, metas, dívidas, assinaturas, divisão de despesas, timeboxes, OKRs, análise e insights de IA. Tudo pertence só ao usuário dono.
- `plans.py`: Rotas /plans: lista os planos e preços (somente leitura).
- `search.py`: Rota /search: busca global (campo de busca do topo) em colaboradores, clientes, projetos, lançamentos e fornecedores da empresa.
- `suppliers.py`: Rotas /suppliers: cadastro de fornecedores (listar, criar, ver, editar, excluir).
- `system.py`: Rotas /system: status das integrações (usado em Configurações) e a versão vigente dos termos de uso.
