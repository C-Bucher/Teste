"""Bank statement parsing: OFX 1.x (SGML, as most Brazilian banks export), OFX 2.x (XML) and CSV."""

import pytest

from app.integrations.bank.statement import StatementError, parse_statement

OFX_SGML = """OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
<SIGNONMSGSRSV1><SONRS><STATUS><CODE>0<SEVERITY>INFO</STATUS><DTSERVER>20260930120000[-3:BRT]<LANGUAGE>POR</SONRS></SIGNONMSGSRSV1>
<BANKMSGSRSV1><STMTTRNRS><TRNUID>1<STMTRS><CURDEF>BRL
<BANKACCTFROM><BANKID>0260<ACCTID>12345-6<ACCTTYPE>CHECKING</BANKACCTFROM>
<BANKTRANLIST><DTSTART>20260901<DTEND>20260930
<STMTTRN><TRNTYPE>CREDIT<DTPOSTED>20260905000000[-3:BRT]<TRNAMT>1500.00<FITID>abc-001<MEMO>Transferência recebida - Cliente Ação
</STMTTRN>
<STMTTRN><TRNTYPE>DEBIT<DTPOSTED>20260910<TRNAMT>-89,90<FITID>abc-002<NAME>PAG*INTERNET FIBRA
</STMTTRN>
</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>
""".encode("cp1252")

OFX_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<?OFX OFXHEADER="200" VERSION="220"?>
<OFX><BANKMSGSRSV1><STMTTRNRS><STMTRS>
<BANKACCTFROM><BANKID>341</BANKID><ACCTID>9999</ACCTID></BANKACCTFROM>
<BANKTRANLIST>
<STMTTRN><TRNTYPE>DEBIT</TRNTYPE><DTPOSTED>20260912</DTPOSTED><TRNAMT>-250.00</TRNAMT><FITID>x1</FITID><MEMO>Aluguel</MEMO></STMTTRN>
</BANKTRANLIST></STMTRS></STMTTRNRS></BANKMSGSRSV1></OFX>"""


def test_parses_sgml_ofx_from_brazilian_bank():
    st = parse_statement(OFX_SGML, "extrato.ofx")
    assert st.bank_id == "0260"
    assert st.account_id == "12345-6"
    assert [(t.external_id, t.date, t.amount) for t in st.transactions] == [
        ("abc-001", "2026-09-05", 1500.00),
        ("abc-002", "2026-09-10", -89.90),
    ]
    assert st.transactions[0].description == "Transferência recebida - Cliente Ação"
    assert st.transactions[1].description == "PAG*INTERNET FIBRA"


def test_parses_xml_ofx():
    st = parse_statement(OFX_XML, "extrato.ofx")
    assert st.bank_id == "341"
    assert [(t.date, t.amount, t.description) for t in st.transactions] == [("2026-09-12", -250.0, "Aluguel")]


def test_parses_brazilian_csv_with_semicolon_and_decimal_comma():
    csv = "Data;Descrição;Valor\n05/09/2026;Pix recebido;1.500,00\n10/09/2026;Conta de luz;-120,35\n".encode("utf-8")
    st = parse_statement(csv, "extrato.csv")
    assert [(t.date, t.amount, t.description) for t in st.transactions] == [
        ("2026-09-05", 1500.0, "Pix recebido"),
        ("2026-09-10", -120.35, "Conta de luz"),
    ]
    # CSV has no FITID: the id is a stable hash, so re-importing produces the same ids
    again = parse_statement(csv, "extrato.csv")
    assert [t.external_id for t in st.transactions] == [t.external_id for t in again.transactions]


def test_parses_csv_with_comma_and_iso_dates_and_separate_columns():
    csv = b"date,description,credit,debit\n2026-09-01,Venda,300.00,\n2026-09-02,Fornecedor,,75.50\n"
    st = parse_statement(csv, "x.csv")
    assert [(t.date, t.amount) for t in st.transactions] == [("2026-09-01", 300.0), ("2026-09-02", -75.5)]


def test_identical_csv_lines_on_the_same_day_are_kept_apart():
    csv = b"data;descricao;valor\n05/09/2026;Cafe;-5,00\n05/09/2026;Cafe;-5,00\n"
    st = parse_statement(csv, "x.csv")
    assert len({t.external_id for t in st.transactions}) == 2


@pytest.mark.parametrize("content,name", [(b"isto nao e um extrato", "x.ofx"), (b"a;b\n1;2\n", "x.csv"), (b"\x00\x01", "x.pdf")])
def test_rejects_unreadable_files(content, name):
    with pytest.raises(StatementError):
        parse_statement(content, name)
