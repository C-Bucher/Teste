# ADR 003 — Design System Obsidian Flow e Stack Frontend (React 19 + Tailwind CSS v4)

## Status
Aprovado / Implementado

## Contexto
Painéis de gestão financeira tradicionais costumam sofrer de sobrecarga visual e baixa usabilidade. O TechConnect 2.0 precisava de uma interface confortável para olhar gráficos, o quadro Kanban e dados contábeis por longos períodos, sem cansar a vista.

## Decisão
Adotamos um design system próprio, o Obsidian Flow, construído sobre:
1. React 19, TypeScript e Vite, para renderização reativa e componentes concorrentes.
2. Tailwind CSS v4, com o motor nativo `@theme` e uma paleta dark mode com glassmorphism.
3. Framer Motion, para animações de gavetas (*drawers*), modais e transições de elementos.
4. Recharts e Lucide React, para os gráficos financeiros e os ícones.

## Justificativa
- Vite e React 19 dão um Hot Module Replacement praticamente instantâneo e um bundle mais leve para carregar.
- O tema escuro, com contraste calibrado e efeito de vidro translúcido, ajuda na leitura de telas densas como o DRE, a tabela de funcionários e os extratos.
- O quadro Kanban usa a API nativa de drag and drop do HTML5 (`draggable`, `onDragStart`, `onDrop`); o Framer Motion cuida das animações ao redor — abrir/fechar modais e gavetas, entrada e saída de elementos —, não do arrasto dos cards em si.

## Consequências
- Positivas: interface moderna e responsiva, com boa legibilidade nas telas de dados densos.
- Cuidados: os tokens de espaçamento e as larguras máximas do Tailwind v4 precisam de atenção para não sobrepor elementos em telas menores.
