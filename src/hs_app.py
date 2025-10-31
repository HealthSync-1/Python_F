# src/hs_app.py
import os
from datetime import datetime
from utils import get_credentials, parse_date_br, parse_datetime_br, yn_to_char, char_to_bool
from connection_functions import CRUD_Connect
from external_api import buscar_cep
from export_json import export_pacientes, export_teleconsultas, export_join

CLEAR = "cls" if os.name == "nt" else "clear"

def pause():
    input("\nPressione ENTER para continuar...")

# ---------------- Pacientes ----------------
def cadastrar_paciente(cC, conn):
    os.system(CLEAR)
    print("=== Cadastrar Paciente ===\n")
    try:
        nome = input("Nome completo: ").strip()
        nasc_str = input("Nascimento (dd/mm/aaaa): ").strip()
        tel = input("Telefone (ex: 11999999999): ").strip()

        if not nome or not nasc_str or not tel:
            print("Campos obrigatórios não preenchidos.")
            pause(); return

        nasc = parse_date_br(nasc_str)  # datetime
        sql = "INSERT INTO hs_paciente (nome, nascimento, telefone, alta) VALUES (:n, :d, :t, 'N')"
        cC.execute(sql, n=nome, d=nasc, t=tel)
        conn.commit()
        print("\nPaciente cadastrado com sucesso!")
    except Exception as e:
        print("Erro ao cadastrar paciente:", e)
    pause()

def listar_pacientes(cR):
    os.system(CLEAR)
    print("=== Listar Pacientes ===\n")
    try:
        cR.execute("""
            SELECT id, nome, TO_CHAR(nascimento,'DD/MM/YYYY') AS nasc, telefone, alta
              FROM hs_paciente
             ORDER BY id
        """)
        rows = cR.fetchall()
        if not rows:
            print("Nenhum paciente.")
        else:
            print(f"{'ID':<5} {'NOME':<30} {'NASC':<12} {'TEL':<14} {'ALTA':<4}")
            print("-"*70)
            for r in rows:
                print(f"{r[0]:<5} {r[1]:<30} {r[2]:<12} {r[3]:<14} {r[4]:<4}")
    except Exception as e:
        print("Erro ao listar:", e)
    pause()

def atualizar_paciente(cU, cR, conn):
    os.system(CLEAR)
    print("=== Atualizar Paciente ===\n")
    try:
        pid = int(input("ID do paciente: ").strip())
        cR.execute("SELECT id, nome, nascimento, telefone, alta FROM hs_paciente WHERE id = :id", id=pid)
        row = cR.fetchone()
        if not row:
            print("ID não encontrado."); pause(); return

        atual_nome = row[1]
        atual_nasc = row[2]
        atual_tel  = row[3]
        atual_alta = row[4]

        print(f"Atual: Nome={atual_nome}, Nasc={atual_nasc}, Tel={atual_tel}, Alta={atual_alta}")
        nome = input("Novo nome (enter p/ manter): ").strip() or atual_nome
        nasc_in = input("Nova data nasc (dd/mm/aaaa) (enter p/ manter): ").strip()
        tel  = input("Novo telefone (enter p/ manter): ").strip() or atual_tel
        alta_in = input("Marcar alta? (S/N) (enter p/ manter): ").strip().upper()

        nasc = atual_nasc
        if nasc_in:
            nasc = parse_date_br(nasc_in)

        alta = atual_alta
        if alta_in in ("S","N"):
            alta = alta_in

        sql = """
            UPDATE hs_paciente
               SET nome = :n, nascimento = :d, telefone = :t, alta = :a
             WHERE id = :id
        """
        cU.execute(sql, n=nome, d=nasc, t=tel, a=alta, id=pid)
        conn.commit()
        print("Atualização realizada.")
    except Exception as e:
        print("Erro ao atualizar:", e)
    pause()

def excluir_paciente(cD, conn):
    os.system(CLEAR)
    print("=== Excluir Paciente ===\n")
    try:
        pid = int(input("ID do paciente: ").strip())
        # Regra: não excluir se tiver teleconsultas vinculadas
        cD.execute("SELECT COUNT(1) FROM hs_teleconsulta WHERE paciente_id = :id", id=pid)
        qtd, = cD.fetchone()
        if qtd and qtd > 0:
            print("Paciente tem teleconsultas. Cancele/exclua-as antes.")
            pause(); return
        cD.execute("DELETE FROM hs_paciente WHERE id = :id", id=pid)
        conn.commit()
        print("Exclusão concluída (se ID existia).")
    except Exception as e:
        print("Erro ao excluir:", e)
    pause()

