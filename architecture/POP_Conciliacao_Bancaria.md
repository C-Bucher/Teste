# POP - Auto-Conciliação Bancária (Gemini IA)

## 1. Objetivo
Automatizar a categorização de linhas de um extrato bancário (OFX/CSV), associando-as ao Fornecedor e Centro de Custo corretos para poupar tempo na conciliação.

## 2. Entradas
- Array JSON com a listagem crua do banco contendo: Data, Descrição (texto confuso do banco), Valor (Positivo/Negativo).
- Listagem dos ID/Nomes dos Fornecedores e Centros de Custo ativos na empresa.

## 3. Lógica Determinística (Regras de Negócio)
1. O usuário faz o upload do arquivo no Frontend (React).
2. O Backend (FastAPI) converte as linhas do CSV para JSON (limite máximo de 100 linhas por requisição para evitar timeout).
3. O Backend envia os dados ao Gemini com o contexto das "Categorias Possíveis".
4. O Gemini devolve um array indicando as combinações de maior probabilidade.
5. O Backend enriquece os dados recebidos com os IDs reais do banco de dados e repassa ao Frontend para revisão humana.
6. Apenas após a aprovação do usuário a conciliação persiste os dados no módulo M2 (Financeiro).

## 4. Prompt Base (Template)
"Analise as seguintes transações bancárias cruas: {transacoes_json}. Mapeie cada uma delas para uma das seguintes categorias: {categorias_json} e sugira o fornecedor. Retorne APENAS um JSON array."

## 5. Saída
JSON estruturado validado pelo schema `ConciliationResponse`.
