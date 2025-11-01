from utils import get_credentials, parse_date_br, parse_datetime_br
from connection_functions import CRUD_Connect

def get_or_create_paciente(c_read, c_create, conn, nome: str, nasc_str: str, telefone: str) -> int:
    """
    Retorna o ID do paciente se já existir (nome + telefone + nascimento).
    Caso não exista, cria e retorna o novo ID.
    """
    nasc = parse_date_br(nasc_str)

    c_read.execute(
        "SELECT id FROM hs_paciente "
        "WHERE nome = :n AND telefone = :t AND TRUNC(nascimento) = TRUNC(:d)",
        n=nome, t=telefone, d=nasc
    )
    row = c_read.fetchone()
    if row:
        print(f"Paciente já existe: {nome} ({telefone}) -> id {row[0]}")
        return int(row[0])

    id_var = c_create.var(int)
    c_create.execute(
        "INSERT INTO hs_paciente (nome, nascimento, telefone, alta) "
        "VALUES (:n, :d, :t, 'N') RETURNING id INTO :id",
        n=nome, d=nasc, t=telefone, id=id_var
    )
    conn.commit()
    novo_id = id_var.getvalue()[0]
    print(f"Paciente criado: {nome} ({telefone}) -> id {novo_id}")
    return int(novo_id)


def get_or_create_teleconsulta(
    c_read, c_create, conn,
    paciente_id: int, medico: str, dt_str: str,
    diagnostico: str, urgencia: str, elegivel_online: str, status: str, plano: str
) -> int:
    """
    Retorna o ID da teleconsulta se já existir (paciente + médico + data_hora).
    Caso não exista, cria e retorna o novo ID.
    """
    dt = parse_datetime_br(dt_str)

    c_read.execute(
        "SELECT id FROM hs_teleconsulta "
        "WHERE paciente_id = :pid AND medico = :m AND data_hora = :dt",
        pid=paciente_id, m=medico, dt=dt
    )
    row = c_read.fetchone()
    if row:
        print(f"Teleconsulta já existe: pac={paciente_id} | {dt_str} | {medico} -> id {row[0]}")
        return int(row[0])

    c_create.execute(
        "INSERT INTO hs_teleconsulta "
        "(paciente_id, medico, data_hora, diagnostico, urgencia, elegivel_online, status, plano) "
        "VALUES (:pid, :med, :dt, :diag, :urg, :elig, :st, :pl)",
        pid=paciente_id, med=medico, dt=dt, diag=diagnostico,
        urg=urgencia, elig=elegivel_online, st=status, pl=plano
    )
    conn.commit()

    c_read.execute(
        "SELECT id FROM hs_teleconsulta "
        "WHERE paciente_id = :pid AND medico = :m AND data_hora = :dt",
        pid=paciente_id, m=medico, dt=dt
    )
    rec = c_read.fetchone()
    novo_id = int(rec[0])
    print(f"Teleconsulta criada: pac={paciente_id} | {dt_str} | {medico} -> id {novo_id}")
    return novo_id


def main():
    user_, pass_ = get_credentials()
    cC, cR, cU, cD, conn, ok = CRUD_Connect(user_, pass_)
    if not ok:
        print("Sem conexão.")
        return

    try:
        # -------------------------
        # Pacientes 
        # -------------------------
        pacientes_seed = [
            ("Ana Paula Silva", "12/03/1985", "11999990001"),
            ("Bruno Souza",     "25/07/1990", "11999990002"),
            ("Carla Mendes",    "02/11/1978", "11999990003"),
        ]

        pacientes_ids = []
        for nome, nasc, tel in pacientes_seed:
            pid = get_or_create_paciente(cR, cC, conn, nome, nasc, tel)
            pacientes_ids.append(pid)

        # -------------------------
        # Teleconsultas (seed)
        # -------------------------
        teleconsultas_seed = [
            (0, "Dr. Marcos", "30/10/2025 14:30", "Dor lombar crônica",  "media", "S", "agendada",  "Exercícios leves"),
            (1, "Dra. Livia", "31/10/2025 09:00", "Reabilitação joelho", "alta",  "N", "agendada",  "Fortalecimento quadríceps"),
            (2, "Dr. Paulo",  "01/11/2025 10:00", "Ombro doloroso",      "baixa", "S", "agendada",  ""),
        ]

        for idx, med, dt_str, diag, urg, elig, st, plano in teleconsultas_seed:
            if idx < 0 or idx >= len(pacientes_ids):
                print(f"Índice de paciente inválido no seed: {idx}")
                continue
            get_or_create_teleconsulta(
                cR, cC, conn,
                paciente_id=pacientes_ids[idx],
                medico=med, dt_str=dt_str,
                diagnostico=diag, urgencia=urg, elegivel_online=elig, status=st, plano=plano
            )

        # -------------------------
        # Smoke test
        # -------------------------
        cR.execute("SELECT COUNT(1) FROM hs_paciente")
        print("Total pacientes:", cR.fetchone()[0])
        cR.execute("SELECT COUNT(1) FROM hs_teleconsulta")
        print("Total teleconsultas:", cR.fetchone()[0])

    except Exception as e:
        print("Erro no seed:", e)
        try:
            conn.rollback()
        except: ...
    finally:
        try:
            conn.close()
        except: ...


if __name__ == "__main__":
    main()
