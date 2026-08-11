# POP - Gerador de Orçamentos Preditivo (Gemini IA)

## 1. Objetivo
Criar propostas financeiras extremamente precisas para novos projetos/clientes usando o histórico de Custo por Tarefa (Cost-per-Task) da empresa.

## 2. Entradas
- Briefing/Necessidades do Cliente (Texto Livre).
- Histórico médio de `costPerHourSnapshot` por cargo/perfil dentro da empresa.
- Taxa de Markup/Margem de Lucro desejada.

## 3. Lógica Determinística (Regras de Negócio)
1. O Backend extrai a média de custo/hora dos cargos ativos (ex: Designer Sênior = R$45/h, Dev = R$80/h).
2. Envia as médias e o briefing para o Gemini.
3. O Gemini quebra o briefing em subtarefas (WBS - Work Breakdown Structure), estima as horas por papel, e multiplica pela média de custo/hora.
4. O Gemini aplica o Markup e devolve a precificação sugerida.
5. O Backend repassa a proposta para o Frontend onde o gerente pode editar antes de aprovar.

## 4. Prompt Base (Template)
"Atue como um gerente de projetos de PME. Baseado no briefing {briefing} e no custo/hora dos papéis {custos_hora_json}, decomponha o projeto em tarefas, estime as horas e gere um orçamento com margem de {markup}%. Retorne um JSON estrito."

## 5. Saída
JSON estruturado validado pelo schema `ProposalResponse`.
