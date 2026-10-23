# NOTA: Relatório do que está configurado e do que falta para produção (IA, pagamentos, e-mail, bancos, armazenamento etc.).
#       Alimenta a aba Conexões em Configurações e o aviso de inicialização.

"""What is configured and what is missing for production (Configurações → Conexões de API and the startup log)."""

import os


def _set(name: str) -> bool:
    value = os.getenv(name, "").strip()
    return bool(value) and not value.startswith(("sua-", "seu-", "troque"))


def integrations_report() -> list[dict]:
    """Each item: key, label, status (configured | partial | unconfigured), detail (what to do)."""
    prod = os.getenv("APP_ENV", "development").lower() == "production"
    asaas = _set("ASAAS_API_KEY")
    asaas_env = "produção" if os.getenv("ASAAS_ENV", "sandbox").lower() == "production" else "sandbox"
    items = [
        {"key": "gemini", "label": "IA (Gemini)",
         "status": "configured" if _set("GEMINI_API_KEY") else "unconfigured",
         "detail": "Respostas da IA com o modelo." if _set("GEMINI_API_KEY") else "Sem chave: a IA responde por regras com os dados reais."},
        {"key": "payments", "label": "Pagamentos (Asaas)",
         "status": ("configured" if asaas and _set("ASAAS_WEBHOOK_TOKEN") else "partial") if asaas else "unconfigured",
         "detail": (f"Ambiente {asaas_env}." + ("" if _set("ASAAS_WEBHOOK_TOKEN") else " Falta ASAAS_WEBHOOK_TOKEN: pagamentos não serão confirmados."))
         if asaas else ("Checkout desativado em produção." if prod else "Pagamento simulado (só desenvolvimento).")},
        {"key": "email", "label": "E-mail (SMTP)",
         "status": "configured" if _set("SMTP_HOST") else "unconfigured",
         "detail": "Recuperação de senha e avisos são enviados." if _set("SMTP_HOST") else "E-mails só ficam no log: a recuperação de senha não chega ao usuário."},
        {"key": "bank", "label": "Bancos (Pluggy)",
         "status": ("configured" if _set("PLUGGY_WEBHOOK_SECRET") else "partial") if _set("PLUGGY_CLIENT_ID") and _set("PLUGGY_CLIENT_SECRET") else "unconfigured",
         "detail": "Conexão automática ativa." if _set("PLUGGY_CLIENT_ID") else "Só importação de extrato OFX/CSV."},
        {"key": "storage", "label": "Armazenamento de arquivos",
         "status": "configured" if os.getenv("STORAGE_BACKEND", "local").lower() == "s3" and _set("S3_BUCKET") else ("partial" if prod else "configured"),
         "detail": "S3 compatível (compartilhado entre servidores)." if os.getenv("STORAGE_BACKEND", "local").lower() == "s3"
         else "Disco local do servidor: use S3/Supabase Storage com mais de uma instância."},
        {"key": "scheduler", "label": "Sincronização diária",
         "status": "configured" if _set("CRON_SECRET") else "unconfigured",
         "detail": "Agende POST /api/v1/jobs/daily uma vez por dia (alertas e sincronização bancária)." if _set("CRON_SECRET")
         else "Defina CRON_SECRET e agende POST /api/v1/jobs/daily: sem isso não há alertas de vencimento nem sincronização diária."},
        {"key": "encryption", "label": "Chave de criptografia",
         "status": "configured" if _set("ENCRYPTION_KEY") else ("partial" if prod else "configured"),
         "detail": "Chave própria para segredos do 2FA." if _set("ENCRYPTION_KEY")
         else "Usando a SECRET_KEY: trocar a SECRET_KEY invalidaria o 2FA de todos. Defina ENCRYPTION_KEY."},
    ]
    return items


def production_warnings() -> list[str]:
    return [f"{i['label']}: {i['detail']}" for i in integrations_report() if i["status"] != "configured"]