def conceder_alta_paciente(cU, cR, conn):
    os.system(CLEAR)
    print("=== Conceder Alta a Paciente ===\n")
    try:
        pid = int(input("ID do paciente: ").strip())
        cR.execute("SELECT id FROM hs_paciente WHERE id = :id", id=pid)
        row = cR.fetchone()
        if not row:
            print("ID não encontrado."); pause(); return
        cU.execute("UPDATE hs_paciente SET alta = 'S' WHERE id = :id", id=pid)
        conn.commit()
        print("Alta registrada.")
    except Exception as e:
        print("Erro ao conceder alta:", e)
    pause()

# --------------- Teleconsultas ---------------
def agendar_teleconsulta(cC, cR, conn):
    os.system(CLEAR)
    print("=== Agendar Teleconsulta ===\n")
    try:
        # listar pacientes resumido
        cR.execute("SELECT id, nome FROM hs_paciente ORDER BY id")
        pats = cR.fetchall()
        if not pats:
            print("Cadastre pacientes antes."); pause(); return

        print("Pacientes:")
        for p in pats:
            print(f"{p[0]} - {p[1]}")
        pid = int(input("\nID do paciente: ").strip())

        # confirma existência
        cR.execute("SELECT 1 FROM hs_paciente WHERE id = :id", id=pid)
        if not cR.fetchone():
            print("Paciente inexistente."); pause(); return

        medico = input("Médico/Fisioterapeuta: ").strip()
        dt_str = input("Data/hora (dd/mm/aaaa HH:MM): ").strip()
        data_hora = parse_datetime_br(dt_str)
        diagnostico = input("Diagnóstico: ").strip()
        urgencia = input("Urgência (baixa/media/alta): ").strip().lower()
        if urgencia not in ("baixa","media","alta"):
            print("Urgência inválida."); pause(); return
        elegivel = input("Elegível online? (S/N): ").strip().upper()
        if elegivel not in ("S","N"):
            print("Valor inválido."); pause(); return
        status = "agendada"
        plano = input("Plano/Metas (opcional): ").strip()

        sql = """
            INSERT INTO hs_teleconsulta
                (paciente_id, medico, data_hora, diagnostico, urgencia, elegivel_online, status, plano)
            VALUES (:pid, :med, :dt, :diag, :urg, :elig, :st, :plan)
        """
        cC.execute(sql, pid=pid, med=medico, dt=data_hora, diag=diagnostico,
                   urg=urgencia, elig=elegivel, st=status, plan=plano)
        conn.commit()
        print("\nTeleconsulta agendada!")
    except Exception as e:
        print("Erro ao agendar:", e)
    pause()

def listar_teleconsultas(cR):
    os.system(CLEAR)
    print("=== Listar Teleconsultas ===\n")
    try:
        cR.execute("""
            SELECT t.id, p.nome, TO_CHAR(t.data_hora,'DD/MM/YYYY HH24:MI'), t.medico,
                   t.diagnostico, t.urgencia, t.elegivel_online, t.status
              FROM hs_teleconsulta t
              JOIN hs_paciente p ON p.id = t.paciente_id
             ORDER BY t.id
        """)
        rows = cR.fetchall()
        if not rows: print("Nenhuma teleconsulta.")
        else:
            print(f"{'ID':<5} {'PACIENTE':<28} {'DATA/HORA':<17} {'MEDICO':<20} {'URG':<6} {'ONL':<3} {'STATUS':<12}")
            print("-"*95)
            for r in rows:
                print(f"{r[0]:<5} {r[1]:<28} {r[2]:<17} {r[3]:<20} {r[5]:<6} {r[6]:<3} {r[7]:<12}")
    except Exception as e:
        print("Erro ao listar:", e)
    pause()

