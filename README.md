# HealthSync – Sprint 4 (Oracle) · Hospital das Clínicas

> App de console em Python com persistência Oracle: **Pacientes** e **Teleconsultas**, exportação **JSON** e consumo de **API pública (ViaCEP)**.

**Integrantes**
- **Maicon Douglas** — RM **561279**
- **Laura Lopes** — RM **566376**
- **Richard Freitas** — RM **566127**

---

## ⚡ TL;DR — Passos rápidos para rodar

> Testado em Windows 10/11 e compatível com macOS/Linux (ajuste os comandos do terminal conforme seu SO).

1. **Pré‑requisitos**
   - **Python 3.11+** (`python --version`)
   - Acesso de rede ao Oracle da FIAP (`oracle.fiap.com.br:1521`)
   - (Opcional) **Oracle Instant Client** para Modo Thick

2. **Clone e entre no projeto**
   ```powershell
   git clone <URL_DO_REPO>
   cd <PASTA_DO_REPO>
   ```

3. **Crie e ative um ambiente virtual**
   - **Windows (PowerShell)**
     ```powershell
     py -3.11 -m venv .venv
     .\.venv\Scripts\Activate.ps1
     ```
   - **macOS/Linux (bash/zsh)**
     ```bash
     python3 -m venv .venv
     source .venv/bin/activate
     ```

4. **Instale dependências**
   ```bash
   pip install -r requirements.txt
   ```

5. **Crie o arquivo `.env` (credenciais do Oracle)**  
   Crie um arquivo `.env` na raiz com **seus dados**:
   ```dotenv
   USER=SEU_USUARIO_ORACLE
   PASSWORD=SUA_SENHA_ORACLE
   HOST=oracle.fiap.com.br
   PORT=1521
   SID=orcl
   # Opcional para Modo Thick (Windows exemplo):
   # INSTANT_CLIENT=C:\instantclient-basic-windows.x64-23.9.0.25.07\instantclient_23_9
   ```

6. **Teste rápido de conexão**
   ```bash
   python quick_check.py
   ```
   Saída esperada (ex.): `Conexão OK: (1,)`

7. **Crie as tabelas no Oracle**
   ```bash
   python src/create_tables.py
   ```

8. **(Opcional) Popular com dados de exemplo (idempotente)**
   ```bash
   python src/seed_data.py
   ```

9. **Rodar o sistema (menus CRUD, export JSON, ViaCEP)**
   ```bash
   python src/hs_app.py
   ```

10. **(Opcional) Limpar o ambiente (apaga tabelas)**
    ```bash
    python src/drop_tables.py
    ```

---

## 🧱 Estrutura (visão geral)

```
.
├── requirements.txt
├── .env                      # (não versionar) credenciais Oracle
├── quick_check.py            # teste mínimo de conexão
├── sql/
│   ├── create_tables.sql     # DDL das tabelas
│   └── drop_tables.sql       # drop e purge das tabelas
└── src/
    ├── connection_functions.py  # CRUD_Connect: centraliza conexão e cursores
    ├── create_tables.py         # executa criação das tabelas
    ├── drop_tables.py           # executa remoção das tabelas
    ├── export_json.py           # exporta JSON de consultas
    ├── external_api.py          # consumo ViaCEP (API pública)
    ├── hs_app.py                # app principal (menus/submenus)
    ├── seed_data.py             # popular dados (idempotente)
    └── utils.py                 # helpers: .env, parsing de datas, etc.
```

---

## 📄 SQL – O que há nos arquivos

### `sql/create_tables.sql`
Cria o schema mínimo do HealthSync:
- **HS_PACIENTE**  
  - `ID` — `NUMBER GENERATED AS IDENTITY` (PK)  
  - `NOME` — `VARCHAR2(120)`  
  - `NASCIMENTO` — `DATE`  
  - `TELEFONE` — `VARCHAR2(20)`  
  - `ALTA` — `CHAR(1)` com `CHECK (ALTA IN ('S','N'))`, default `N`
