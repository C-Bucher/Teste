# NOTA: Respostas por regras, usadas quando a IA está indisponível ou a cota do plano acabou. Todo número vem dos dados reais.

"""Rule-based answers used when the model is unavailable or the plan's quota is spent.
Every number comes from the real snapshot; nothing here is invented."""

import re
import unicodedata


def brl(v: float) -> str:
    s = f"{abs(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"-R$ {s}" if v < 0 else f"R$ {s}"


def _plain(text: str) -> str:
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()


def business_chat(snapshot: dict, message: str) -> str:
    q = _plain(message)
    nxt, ven, d90 = snapshot["proximos_30_dias"], snapshot["vencidos"], snapshot["ultimos_90_dias"]
    if any(w in q for w in ("caixa", "fluxo", "pagar", "receber", "vencid")):
        saldo = nxt["a_receber"] - nxt["a_pagar"]
        txt = (f"Próximos 30 dias: {brl(nxt['a_receber'])} a receber e {brl(nxt['a_pagar'])} a pagar, "
               f"saldo previsto de {brl(saldo)}.")
        if ven["quantidade"]:
            txt += f" Há {ven['quantidade']} lançamento(s) vencido(s): {brl(ven['a_pagar'])} a pagar e {brl(ven['a_receber'])} a receber."
        if nxt["maiores_a_pagar"]:
            top = nxt["maiores_a_pagar"][0]
            txt += f" Maior conta a pagar: {top['descricao']} ({brl(top['valor'])}, vence {top['vencimento']})."
        return txt
    if any(w in q for w in ("dre", "resultado", "lucro", "margem", "receita", "despesa")):
        rec, desp = d90["receitas_recebidas"], d90["despesas_pagas"]
        margem = f" Margem de {((rec - desp) / rec) * 100:.1f}%." if rec else ""
        cats = snapshot["despesas_por_categoria_90_dias"]
        top = f" Maior grupo de despesa: {cats[0]['categoria']} ({brl(cats[0]['total'])})." if cats else ""
        return f"Últimos 90 dias: receitas de {brl(rec)} e despesas de {brl(desp)}, resultado de {brl(rec - desp)}.{margem}{top}"
    if any(w in q for w in ("ctc", "equipe", "colaborador", "folha", "custo hora", "custo-hora")):
        eq = snapshot["equipe"]
        return (f"A equipe tem {eq['colaboradores_ativos']} colaborador(es) ativo(s), custo mensal total de "
                f"{brl(eq['custo_mensal_total'])} e custo-hora médio de {brl(eq['custo_hora_medio'])}.")
    if any(w in q for w in ("banco", "concilia", "extrato")):
        n = snapshot["movimentacoes_bancarias_sem_conciliacao"]
        return f"Há {n} movimentação(ões) bancária(s) aguardando conciliação em Bancos." if n else "Todas as movimentações bancárias importadas estão conciliadas."
    return ("Posso analisar fluxo de caixa e contas a vencer, resultado (DRE), custo da equipe (CTC) e conciliação bancária. "
            "Pergunte, por exemplo: \"como está meu caixa nos próximos 30 dias?\"")


def business_insights(snapshot: dict) -> list[dict]:
    out = []
    ven, nxt, d90 = snapshot["vencidos"], snapshot["proximos_30_dias"], snapshot["ultimos_90_dias"]
    if ven["a_pagar"] > 0:
        out.append({"type": "ALERTA", "title": "Contas vencidas", "description": f"{brl(ven['a_pagar'])} em despesas já venceram sem baixa. Confira se foram pagas ou renegocie.", "impact": "Alto", "urgency": "Alta"})
    if ven["a_receber"] > 0:
        out.append({"type": "ALERTA", "title": "Recebimentos atrasados", "description": f"{brl(ven['a_receber'])} a receber estão vencidos. Vale cobrar os clientes.", "impact": "Alto", "urgency": "Alta"})
    if nxt["a_pagar"] > nxt["a_receber"]:
        out.append({"type": "ALERTA", "title": "Caixa dos próximos 30 dias", "description": f"As saídas previstas ({brl(nxt['a_pagar'])}) superam as entradas ({brl(nxt['a_receber'])}) em {brl(nxt['a_pagar'] - nxt['a_receber'])}. Reserve capital ou antecipe recebimentos.", "impact": "Alto", "urgency": "Media"})
    cats = snapshot["despesas_por_categoria_90_dias"]
    if cats and cats[0]["participacao"] >= 0.3:
        out.append({"type": "OPORTUNIDADE", "title": f"Revisar gastos com {cats[0]['categoria']}", "description": f"Essa categoria concentra {cats[0]['participacao'] * 100:.0f}% das despesas dos últimos 90 dias ({brl(cats[0]['total'])}). Uma renegociação aqui tem o maior efeito.", "impact": "Medio", "urgency": "Media"})
    if snapshot["movimentacoes_bancarias_sem_conciliacao"]:
        out.append({"type": "ALERTA", "title": "Extrato sem conciliação", "description": f"{snapshot['movimentacoes_bancarias_sem_conciliacao']} movimentação(ões) bancária(s) ainda não foram conciliadas.", "impact": "Medio", "urgency": "Media"})
    rec, desp = d90["receitas_recebidas"], d90["despesas_pagas"]
    if rec > 0 and rec > desp:
        out.append({"type": "OPORTUNIDADE", "title": "Resultado positivo", "description": f"Margem de {((rec - desp) / rec) * 100:.1f}% nos últimos 90 dias. Considere separar parte do resultado para reserva.", "impact": "Medio", "urgency": "Baixa"})
    if not out:
        out.append({"type": "OPORTUNIDADE", "title": "Comece pelos lançamentos", "description": "Registre contas a pagar e a receber (ou importe o extrato em Bancos) para receber análises do seu caixa.", "impact": "Medio", "urgency": "Baixa"})
    return out


