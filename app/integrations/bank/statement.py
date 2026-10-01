"""Bank statement files (OFX 1.x SGML, OFX 2.x XML, CSV) -> normalized transactions.

Brazilian banks differ in the details (decimal comma in TRNAMT, positive debits, CP1252 text,
timezone suffixes on dates), so the parser is deliberately tolerant and pure: bytes in, data out.
"""

import csv
import hashlib
import io
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime


class StatementError(ValueError):
    """The file is not a statement we can read."""


@dataclass
class ParsedTransaction:
    external_id: str
    date: str          # ISO yyyy-mm-dd
    amount: float      # positive = money in, negative = money out
    description: str


@dataclass
class ParsedStatement:
    bank_id: str | None = None
    account_id: str | None = None
    transactions: list[ParsedTransaction] = field(default_factory=list)


_DEBIT_TYPES = {"DEBIT", "PAYMENT", "CHECK", "FEE", "SRVCHG", "ATM", "POS", "DIRECTDEBIT"}


def _decode(content: bytes) -> str:
    try:
        return content.decode("utf-8-sig")
    except UnicodeDecodeError:
        return content.decode("cp1252", errors="replace")


def _parse_amount(raw: str) -> float:
    s = raw.strip().replace("R$", "").replace(" ", "").replace(" ", "")
    if not s:
        raise ValueError("vazio")
    negative = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    if "," in s:  # Brazilian notation: 1.500,00
        s = s.replace(".", "").replace(",", ".")
    value = float(s)
    return -abs(value) if negative else value


def _parse_date(raw: str) -> str:
    s = raw.strip()
    digits = re.match(r"(\d{8})", s)
    if digits and "/" not in s and "-" not in s[:8]:
        return datetime.strptime(digits.group(1), "%Y%m%d").date().isoformat()
    for fmt in ("%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d/%m/%y", "%d.%m.%Y"):
        try:
            return datetime.strptime(s[:10] if fmt != "%d/%m/%y" else s[:8], fmt).date().isoformat()
        except ValueError:
            continue
    raise ValueError(f"data inválida: {raw}")


def _tag(block: str, name: str) -> str | None:
    m = re.search(rf"<{name}>([^<\r\n]*)", block, re.IGNORECASE)
    return m.group(1).strip() if m and m.group(1).strip() else None


def _parse_ofx(text: str) -> ParsedStatement:
    st = ParsedStatement(bank_id=_tag(text, "BANKID"), account_id=_tag(text, "ACCTID"))
    blocks = re.split(r"<STMTTRN>", text, flags=re.IGNORECASE)[1:]
    for block in blocks:
        block = re.split(r"</STMTTRN>|</BANKTRANLIST>", block, flags=re.IGNORECASE)[0]
        posted, raw_amount = _tag(block, "DTPOSTED"), _tag(block, "TRNAMT")
        if not posted or not raw_amount:
            continue
        amount = _parse_amount(raw_amount)
        if (_tag(block, "TRNTYPE") or "").upper() in _DEBIT_TYPES and amount > 0:
            amount = -amount  # some banks export debits as positive numbers
        date = _parse_date(posted)
        description = _tag(block, "MEMO") or _tag(block, "NAME") or "(sem descrição)"
        external_id = _tag(block, "FITID") or _hash_id(date, amount, description, 0)
        st.transactions.append(ParsedTransaction(external_id, date, round(amount, 2), description))
    if not st.transactions:
        raise StatementError("Nenhuma transação encontrada no arquivo OFX")
    return st


def _norm(header: str) -> str:
    h = unicodedata.normalize("NFKD", header).encode("ascii", "ignore").decode().lower().strip()
    return re.sub(r"[^a-z]", "", h)


_COLUMNS = {
    "date": {"data", "date", "dt", "datalancamento", "datamovimento", "dataoperacao"},
    "description": {"descricao", "description", "historico", "lancamento", "memo", "detalhe", "estabelecimento"},
    "amount": {"valor", "amount", "value", "quantia", "valorrs"},
    "credit": {"credito", "credit", "entrada", "entradas"},
    "debit": {"debito", "debit", "saida", "saidas"},
}


def _hash_id(date: str, amount: float, description: str, occurrence: int) -> str:
    raw = f"{date}|{amount:.2f}|{description.strip().lower()}|{occurrence}"
    return "h-" + hashlib.sha1(raw.encode()).hexdigest()[:24]


def _parse_csv(text: str) -> ParsedStatement:
    lines = [l for l in text.splitlines() if l.strip()]
    if len(lines) < 2:
        raise StatementError("Arquivo CSV vazio")
    delimiter = ";" if lines[0].count(";") >= lines[0].count(",") else ","
    reader = csv.reader(io.StringIO("\n".join(lines)), delimiter=delimiter)
    header = [_norm(h) for h in next(reader)]
    col = {}
    for key, names in _COLUMNS.items():
        for i, h in enumerate(header):
            if h in names:
                col[key] = i
                break
    if "date" not in col or "description" not in col or not ("amount" in col or "credit" in col or "debit" in col):
        raise StatementError("Colunas não reconhecidas: o CSV precisa de data, descrição e valor (ou crédito/débito)")

    st = ParsedStatement()
    seen: dict[tuple, int] = {}
    for row in reader:
        if len(row) < len(header):
            continue
        try:
            date = _parse_date(row[col["date"]])
            if "amount" in col and row[col["amount"]].strip():
                amount = _parse_amount(row[col["amount"]])
            else:
                credit = row[col["credit"]].strip() if "credit" in col else ""
                debit = row[col["debit"]].strip() if "debit" in col else ""
                amount = _parse_amount(credit) if credit else -abs(_parse_amount(debit))
        except ValueError:
            continue  # summary/balance lines
        description = row[col["description"]].strip() or "(sem descrição)"
        key = (date, round(amount, 2), description.lower())
        occurrence = seen.get(key, 0)
        seen[key] = occurrence + 1
        st.transactions.append(ParsedTransaction(_hash_id(date, amount, description, occurrence), date, round(amount, 2), description))
    if not st.transactions:
        raise StatementError("Nenhuma transação válida encontrada no CSV")
    return st


def parse_statement(content: bytes, filename: str) -> ParsedStatement:
    text = _decode(content)
    if "<OFX" in text.upper() or "OFXHEADER" in text.upper():
        return _parse_ofx(text)
    if filename.lower().endswith((".csv", ".txt")):
        return _parse_csv(text)
    raise StatementError("Formato não suportado. Envie o extrato em OFX ou CSV")
