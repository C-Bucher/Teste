# NOTA: Testa o comprovante anexado ao lançamento: upload, download e acesso só pela empresa dona.

"""FIN-2: receipts attached to financial entries, stored privately and served only to the owning company."""


async def _entry(client, acc):
    r = await client.post("/financial/entries", headers=acc["headers"], json={"type": "DESPESA", "amount": 80, "description": "Internet"})
    return r.json()["id"]


async def test_upload_and_download_attachment(client, company_a):
    eid = await _entry(client, company_a)
    r = await client.post(f"/financial/entries/{eid}/attachment", headers=company_a["headers"],
                          files={"file": ("nota.pdf", b"%PDF-1.4 conteudo", "application/pdf")})
    assert r.status_code == 200, r.text
    assert r.json()["attachment_name"] == "nota.pdf"

    d = await client.get(f"/financial/entries/{eid}/attachment", headers=company_a["headers"])
    assert d.status_code == 200
    assert d.content == b"%PDF-1.4 conteudo"


async def test_attachment_is_private_to_the_company(client, company_a, company_b):
    eid = await _entry(client, company_a)
    await client.post(f"/financial/entries/{eid}/attachment", headers=company_a["headers"],
                      files={"file": ("nota.pdf", b"%PDF-1.4 x", "application/pdf")})
    assert (await client.get(f"/financial/entries/{eid}/attachment", headers=company_b["headers"])).status_code == 404
    assert (await client.post(f"/financial/entries/{eid}/attachment", headers=company_b["headers"],
                              files={"file": ("x.pdf", b"%PDF", "application/pdf")})).status_code == 404
    # the stored file path never reaches the API response
    entry = (await client.get(f"/financial/entries/{eid}", headers=company_a["headers"])).json()
    assert "attachment_path" not in entry


async def test_rejects_disallowed_type_and_oversize(client, company_a):
    eid = await _entry(client, company_a)
    r = await client.post(f"/financial/entries/{eid}/attachment", headers=company_a["headers"],
                          files={"file": ("virus.exe", b"MZ", "application/octet-stream")})
    assert r.status_code == 400
    big = b"0" * (10 * 1024 * 1024 + 1)
    r = await client.post(f"/financial/entries/{eid}/attachment", headers=company_a["headers"],
                          files={"file": ("grande.pdf", big, "application/pdf")})
    assert r.status_code == 413


async def test_download_without_attachment_is_404(client, company_a):
    eid = await _entry(client, company_a)
    assert (await client.get(f"/financial/entries/{eid}/attachment", headers=company_a["headers"])).status_code == 404


async def test_export_does_not_leak_storage_key(client, company_a):
    eid = await _entry(client, company_a)
    await client.post(f"/financial/entries/{eid}/attachment", headers=company_a["headers"],
                      files={"file": ("nota.pdf", b"%PDF-1.4 x", "application/pdf")})
    r = await client.post("/exports/request", headers=company_a["headers"], json={"type": "DRE", "format": "JSON"})
    assert r.status_code == 200, r.text
    exported = (await client.get(f"/exports/download/{r.json()['id']}", headers=company_a["headers"])).text
    assert "attachment_key" not in exported
    assert "nota.pdf" in exported
