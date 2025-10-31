# src/external_api.py
import requests

def buscar_cep(cep: str) -> dict | None:
    cep = cep.strip().replace("-", "")
    if not cep.isdigit() or len(cep) != 8:
        print("CEP inválido (use 8 dígitos).")
        return None
    url = f"https://viacep.com.br/ws/{cep}/json/"
    try:
        r = requests.get(url, timeout=10)
        r.raise_for_status()
        data = r.json()
        if "erro" in data:
            print("CEP não encontrado.")
            return None
        return data
    except Exception as e:
        print("Falha ao consultar ViaCEP:", e)
        return None
