# HealthSync – Sprint 4 (Oracle) – Hospital das Clínicas

Aplicação **console** em Python com **persistência Oracle**, **CRUD** de Pacientes e Teleconsultas, **exportação para JSON** e **integração com API pública (ViaCEP)**.

## O que foi feito
- Integração com Oracle via `oracledb` (modo Thin/Thick com Instant Client opcional).
- CRUD completo de **Pacientes** (cadastrar, listar, atualizar, excluir, conceder alta).
- CRUD completo de **Teleconsultas** (agendar, listar, atualizar, excluir, concluir sessão).
- Regra de negócio: impedir exclusão de Paciente com Teleconsultas vinculadas.
- Exportação para JSON: pacientes, teleconsultas e join paciente x teleconsulta.
- Seed **idempotente** de dados: cria registros exemplo só se não existirem.
- Consumo de API pública (ViaCEP) para consulta de CEP no menu de Integrações.
- Scripts auxiliares para criar/derrubar tabelas, conexão isolada e utilitários.

## Pré-requisitos
- Python 3.11 (recomendado usar venv)
- Oracle acessível (HOST/PORT/SID)
- (Opcional) Oracle Instant Client para Modo Thick
- Dependências: `oracledb`, `python-dotenv`, `requests`, `pandas`

## Instalação
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# ou:
# pip install oracledb python-dotenv requests pandas
```

## Configuração do `.env`
Crie um arquivo `.env` na raiz do projeto (**não versionar** credenciais reais) com:
```
USER=[USUÁRIO_ORACLE]
PASSWORD=[SENHA_ORACLE]
HOST=oracle.fiap.com.br
PORT=1521
SID=orcl
INSTANT_CLIENT=[CAMINHO_DO_INSTANT_CLIENT_OPCIONAL]
```

## Criar Tabelas
```powershell
python src/create_tables.py
```

## Popular dados (Seed idempotente) — opcional
```powershell
python src/seed_data.py
```

## Executar o App (menus)
```powershell
python src/hs_app.py
```

## Exportação de JSON
Arquivos gerados em `exports/`:
- `pacientes.json`
- `teleconsultas.json`
- `teleconsultas_pacientes.json`

## Integração com API pública (ViaCEP)
No menu **Relatórios e Integrações**, escolha **Consultar CEP (ViaCEP)** e informe o CEP no formato `00000000`.

## Observações
- Se usar Modo Thick, confira o caminho do Instant Client no `.env`.
- Para resetar esquema rapidamente: `python src/drop_tables.py` seguido de `python src/create_tables.py`.
- Seed é idempotente: rodar novamente não duplica dados.

## Integrantes
- Maicon Douglas — RM 561279
- Laura Lopes — RM 566376
- Richard Freitas — RM 566127