- **HS_TELECONSULTA**  
  - `ID` — `NUMBER GENERATED AS IDENTITY` (PK)  
  - `PACIENTE_ID` — FK → `HS_PACIENTE(ID)` (ON DELETE RESTRICT)  
  - `MEDICO` — `VARCHAR2(120)`  
  - `DATA_HORA` — `DATE` (armazenando data+hora)  
  - `DIAGNOSTICO` — `VARCHAR2(200)`  
  - `URGENCIA` — `VARCHAR2(10)` com `CHECK IN ('baixa','media','alta')`  
  - `ELEGIVEL_ONLINE` — `CHAR(1)` com `CHECK IN ('S','N')`  
  - `STATUS` — `VARCHAR2(20)` com `CHECK IN ('agendada','em_andamento','concluida','cancelada')`  
  - `PLANO` — `VARCHAR2(400)` (opcional)

Também podem existir **índices auxiliares** (ex.: `IDX_TC_PAC`, `IDX_TC_DT`).

### `sql/drop_tables.sql`
Remove as tabelas, em ordem de dependência, com `PURGE` quando suportado:
- `DROP TABLE HS_TELECONSULTA PURGE;`
- `DROP TABLE HS_PACIENTE PURGE;`

---

## 🐍 Python – Resumo de cada script

### `src/create_tables.py`
- Lê as credenciais do `.env`, abre conexão (via `CRUD_Connect`) e executa o DDL de criação das tabelas.
- Pode ler de `sql/create_tables.sql` ou usar DDL embutido (conforme sua versão do projeto).  
- **Uso:** `python src/create_tables.py`

### `src/drop_tables.py`
- Remove as tabelas do schema do projeto em ordem correta (Teleconsulta → Paciente).  
- **Uso:** `python src/drop_tables.py`

### `src/export_json.py`
- Executa **consultas SELECT** e exporta resultados para a pasta `exports/` em:
  - `pacientes.json`  
  - `teleconsultas.json`  
  - `teleconsultas_join.json` (join paciente + teleconsulta)
- Útil para evidenciar o requisito de **exportação**.  
- **Uso isolado:** `python src/export_json.py`  
  - (Também é invocado a partir do menu do `hs_app.py`.)

### `src/external_api.py`
- Exemplo de **consumo de API pública (ViaCEP)** com `requests`:
  - Função `consultar_cep(cep: str)` → retorna JSON do ViaCEP.
- **Uso isolado:** `python src/external_api.py 01001000`  
  - (Também é invocado pelo menu “Relatórios e Integrações”.)

### `src/hs_app.py`  👉 **Aplicação principal (console)**
- Apresenta **menus e submenus**:
  - **Pacientes:** cadastrar, listar, atualizar, excluir, conceder alta  
    - *Regra:* impedir exclusão de paciente que possua teleconsultas vinculadas.
  - **Teleconsultas:** agendar, listar, atualizar, excluir, concluir sessão  
    - “Concluir” permite incluir orientações finais no plano.
  - **Relatórios e Integrações:** exportar JSON + consultar CEP (ViaCEP)
- Realiza **validações básicas** e mensagens claras (sucesso/erro).
- **Uso:** `python src/hs_app.py`

### `src/seed_data.py`
- **Popularizador idempotente**: cria alguns pacientes e teleconsultas **só se ainda não existirem**.
- Ajuda a ter dados previsíveis para demonstração e testes.  
- **Uso:** `python src/seed_data.py`

### `quick_check.py`
- Teste mínimo do ambiente:
  - imprime versão do Python, `oracledb` e modo (Thin/Thick),
  - tenta conectar e faz `SELECT 1 FROM dual`.
- **Uso:** `python quick_check.py`

### `src/utils.py`
- Funções utilitárias comuns ao projeto:
  - `get_credentials()` — lê `.env` e devolve `(USER, PASSWORD)`
  - `parse_date_br("dd/mm/aaaa")` → `datetime.date`
  - `parse_datetime_br("dd/mm/aaaa HH:MM")` → `datetime.datetime`
  - normalizações e helpers de formatação

