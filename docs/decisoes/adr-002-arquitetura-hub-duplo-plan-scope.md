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
