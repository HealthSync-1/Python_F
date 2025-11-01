from utils import get_credentials
from connection_functions import CRUD_Connect

CREATE_SQL = [
    """
    CREATE TABLE HS_PACIENTE (
      ID          NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
      NOME        VARCHAR2(100)     NOT NULL,
      NASCIMENTO  DATE              NOT NULL,
      TELEFONE    VARCHAR2(20)      NOT NULL,
      ALTA        CHAR(1) DEFAULT 'N' CHECK (ALTA IN ('S','N'))
    )
    """,
    """
    CREATE TABLE HS_TELECONSULTA (
      ID               NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
      PACIENTE_ID      NUMBER           NOT NULL,
      MEDICO           VARCHAR2(100)    NOT NULL,
      DATA_HORA        DATE             NOT NULL,
      DIAGNOSTICO      VARCHAR2(400)    NOT NULL,
      URGENCIA         VARCHAR2(10)     NOT NULL CHECK (URGENCIA IN ('baixa','media','alta')),
      ELEGIVEL_ONLINE  CHAR(1)          NOT NULL CHECK (ELEGIVEL_ONLINE IN ('S','N')),
      STATUS           VARCHAR2(20)     NOT NULL CHECK (STATUS IN ('agendada','em_andamento','concluida','cancelada')),
      PLANO            VARCHAR2(2000),
      CONSTRAINT FK_TELE_PACIENTE FOREIGN KEY (PACIENTE_ID) REFERENCES HS_PACIENTE(ID)
    )
    """
]

if __name__ == "__main__":
    user_, pass_ = get_credentials()
    cC, cR, cU, cD, conn, ok = CRUD_Connect(user_, pass_)
    if not ok:
        print("Sem conexão.")
        raise SystemExit(1)

    try:
        for sql in CREATE_SQL:
            try:
                cC.execute(sql)
                conn.commit()
            except Exception as e:
                print("Aviso ao criar (talvez já exista):", e)
        print("Tabelas criadas/prontas.")
    finally:
        conn.close()
