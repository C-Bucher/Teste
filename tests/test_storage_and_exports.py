# NOTA: Testa o armazenamento (local e S3) e as exportações em XLSX e PDF.

"""STO-1 (S3-compatible storage backend) and EXP-1 (XLSX/PDF exports)."""

import io

import pytest

from app.core import storage


class FakeS3:
    def __init__(self):
        self.objects = {}

    def put_object(self, Bucket, Key, Body, ContentType):
        self.objects[(Bucket, Key)] = Body

    def get_object(self, Bucket, Key):
        if (Bucket, Key) not in self.objects:
            raise KeyError(Key)
        return {"Body": io.BytesIO(self.objects[(Bucket, Key)])}

    def delete_object(self, Bucket, Key):
        self.objects.pop((Bucket, Key), None)

    def get_paginator(self, _name):
        objects = self.objects

        class P:
            def paginate(self, Bucket, Prefix):
                yield {"Contents": [{"Key": k} for (b, k) in list(objects) if b == Bucket and k.startswith(Prefix)]}
        return P()


@pytest.fixture
def s3(monkeypatch):
    fake = FakeS3()
    monkeypatch.setenv("STORAGE_BACKEND", "s3")
    monkeypatch.setenv("S3_BUCKET", "techconnect-test")
    monkeypatch.setattr(storage, "_s3_client", fake)
    return fake


async def test_attachments_and_exports_go_to_s3_when_configured(client, company_a, s3):
    h = company_a["headers"]
    entry = (await client.post("/financial/entries", headers=h, json={"type": "DESPESA", "amount": 10})).json()
    await client.post(f"/financial/entries/{entry['id']}/attachment", headers=h, files={"file": ("nota.pdf", b"%PDF-s3", "application/pdf")})
    assert any(k.startswith(f"attachments/{company_a['user']['company_id']}/") for (_, k) in s3.objects)
    assert (await client.get(f"/financial/entries/{entry['id']}/attachment", headers=h)).content == b"%PDF-s3"

    exp = (await client.post("/exports/request", headers=h, json={"type": "DRE", "format": "CSV"})).json()
    assert ("techconnect-test", f"exports/{company_a['user']['company_id']}/export_{exp['id']}.csv") in s3.objects
    assert (await client.get(f"/exports/download/{exp['id']}", headers=h)).status_code == 200

    await storage.delete_company_files(company_a["user"]["company_id"])
    assert not s3.objects


@pytest.mark.parametrize("fmt,magic", [("XLSX", b"PK"), ("PDF", b"%PDF")])
async def test_xlsx_and_pdf_exports_are_real_files(client, company_a, fmt, magic):
    h = company_a["headers"]
    await client.post("/suppliers/", headers=h, json={"name": "=CMD|calc", "category": "TI"})
    exp = await client.post("/exports/request", headers=h, json={"type": "FORNECEDORES", "format": fmt})
    assert exp.status_code == 200, exp.text
    d = await client.get(f"/exports/download/{exp.json()['id']}", headers=h)
    assert d.status_code == 200 and d.content.startswith(magic)
    if fmt == "XLSX":
        from openpyxl import load_workbook
        ws = load_workbook(io.BytesIO(d.content)).active
        values = [c.value for row in ws.iter_rows() for c in row]
        assert "'=CMD|calc" in values, "formula injection neutralised in spreadsheets too"
        assert "company_id" not in values


async def test_unknown_format_is_rejected(client, company_a):
    assert (await client.post("/exports/request", headers=company_a["headers"], json={"type": "DRE", "format": "DOCX"})).status_code == 400
