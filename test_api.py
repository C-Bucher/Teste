import urllib.request, json

# Login
data = json.dumps({"email": "admin@techconnect.com.br", "password": "Admin@123"}).encode()
req = urllib.request.Request("http://localhost:8000/api/v1/auth/login", data=data, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as r:
    token_data = json.loads(r.read())
    token = token_data.get("access_token", "")
    print("Token OK:", token[:30], "...")

# Monthly Summary
req2 = urllib.request.Request("http://localhost:8000/api/v1/financial/monthly-summary", headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req2) as r:
    data = json.loads(r.read())
    for item in data["items"]:
        print(f"{item['name']}: R+{item['receitas']:.0f} R-{item['despesas']:.0f}")

# DRE
req3 = urllib.request.Request("http://localhost:8000/api/v1/financial/dre", headers={"Authorization": f"Bearer {token}"})
with urllib.request.urlopen(req3) as r:
    data = json.loads(r.read())
    print("DRE total_receitas:", data["total_receitas"])
    print("DRE total_despesas:", data["total_despesas"])
