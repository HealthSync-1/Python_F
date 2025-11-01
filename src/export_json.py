import os
import json

def export_pacientes(cursor_read, out_dir="exports", filename="pacientes.json"):
    cursor_read.execute("""
        SELECT id, nome, TO_CHAR(nascimento, 'DD/MM/YYYY') AS nascimento, telefone, alta
          FROM hs_paciente
         ORDER BY id
    """)
    rows = cursor_read.fetchall()
    data = [
        {"id": r[0], "nome": r[1], "nascimento": r[2], "telefone": r[3], "alta": r[4]}
        for r in rows
    ]
    return _dump(data, out_dir, filename)

def export_teleconsultas(cursor_read, out_dir="exports", filename="teleconsultas.json"):
    cursor_read.execute("""
        SELECT id, paciente_id, medico,
               TO_CHAR(data_hora, 'DD/MM/YYYY HH24:MI') AS data_hora,
               diagnostico, urgencia, elegivel_online, status, plano
          FROM hs_teleconsulta
         ORDER BY id
    """)
    rows = cursor_read.fetchall()
    data = [
        {
            "id": r[0], "paciente_id": r[1], "medico": r[2], "data_hora": r[3],
            "diagnostico": r[4], "urgencia": r[5], "elegivel_online": r[6],
            "status": r[7], "plano": r[8]
        } for r in rows
    ]
    return _dump(data, out_dir, filename)

def export_join(cursor_read, out_dir="exports", filename="teleconsultas_pacientes.json"):
    cursor_read.execute("""
        SELECT t.id, p.nome AS paciente, TO_CHAR(p.nascimento,'DD/MM/YYYY') AS nasc,
               t.medico, TO_CHAR(t.data_hora,'DD/MM/YYYY HH24:MI') AS data_hora,
               t.diagnostico, t.urgencia, t.elegivel_online, t.status, t.plano
          FROM hs_teleconsulta t
          JOIN hs_paciente    p ON p.id = t.paciente_id
         ORDER BY t.id
    """)
    rows = cursor_read.fetchall()
    data = [
        {
            "teleconsulta_id": r[0], "paciente": r[1], "nascimento": r[2],
            "medico": r[3], "data_hora": r[4], "diagnostico": r[5],
            "urgencia": r[6], "elegivel_online": r[7], "status": r[8], "plano": r[9]
        } for r in rows
    ]
    return _dump(data, out_dir, filename)

def _dump(data, out_dir, filename):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, filename)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return path
