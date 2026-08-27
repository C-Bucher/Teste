# POP - CFO Virtual Inteligente (Gemini IA)

## 1. Objetivo
Analisar mensalmente (ou sob demanda) o DRE (Demonstrativo do Resultado do Exercício) e o histórico de `Cost-per-Task` da empresa para gerar insights acionáveis para o dono.

## 2. Entradas
- Período da Análise (Ex: "Março 2026").
- JSON com DRE consolidado do período (Receitas, Despesas por Centro de Custo, Lucro Bruto e Líquido).
- JSON com top 10 projetos/tarefas que tiveram maior `Cost-per-Task` no Kanban versus o Orçamento.

## 3. Lógica Determinística (Regras de Negócio)
1. O backend coleta os dados do repositório MySQL e sanitiza o payload, removendo nomes de colaboradores e usando apenas "Colaborador A", "Colaborador B" (Compliance LGPD).
2. Constrói um Prompt injetando as variáveis no template do CFO.
3. Chama a API do Gemini 2.5 Flash via REST.
4. Faz o parse da resposta em JSON utilizando a estrutura `CFOInsightResponse`.
5. Se a API falhar (timeout ou limite), retorna erro gracefully (fallback silencioso no log) sem quebrar o ERP.

## 4. Prompt Base (Template)
"Você é o CFO Virtual de uma PME. Analise o seguinte DRE: {dre_json}. Analise as tarefas de maior custo real: {cpt_json}. Gere 3 insights acionáveis no formato JSON seguindo a estrutura fornecida."

## 5. Saída
Objeto JSON estrito validado pelo schema Pydantic.
