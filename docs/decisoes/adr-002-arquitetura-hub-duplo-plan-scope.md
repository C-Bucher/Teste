# ADR 002 — Arquitetura de Hub Duplo com Controle por Plan Scope e RBAC

## Status
Aprovado / Implementado

## Contexto
Muitos donos de micro e pequenas empresas misturam gastos pessoais com empresariais. Para resolver essa dor sem criar duas plataformas separadas (o que aumentaria a complexidade de autenticação e manutenção), era necessário disponibilizar um ambiente financeiro corporativo (ERP) e um módulo de finanças pessoais no mesmo sistema, garantindo isolamento de dados e controle de planos.

## Decisão
Implementou-se a arquitetura de **Hub Duplo** (Hub Empresarial e Hub Pessoal), governada por dois eixos de controle:
1. **Escopo do Plano (`plan_scope`):** `pessoal`, `empresarial` ou `completo`.
2. **Papel de Acesso (RBAC):** `ADMIN`, `GERENTE` ou `FUNCIONARIO`.
3. **Alternador de Contexto no Header:** Usuários com plano `completo` podem chavear instantaneamente entre o workspace da empresa e o módulo pessoal sem deslogar.

## Justificativa
- **Experiência do Usuário (UX):** Elimina a fricção de múltiplos logins para o empreendedor que gerencia seu negócio e sua vida financeira simultaneamente.
- **Isolamento de Dados:** As tabelas do Hub Pessoal (`personal_entries`, `personal_budgets`, `personal_goals`, etc.) utilizam `owner_id` referenciando o usuário, enquanto as tabelas corporativas vinculam-se a `company_id`.
- **Monetização e Escalabilidade:** Permite comercializar planos distintos conforme o perfil do cliente final.

## Consequências
- **Positivas:** Modelo de negócio flexível, experiência de usuário fluida e segregação lógica estrita entre dados PJ e PF.
- **Atenção:** Necessidade de garantir que rotas de API filtrem estritamente os dados pelo `owner_id` do token JWT para evitar vazamento entre usuários.

## Atualização (2026-09-21)
- O eixo de papéis passou a ser refinado por **módulos liberados por cargo** — ver [ADR 004](adr-004-permissoes-por-cargo-e-onboarding.md).
- **Isolamento do Hub Pessoal ainda não cumprido:** as tabelas têm `owner_id`, mas `personal.py` usa um proprietário fixo (`usr-001`) em vez do usuário do token; hoje todos os usuários veem os mesmos dados pessoais. Pendência registrada como **MT-2** no [BACKLOG](../BACKLOG.md). O aviso de "Atenção" acima é, portanto, uma pendência aberta, não uma garantia já entregue.
