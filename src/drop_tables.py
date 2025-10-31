# src/drop_tables.py
from utils import get_credentials
from connection_functions import CRUD_Connect

DROP_SQL = [
    "DROP TABLE HS_TELECONSULTA PURGE",
    "DROP TABLE HS_PACIENTE PURGE"
]

if __name__ == "__main__":
    user_, pass_ = get_credentials()
    cC, cR, cU, cD, conn, ok = CRUD_Connect(user_, pass_)
    if not ok:
        print("Sem conexão.")
        raise SystemExit(1)

    try:
        for sql in DROP_SQL:
            try:
                cD.execute(sql)
                conn.commit()
            except Exception as e:
                print("Aviso ao dropar (talvez não exista):", e)
        print("Tabelas removidas.")
    finally:
        conn.close()
