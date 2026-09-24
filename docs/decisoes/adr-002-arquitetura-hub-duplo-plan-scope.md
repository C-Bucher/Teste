# ADR 002 — Arquitetura de Hub Duplo com Controle por Plan Scope e RBAC

## Status
Aprovado / Implementado

## Contexto
Muitos donos de micro e pequenas empresas misturam gastos pessoais com empresariais. Para resolver isso sem criar duas plataformas separadas — o que aumentaria a complexidade de autenticação e manutenção — era preciso ter um ambiente financeiro corporativo (ERP) e um módulo de finanças pessoais no mesmo sistema, com dados isolados e planos configuráveis.

## Decisão
Implementamos a arquitetura de Hub Duplo (Hub Empresarial e Hub Pessoal), governada por dois eixos:
1. Escopo do plano (`plan_scope`): `pessoal`, `empresarial` ou `completo`.
2. Papel de acesso (RBAC): `ADMIN`, `GERENTE` ou `FUNCIONARIO`.
3. Um alternador no cabeçalho: usuários com plano `completo` trocam entre o workspace da empresa e o módulo pessoal sem deslogar.

## Justificativa
- Elimina a fricção de múltiplos logins para quem gerencia o próprio negócio e a própria vida financeira ao mesmo tempo.
- As tabelas do Hub Pessoal (`personal_entries`, `personal_budgets`, `personal_goals` etc.) usam `owner_id` referenciando o usuário, enquanto as tabelas corporativas se vinculam a `company_id`.
- Permite comercializar planos diferentes conforme o perfil do cliente.

## Consequências
- Positivas: um modelo de negócio flexível e uma experiência de usuário fluida, sem precisar de duas contas.
- Atenção: as rotas de API precisam filtrar os dados pelo `owner_id` do token JWT para não vazar dados entre usuários — ver a atualização abaixo, porque essa filtragem ainda não foi implementada.

## Atualização (2026-09-21)
O eixo de papéis foi refinado com módulos liberados por cargo — ver [ADR 004](adr-004-permissoes-por-cargo-e-onboarding.md).

O isolamento do Hub Pessoal, no entanto, ainda não está feito: as tabelas têm `owner_id`, mas `personal.py` usa um proprietário fixo (`usr-001`) em vez do usuário do token, então hoje todo mundo vê os mesmos dados pessoais. Isso está registrado como MT-2 no [BACKLOG](../BACKLOG.md). Em outras palavras, o alerta de "Atenção" logo acima descrevia um risco que, na prática, se concretizou — não é uma garantia que o sistema já cumpre.
