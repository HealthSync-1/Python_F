# src/connection_functions.py
import os
import oracledb
from dotenv import load_dotenv

load_dotenv(override=True)

HOST = os.getenv("HOST", "oracle.fiap.com.br")
PORT = os.getenv("PORT", "1521")
SID  = os.getenv("SID",  "orcl")
IC_LIB = os.getenv("INSTANT_CLIENT")  # se quiser Modo Thick

def CRUD_Connect(user_id: str, user_pass: str, host=HOST, port=PORT, SID=SID, only_test=False):
    """
    Usa oracledb em:
    - Modo Thick se INSTANT_CLIENT estiver definido e válido.
    - Caso contrário, Modo Thin (não precisa Instant Client).
    """
    try:
        if IC_LIB:
            # Modo Thick (com Instant Client)
            oracledb.init_oracle_client(lib_dir=IC_LIB)
            print("Oracle Client inicializado (Modo Thick).")
        else:
            # Modo Thin (default)
            print("Usando Modo Thin (sem Instant Client).")
    except Exception as e:
        print("Aviso ao iniciar Oracle Client (seguindo em Thin se possível):", e)

    # DSN: tenta service_name (mais comum), se a sua versão não aceitar, cai para sid
    try:
        dsn = oracledb.makedsn(host, port, service_name=SID)
    except TypeError:
        dsn = oracledb.makedsn(host, port, sid=SID)

    try:
        print("Conectando ao Oracle...")
        # ⚠️ Removido o parâmetro encoding="UTF-8"
        conn = oracledb.connect(user=user_id, password=user_pass, dsn=dsn)
    except Exception as e:
        print("Falha na conexão:", e)
        return False, False, False, False, False, False

    try:
        c_create = conn.cursor()
        c_read   = conn.cursor()
        c_update = conn.cursor()
        c_delete = conn.cursor()
    except Exception as e:
        print("Falha ao criar cursores:", e)
        try: conn.close()
        except: pass
        return False, False, False, False, False, False

    print("Conectado com sucesso!")
    if only_test:
        conn.close()
        print("Conexão de teste encerrada.")
        return False, False, False, False, False, True

    return c_create, c_read, c_update, c_delete, conn, True