> **Observação:** a conexão Oracle é centralizada em `connection_functions.py` (retorna **cursores de Create/Read/Update/Delete** + conexão). Isso desacopla a persistência do restante da aplicação.

---

## 🔐 `.env` — Configuração de ambiente

Crie na **raiz** um arquivo `.env` (não commit!) com:

```dotenv
USER=SEU_USUARIO_ORACLE
PASSWORD=SUA_SENHA_ORACLE
HOST=oracle.fiap.com.br
PORT=1521
SID=orcl

# (Opcional) Para Modo Thick:
# INSTANT_CLIENT=C:\instantclient-basic-windows.x64-23.9.0.25.07\instantclient_23_9
```

- Se `INSTANT_CLIENT` **não** for definido, o driver usa **Modo Thin** (não precisa instalar o Instant Client).
- Em **Windows**, se usar Thick, confirme o caminho correto do Instant Client.
- Não exponha o `.env` publicamente.

---

## 📦 `requirements.txt`

```txt
oracledb
python-dotenv
requests
pandas
```

- `oracledb` — driver oficial Oracle para Python (Thin/Thick)
- `python-dotenv` — leitura do `.env`
- `requests` — consumo da API ViaCEP
- `pandas` — apoio a listagens/exportações (opcional, mas útil)

Instalação:

```bash
pip install -r requirements.txt
```

---

## 🧭 Fluxo típico de uso

1. `python quick_check.py` — validar conexão e driver  
2. `python src/create_tables.py` — criar tabelas  
3. `python src/seed_data.py` — popular (opcional, idempotente)  
4. `python src/hs_app.py` — navegar pelos menus e testar CRUD / export / ViaCEP  
5. `python src/drop_tables.py` — limpar ambiente (opcional)

---

## 🖥️ (Opcional) Como seria um **Front‑End** para apresentar o projeto

Para uma apresentação visual, poderíamos expor uma **API REST** em Python (ex.: **FastAPI**/**Flask**) por cima da lógica atual e construir um **front React** (ou outro).

**Possível API (exemplos):**
- `GET /api/pacientes` — lista pacientes
- `POST /api/pacientes` — cria paciente
- `PUT /api/pacientes/{id}` — atualiza paciente
- `DELETE /api/pacientes/{id}` — remove paciente (bloquear se houver teleconsulta)
- `GET /api/teleconsultas` — lista teleconsultas (filtros: paciente_id, status)
- `POST /api/teleconsultas` — cria teleconsulta
- `PATCH /api/teleconsultas/{id}/concluir` — conclui sessão
- `GET /api/export/pacientes|teleconsultas|join` — baixa JSON
- `GET /api/cep/{cep}` — proxy para ViaCEP

**Front (ex.: React + Vite + TS + Tailwind):**
- **Pacientes:** tabela + modal/cadastro/edição; busca por nome/telefone; indicador de “Alta”
- **Teleconsultas:** tabela, filtros (status, urgência), criação/edição, ação “Concluir” (adiciona orientações)
- **Exportações:** botões “Baixar JSON”
- **CEP:** campo para consultar e auto-preencher endereço (se aplicável)

Isso manteria a **mesma regra de negócio** do console, apenas com uma **camada HTTP** para integração visual.

---

## 🧩 Dicas e Troubleshooting

- `ORA-01017: invalid username/password` → revise `USER/PASSWORD` no `.env`
- `ORA-12541: TNS:no listener` / timeout → revise `HOST/PORT/SID` e conectividade de rede
- `DPI-1047: Cannot locate a 64-bit Oracle Client` → você pediu Modo Thick (tem `INSTANT_CLIENT`) mas o caminho é inválido; ajuste o `.env` **ou** remova a variável para usar Modo Thin
- `PermissionError` em Windows ao ativar venv → abra PowerShell **como administrador** e rode:
  ```powershell
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
  ```

---

## 📚 Licença
Uso acadêmico – FIAP · HealthSync • 2025.