def atualizar_teleconsulta(cU, cR, conn):
    os.system(CLEAR)
    print("=== Atualizar Teleconsulta ===\n")
    try:
        tid = int(input("ID da teleconsulta: ").strip())
        cR.execute("""
            SELECT id, paciente_id, medico, data_hora, diagnostico, urgencia, elegivel_online, status, plano
              FROM hs_teleconsulta WHERE id = :id
        """, id=tid)
        t = cR.fetchone()
        if not t:
            print("ID não encontrado."); pause(); return

        print(f"Atual: med={t[2]}, dt={t[3]}, diag={t[4]}, urg={t[5]}, elig={t[6]}, status={t[7]}, plano={t[8]}")
        medico = input("Novo médico (enter p/ manter): ").strip() or t[2]
        dt_in = input("Nova data/hora (dd/mm/aaaa HH:MM) (enter p/ manter): ").strip()
        data_hora = t[3] if not dt_in else parse_datetime_br(dt_in)
        diag = input("Novo diagnóstico (enter p/ manter): ").strip() or t[4]
        urg = input("Nova urgência (baixa/media/alta) (enter p/ manter): ").strip() or t[5]
        if urg not in ("baixa","media","alta"):
            print("Urgência inválida."); pause(); return
        elig_in = input("Elegível online (S/N) (enter p/ manter): ").strip().upper()
        elig = t[6] if elig_in == "" else ("S" if elig_in == "S" else "N")
        st = input("Status (agendada/em_andamento/concluida/cancelada) (enter p/ manter): ").strip() or t[7]
        if st not in ("agendada","em_andamento","concluida","cancelada"):
            print("Status inválido."); pause(); return
        plano = input("Plano/Metas (enter p/ manter): ").strip() or t[8]

        cU.execute("""
            UPDATE hs_teleconsulta
               SET medico=:med, data_hora=:dt, diagnostico=:diag, urgencia=:urg,
                   elegivel_online=:elig, status=:st, plano=:pl
             WHERE id=:id
        """, med=medico, dt=data_hora, diag=diag, urg=urg, elig=elig, st=st, pl=plano, id=tid)
        conn.commit()
        print("Atualização realizada.")
    except Exception as e:
        print("Erro ao atualizar:", e)
    pause()

def excluir_teleconsulta(cD, conn):
    os.system(CLEAR)
    print("=== Excluir Teleconsulta ===\n")
    try:
        tid = int(input("ID da teleconsulta: ").strip())
        cD.execute("DELETE FROM hs_teleconsulta WHERE id = :id", id=tid)
        conn.commit()
        print("Exclusão concluída (se ID existia).")
    except Exception as e:
        print("Erro ao excluir:", e)
    pause()

def concluir_teleconsulta(cU, cR, conn):
    os.system(CLEAR)
    print("=== Concluir Teleconsulta ===\n")
    try:
        tid = int(input("ID da teleconsulta: ").strip())
        cR.execute("SELECT status, plano FROM hs_teleconsulta WHERE id=:id", id=tid)
        row = cR.fetchone()
        if not row:
            print("ID não encontrado."); pause(); return
        if row[0] == "concluida":
            print("Já está concluída."); pause(); return

        orient = input("Orientações pós-sessão (opcional): ").strip()
        plano_final = row[1] or ""
        if orient:
            plano_final = (plano_final + " | " if plano_final else "") + f"Orientações: {orient}"

        cU.execute("""
            UPDATE hs_teleconsulta SET status='concluida', plano=:pl WHERE id=:id
        """, pl=plano_final, id=tid)
        conn.commit()
        print("Teleconsulta concluída!")
    except Exception as e:
        print("Erro ao concluir:", e)
    pause()

# --------------- Relatórios / Export / API ---------------
def listar_por_paciente(cR):
    os.system(CLEAR)
    print("=== Teleconsultas por Paciente ===\n")
    try:
        pid = int(input("ID do paciente: ").strip())
        cR.execute("""
            SELECT id, TO_CHAR(data_hora,'DD/MM/YYYY HH24:MI'), medico, status, urgencia, elegivel_online
              FROM hs_teleconsulta
             WHERE paciente_id = :id
             ORDER BY data_hora
        """, id=pid)
        rows = cR.fetchall()
        if not rows: print("Nenhuma teleconsulta para esse paciente.")
        else:
            for r in rows:
                print(f"{r[0]} | {r[1]} | {r[2]} | {r[3]} | urg:{r[4]} | onl:{r[5]}")
    except Exception as e:
        print("Erro:", e)
    pause()

