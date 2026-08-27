# ADR 003 — Design System Obsidian Flow e Stack Frontend (React 19 + Tailwind CSS v4)

## Status
Aprovado / Implementado

## Contexto
Painéis de gestão financeira e operacional tradicionais frequentemente sofrem de sobrecarga visual, interfaces truncadas e baixa usabilidade. A proposta do TechConnect 2.0 exigia uma interface de alta produtividade para visualização contínua de gráficos, quadro Kanban e dados contábeis em ambientes com baixa fadiga visual.

## Decisão
Adotou-se o design system proprietário **Obsidian Flow**, implementado sobre:
1. **React 19 + TypeScript + Vite** para renderização reativa e componentes concorrentes.
2. **Tailwind CSS v4** com motor nativo `@theme` e paleta Dark Mode com glassmorphism.
3. **Framer Motion** para animações suaves de gavetas (*Drawers*), modais e transições de cards no Kanban.
4. **Recharts e Lucide React** para gráficos financeiros e iconografia consistente.

## Justificativa
- **Performance de Renderização:** O Vite e o React 19 proporcionam recarregamento instantâneo (*Hot Module Replacement*) e menor tempo de inicialização do bundle.
- **Ergonomia Visual:** O tema escuro com contraste calibrado e efeitos de vidro translúcido melhora a leitura de relatórios densos (DRE, tabelas de funcionários, extratos).
- **Interatividade:** O Drag & Drop nativo com Framer Motion torna o manuseio do quadro Kanban dinâmico e responsivo.

## Consequências
- **Positivas:** Interface moderna, responsiva, com forte apelo visual executivo e fluidez operacional.
- **Cuidados:** Configuração cuidadosa dos tokens de espaçamento e larguras máximas do Tailwind v4 para evitar sobreposição em telas menores.
