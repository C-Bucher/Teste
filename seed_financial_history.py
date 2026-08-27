"""
Script de migração: insere lançamentos financeiros históricos
dos últimos 5 meses no banco de dados existente.

Execução: python seed_financial_history.py
"""
import asyncio
from datetime import date, timedelta
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import async_session_maker
from app.db.models import FinancialEntryModel
from sqlalchemy import select

hoje = date.today()

def dias(n: int) -> str:
    return (hoje + timedelta(days=n)).isoformat()

HISTORICO = [
    # M-1 (mês passado ~30-45 dias atrás)
    dict(id="fin-h01", type="RECEITA",  amount=31200.00, description="Projeto API Gateway - Entrega",     due_date=dias(-38), payment_date=dias(-38), status="PAGO",     category="Desenvolvimento", supplier_id=None,      cost_center="Tecnologia"),
    dict(id="fin-h02", type="RECEITA",  amount=12500.00, description="Consultoria ERP - Mes Passado",     due_date=dias(-32), payment_date=dias(-32), status="PAGO",     category="Consultoria",    supplier_id=None,      cost_center="Comercial"),
    dict(id="fin-h03", type="RECEITA",  amount=8400.00,  description="Suporte Premium - Cliente B",       due_date=dias(-45), payment_date=dias(-45), status="PAGO",     category="Suporte",        supplier_id=None,      cost_center="Tecnologia"),
    dict(id="fin-h04", type="DESPESA",  amount=4100.00,  description="AWS - Mes Passado",                 due_date=dias(-35), payment_date=dias(-35), status="PAGO",     category="Infraestrutura", supplier_id="sup-001", cost_center="Tecnologia"),
    dict(id="fin-h05", type="DESPESA",  amount=8500.00,  description="Folha de Pagamento - Mes Passado",  due_date=dias(-40), payment_date=dias(-40), status="PAGO",     category="Pessoal",        supplier_id="sup-002", cost_center="Administrativo"),
    dict(id="fin-h06", type="DESPESA",  amount=3500.00,  description="Aluguel Escritorio - Mes Passado",  due_date=dias(-30), payment_date=dias(-30), status="PAGO",     category="Aluguel",        supplier_id="sup-005", cost_center="Administrativo"),
    # M-2
    dict(id="fin-h07", type="RECEITA",  amount=25800.00, description="Desenvolvimento Mobile App - M-2",  due_date=dias(-68), payment_date=dias(-68), status="PAGO",     category="Desenvolvimento", supplier_id=None,      cost_center="Tecnologia"),
    dict(id="fin-h08", type="RECEITA",  amount=18000.00, description="Contrato SaaS - M-2",               due_date=dias(-62), payment_date=dias(-62), status="PAGO",     category="SaaS",           supplier_id=None,      cost_center="Comercial"),
    dict(id="fin-h09", type="DESPESA",  amount=4050.00,  description="AWS - M-2",                         due_date=dias(-65), payment_date=dias(-65), status="PAGO",     category="Infraestrutura", supplier_id="sup-001", cost_center="Tecnologia"),
    dict(id="fin-h10", type="DESPESA",  amount=8500.00,  description="Folha de Pagamento - M-2",          due_date=dias(-70), payment_date=dias(-70), status="PAGO",     category="Pessoal",        supplier_id="sup-002", cost_center="Administrativo"),
    dict(id="fin-h11", type="DESPESA",  amount=3500.00,  description="Aluguel Escritorio - M-2",          due_date=dias(-60), payment_date=dias(-60), status="PAGO",     category="Aluguel",        supplier_id="sup-005", cost_center="Administrativo"),
    dict(id="fin-h12", type="DESPESA",  amount=2800.00,  description="Contabilidade - M-2",               due_date=dias(-63), payment_date=dias(-63), status="PAGO",     category="Contabilidade",  supplier_id="sup-004", cost_center="Administrativo"),
    # M-3
    dict(id="fin-h13", type="RECEITA",  amount=19500.00, description="Consultoria Digital - M-3",         due_date=dias(-98), payment_date=dias(-98), status="PAGO",     category="Consultoria",    supplier_id=None,      cost_center="Comercial"),
    dict(id="fin-h14", type="RECEITA",  amount=14200.00, description="Manutencao ERP - M-3",              due_date=dias(-92), payment_date=dias(-92), status="PAGO",     category="Suporte",        supplier_id=None,      cost_center="Tecnologia"),
    dict(id="fin-h15", type="RECEITA",  amount=35000.00, description="Projeto Rastreamento Mobile - M-3", due_date=dias(-95), payment_date=dias(-95), status="PAGO",     category="Desenvolvimento", supplier_id=None,      cost_center="Tecnologia"),
    dict(id="fin-h16", type="DESPESA",  amount=4300.00,  description="AWS - M-3",                         due_date=dias(-93), payment_date=dias(-93), status="PAGO",     category="Infraestrutura", supplier_id="sup-001", cost_center="Tecnologia"),
    dict(id="fin-h17", type="DESPESA",  amount=8500.00,  description="Folha de Pagamento - M-3",          due_date=dias(-100), payment_date=dias(-100), status="PAGO",   category="Pessoal",        supplier_id="sup-002", cost_center="Administrativo"),
    dict(id="fin-h18", type="DESPESA",  amount=3500.00,  description="Aluguel Escritorio - M-3",          due_date=dias(-90), payment_date=dias(-90), status="PAGO",     category="Aluguel",        supplier_id="sup-005", cost_center="Administrativo"),
    # M-4
    dict(id="fin-h19", type="RECEITA",  amount=22000.00, description="Desenvolvimento Backend - M-4",     due_date=dias(-128), payment_date=dias(-128), status="PAGO",   category="Desenvolvimento", supplier_id=None,      cost_center="Tecnologia"),
    dict(id="fin-h20", type="RECEITA",  amount=9500.00,  description="Suporte Premium - M-4",             due_date=dias(-122), payment_date=dias(-122), status="PAGO",   category="Suporte",        supplier_id=None,      cost_center="Tecnologia"),
    dict(id="fin-h21", type="DESPESA",  amount=4100.00,  description="AWS - M-4",                         due_date=dias(-125), payment_date=dias(-125), status="PAGO",   category="Infraestrutura", supplier_id="sup-001", cost_center="Tecnologia"),
    dict(id="fin-h22", type="DESPESA",  amount=8500.00,  description="Folha de Pagamento - M-4",          due_date=dias(-130), payment_date=dias(-130), status="PAGO",   category="Pessoal",        supplier_id="sup-002", cost_center="Administrativo"),
    dict(id="fin-h23", type="DESPESA",  amount=3500.00,  description="Aluguel Escritorio - M-4",          due_date=dias(-120), payment_date=dias(-120), status="PAGO",   category="Aluguel",        supplier_id="sup-005", cost_center="Administrativo"),
    dict(id="fin-h24", type="DESPESA",  amount=650.00,   description="GitHub Enterprise - M-4",           due_date=dias(-123), payment_date=dias(-123), status="PAGO",   category="Ferramentas",    supplier_id="sup-003", cost_center="Tecnologia"),
    # M-5
    dict(id="fin-h25", type="RECEITA",  amount=17800.00, description="Consultoria Financeira - M-5",      due_date=dias(-158), payment_date=dias(-158), status="PAGO",   category="Consultoria",    supplier_id=None,      cost_center="Comercial"),
    dict(id="fin-h26", type="RECEITA",  amount=28000.00, description="Projeto E-commerce - Entrega M-5",  due_date=dias(-152), payment_date=dias(-152), status="PAGO",   category="Desenvolvimento", supplier_id=None,      cost_center="Tecnologia"),
    dict(id="fin-h27", type="DESPESA",  amount=3900.00,  description="AWS - M-5",                         due_date=dias(-155), payment_date=dias(-155), status="PAGO",   category="Infraestrutura", supplier_id="sup-001", cost_center="Tecnologia"),
    dict(id="fin-h28", type="DESPESA",  amount=8500.00,  description="Folha de Pagamento - M-5",          due_date=dias(-160), payment_date=dias(-160), status="PAGO",   category="Pessoal",        supplier_id="sup-002", cost_center="Administrativo"),
    dict(id="fin-h29", type="DESPESA",  amount=3500.00,  description="Aluguel Escritorio - M-5",          due_date=dias(-150), payment_date=dias(-150), status="PAGO",   category="Aluguel",        supplier_id="sup-005", cost_center="Administrativo"),
    dict(id="fin-h30", type="DESPESA",  amount=2800.00,  description="Contabilidade - M-5",               due_date=dias(-153), payment_date=dias(-153), status="PAGO",   category="Contabilidade",  supplier_id="sup-004", cost_center="Administrativo"),
]


async def main():
    async with async_session_maker() as session:
        # Verifica quais IDs já existem para ser idempotente
        result = await session.execute(select(FinancialEntryModel.id))
        existing_ids = {row[0] for row in result.all()}

        inserted = 0
        skipped = 0
        for entry_data in HISTORICO:
            if entry_data["id"] in existing_ids:
                skipped += 1
                continue
            entry = FinancialEntryModel(**entry_data)
            session.add(entry)
            inserted += 1

        await session.commit()
        print(f"✅ Concluído: {inserted} lançamentos inseridos, {skipped} já existiam.")


if __name__ == "__main__":
    asyncio.run(main())