def personal_insights(snapshot: dict) -> list[dict]:
    out = []
    for b in snapshot["orcamentos"]:
        if b["uso"] is not None and b["uso"] >= 0.9:
            out.append({"type": "ALERT", "message": f"Seus gastos com {b['categoria']} estão em {b['uso'] * 100:.0f}% do orçamento do mês ({brl(b['gasto_no_mes'])} de {brl(b['limite'])}).", "impact_value": round(max(b["gasto_no_mes"] - b["limite"], 0), 2)})
    subs = snapshot["assinaturas_ativas"]
    if subs["quantidade"]:
        out.append({"type": "CUT", "message": f"Você tem {subs['quantidade']} assinatura(s) ativa(s) somando {brl(subs['total_mensal'])}/mês ({', '.join(subs['nomes'][:4])}). Cancele as que não usa.", "impact_value": subs["total_mensal"]})
    reserve = snapshot["despesa_media_mensal_3_meses"] * 3
    if reserve and snapshot["saldo_em_contas"] > reserve:
        excess = round(snapshot["saldo_em_contas"] - reserve, 2)
        out.append({"type": "OPPORTUNITY", "message": f"Há {brl(excess)} em conta além de uma reserva de 3 meses de despesas. Esse valor pode render mais aplicado.", "impact_value": excess})
    if snapshot["dividas_restantes"]:
        out.append({"type": "ALERT", "message": f"Suas dívidas somam {brl(snapshot['dividas_restantes'])}. Priorize quitar as de juros mais altos.", "impact_value": snapshot["dividas_restantes"]})
    if not out:
        out.append({"type": "OPPORTUNITY", "message": "Cadastre orçamentos, assinaturas e contas (ou importe o extrato em Bancos) para receber análises personalizadas.", "impact_value": 0})
    return out


_KEYWORDS = [
    (r"\buber\b|\b99\b|taxi|combust|posto|shell|ipiranga|estacion", "Transporte"),
    (r"ifood|rappi|restaurante|padaria|mercado|supermerc|aliment", "Alimentação"),
    (r"\baws\b|amazon web|google cloud|azure|heroku|vercel|digitalocean|hosting|servidor", "Infraestrutura"),
    (r"energia|enel|light|cemig|copel|celesc|eletro", "Energia"),
    (r"telefon|vivo|claro|\btim\b|\boi\b|internet|fibra", "Telecomunicações"),
    (r"aluguel|condominio|imobili", "Aluguel"),
    (r"tarifa|iof|juros|anuidade|cesta", "Tarifas bancárias"),
    (r"spotify|netflix|youtube|prime video|disney|hbo|adobe|microsoft|google workspace|notion|slack", "Assinaturas e software"),
    (r"salario|folha|pro.?labore|inss|fgts", "Pessoal"),
    (r"simples nacional|\bdas\b|darf|iss\b|icms|imposto", "Impostos"),
]


def suggest_category(description: str, known: list[str]) -> tuple[str | None, float]:
    """Keyword guess, preferring a category name the company already uses."""
    text = _plain(description)
    for pattern, category in _KEYWORDS:
        if re.search(pattern, text):
            match = next((k for k in known if _plain(k) == _plain(category)), category)
            return match, 0.6
    for k in known:
        if _plain(k) and _plain(k) in text:
            return k, 0.5
    return None, 0.0
