import os, sys, oracledb
from dotenv import load_dotenv

load_dotenv(override=True)

IC = os.getenv("INSTANT_CLIENT")
if IC:
    try:
        oracledb.init_oracle_client(lib_dir=IC)
        print("Modo Thick (Instant Client) habilitado.")
    except Exception as e:
        print("Aviso ao iniciar Instant Client (seguindo mesmo assim):", e)

print("Python:", sys.version)
print("oracledb:", oracledb.__version__)
print("Thin mode?:", oracledb.is_thin_mode())

HOST = os.getenv("HOST", "oracle.fiap.com.br")
PORT = os.getenv("PORT", "1521")
SID  = os.getenv("SID",  "orcl")

try:
    dsn = oracledb.makedsn(HOST, PORT, service_name=SID)
except TypeError:
    dsn = oracledb.makedsn(HOST, PORT, sid=SID)

try:
    conn = oracledb.connect(
        user=os.getenv("USER"),
        password=os.getenv("PASSWORD"),
        dsn=dsn
    )
    with conn.cursor() as c:
        c.execute("SELECT 1 FROM dual")
        print("Conexão OK:", c.fetchone())
    conn.close()
    sys.exit(0)
except Exception as e:
    print("Falha na conexão:", e)
    sys.exit(1)
