# Sprint 03 — Produto comercial: segurança, cobrança, bancos e IA real

## 1. Identificação da sprint
Período de 23/09/2026 a 07/10/2026. Status: concluída (mergeada na `main` via pull request #3, em 08/10/2026).

## 2. Objetivo da sprint
Levar o TechConnect de protótipo acadêmico a produto que pode cobrar clientes. A sprint teve quatro frentes:
- dados isolados e testados;
- autenticação no padrão de mercado;
- cobrança recorrente real;
- importação e conciliação bancária com o mínimo de trabalho manual.

Também fez parte do objetivo trocar a IA de respostas fixas por análises sobre os dados de cada cliente.

## 3. Entregas e funcionalidades desenvolvidas

### 3.1 Isolamento e persistência (23/09, Abner Trindade)
Dados empresariais com `company_id`, Hub Pessoal por `owner_id`, gates por módulo e plano, assinaturas, faturas, timers, calendário e preferências persistidos, e suporte a Supabase/PostgreSQL (ADR 005 e ADR 006).

### 3.2 Endurecimento (etapa 1, 30/09)
- Suíte `pytest`, com testes que atacam cada recurso a partir de outra empresa e de outro usuário.
- Migrações versionadas com Alembic.
- Política de senha e bloqueio por tentativas.
- Tokens de acesso e de renovação separados.
- Trilha de auditoria.
- Docker Compose com o próprio MySQL (ADR 007).

### 3.3 Planos e abas completas (etapa 2, 30/09)
- 4 planos com os preços aprovados.
- Comprovantes privados nos lançamentos.
- Exportações privadas.
- CTC configurável.
- Exclusão de tarefa no Kanban.
- Minha Conta com direitos LGPD.
- Gestão completa de acessos.
- Patrimônio pessoal calculado com dados reais.

### 3.4 Bancos e conciliação (etapa 3, 30/09)
- Importação OFX/CSV sem duplicar.
- Conciliação automática e manual.
- Regras de categoria.
- Pluggy atrás de interface.
- Limites de conexão por plano (ADR 008).

### 3.5 IA real (etapa 4, 30/09)
Gemini sobre um resumo dos dados reais, com fallback por regras, histórico do chat e cota mensal por plano (ADR 009).

### 3.6 Preparação para o lançamento (etapa 5, 07/10)
- Cobrança recorrente com Asaas, sem dados de cartão no servidor:
  - teste de 7 dias;
  - webhook;
  - bloqueio com tolerância;
  - cancelamento (ADR 010).
- Recuperação de senha por e-mail, verificação em duas etapas, limite por IP e consentimento versionado (ADR 011).
- Armazenamento S3 compatível.
- Exportação XLSX e PDF.
- Webhook da Pluggy e job diário (alertas de vencimento e sincronização bancária).
- E-mails de notificação.
- Datas da demonstração atualizáveis.
- Contraste WCAG AA.
- Lint sem erros, testes de frontend e CI.
- Painel de integrações completo.

## 4. Limitações registradas nesta sprint
- SEC-5: credenciais expostas em `913f78d` continuam válidas. A chave do Gemini já foi bloqueada pelo Google como vazada.
- Asaas e Pluggy estão implementados e testados com provedores simulados, mas ainda não foram validados nos sandboxes reais, por falta de credenciais.
- Termos de uso e política de privacidade são minuta para revisão jurídica.
- O limite por IP vale por instância, e os uploads não passam por antivírus.

## 5. Evidências de conclusão
- 139 testes de backend, verdes em SQLite, PostgreSQL e MySQL e também em Python 3.11.
- 14 testes de frontend, ESLint sem erros e build do frontend.
- Teste de contrato garantindo que todas as chamadas do frontend têm rota no backend.
- Execução de ponta a ponta da aplicação real com banco novo: migrações, seed, login demo, importação de OFX e conciliação automática.
- Especificações em [docs/planejamento/specs](../docs/planejamento/specs) e decisões nas ADRs 007 a 011.