def proximas_agendadas(cR):
    os.system(CLEAR)
    print("=== Próximas (agendadas) ===\n")
    try:
        cR.execute("""
            SELECT id, paciente_id, TO_CHAR(data_hora,'DD/MM/YYYY HH24:MI'), medico
              FROM hs_teleconsulta
             WHERE status='agendada'
             ORDER BY data_hora
        """)
        rows = cR.fetchall()
        if not rows: print("Nenhuma agendada.")
        else:
            for r in rows:
                print(f"{r[0]} | pac:{r[1]} | {r[2]} | {r[3]}")
    except Exception as e:
        print("Erro:", e)
    pause()

def exportar_jsons(cR):
    os.system(CLEAR)
    print("=== Exportar JSON ===\n")
    try:
        p = export_pacientes(cR)
        t = export_teleconsultas(cR)
        j = export_join(cR)
        print(f"Pacientes .....: {p}")
        print(f"Teleconsultas .: {t}")
        print(f"Join ..........: {j}")
    except Exception as e:
        print("Erro ao exportar:", e)
    pause()

def consultar_cep_api():
    os.system(CLEAR)
    print("=== Consultar CEP (ViaCEP) ===\n")
    cep = input("CEP (8 dígitos): ").strip()
    data = buscar_cep(cep)
    if data:
        for k, v in data.items():
            print(f"- {k}: {v}")
    pause()

# ---------------- Menus ----------------
def menu_pacientes(cC, cR, cU, cD, conn):
    while True:
        os.system(CLEAR)
        print("""
== Pacientes ==
1) Cadastrar
2) Listar
3) Atualizar
4) Excluir
5) Conceder Alta
0) Voltar
""")
        op = input("> ").strip()
        if   op == "1": cadastrar_paciente(cC, conn)
        elif op == "2": listar_pacientes(cR)
        elif op == "3": atualizar_paciente(cU, cR, conn)
        elif op == "4": excluir_paciente(cD, conn)
        elif op == "5": conceder_alta_paciente(cU, cR, conn)
        elif op == "0": break
        else: print("Opção inválida."); pause()

def menu_teleconsultas(cC, cR, cU, cD, conn):
    while True:
        os.system(CLEAR)
        print("""
== Teleconsultas ==
1) Agendar
2) Listar
3) Atualizar
4) Excluir
5) Concluir Sessão
6) Listar por Paciente
7) Próximas (agendadas)
0) Voltar
""")
        op = input("> ").strip()
        if   op == "1": agendar_teleconsulta(cC, cR, conn)
        elif op == "2": listar_teleconsultas(cR)
        elif op == "3": atualizar_teleconsulta(cU, cR, conn)
        elif op == "4": excluir_teleconsulta(cD, conn)
        elif op == "5": concluir_teleconsulta(cU, cR, conn)
        elif op == "6": listar_por_paciente(cR)
        elif op == "7": proximas_agendadas(cR)
        elif op == "0": break
        else: print("Opção inválida."); pause()

def menu_relatorios_export_api(cR):
    while True:
        os.system(CLEAR)
        print("""
== Relatórios e Integrações ==
1) Exportar JSON (pacientes, teleconsultas, join)
2) Consultar CEP (ViaCEP)
0) Voltar
""")
        op = input("> ").strip()
        if   op == "1": exportar_jsons(cR)
        elif op == "2": consultar_cep_api()
        elif op == "0": break
        else: print("Opção inválida."); pause()

def main():
    user_, pass_ = get_credentials()
    cC, cR, cU, cD, conn, ok = CRUD_Connect(user_, pass_)
    if not ok:
        print("Não foi possível conectar.")
        return

    while True:
        os.system(CLEAR)
        print("""
==== HealthSync (Hospital das Clínicas) ====
1) Pacientes
2) Teleconsultas
3) Relatórios e Integracões
0) Sair
""")
        op = input("> ").strip()
        if   op == "1": menu_pacientes(cC, cR, cU, cD, conn)
        elif op == "2": menu_teleconsultas(cC, cR, cU, cD, conn)
        elif op == "3": menu_relatorios_export_api(cR)
        elif op == "0":
            print("Até mais!")
            try: conn.close()
            except: pass
            break
        else:
            print("Opção inválida."); pause()

if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nEncerrado.")
