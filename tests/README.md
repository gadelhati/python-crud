# Testes do Python CRUD

## Organização

- `unit/`: funções, serviços e regras isoladas.
- `integration/`: integração entre API, serviços e persistência.
- `e2e/`: fluxos completos da aplicação.
- `security/`: autenticação, autorização, delegação de privilégios e rate limiting.
- `concurrency/`: disputa entre transações e requisições simultâneas.
- `performance/`: perfil de carga Locust.

## Isolamento do banco

A suíte **não utiliza `UVICORN_DATABASE_URL` nem o `.env` normal**. Antes de importar a aplicação,
`tests/config.py` define `UVICORN_DATABASE_URL` a partir de `PYTEST_DATABASE_URL`.

Padrão local:

```powershell
pytest
```

O padrão é exclusivamente `sqlite:///./db_test.sqlite3`.

PostgreSQL local:

```powershell
$env:PYTEST_DATABASE_URL = "postgresql+psycopg://usuario:senha@localhost:5432/app_test"
pytest
```

O nome do banco PostgreSQL é validado como `app_test`, e o host deve ser `localhost` ou
`127.0.0.1`. Não use banco de desenvolvimento ou produção.

A preparação destrutiva (`drop_all`/`create_all`) ocorre apenas depois dessa validação e somente
no banco de teste dedicado. Cada teste funcional usa uma transação externa e sessões da aplicação
participam por savepoints. O rollback da transação externa desfaz os dados gravados pelas rotas.

Os testes marcados como concorrência usam conexões independentes e fazem limpeza explícita. Os
testes de corrida que exigem semântica transacional do PostgreSQL são ignorados em SQLite.

## Execução por categoria

```powershell
pytest -m unit
pytest -m integration
pytest -m e2e
pytest -m security
pytest -m concurrency
```

Performance é executada com Locust, não como teste funcional comum:

```powershell
pip install -e ".[performance]"
$env:PERF_USERNAME = "usuario_admin_de_teste"
$env:PERF_PASSWORD = "senha"
locust -f tests/performance/locustfile.py --host http://localhost:9000
```

Use apenas ambiente de teste/staging, com dados descartáveis e limites de carga controlados.
Não execute testes de carga contra produção sem autorização e planejamento.

## Observações

- `pytest` executa a suíte funcional completa; testes PostgreSQL-only são ignorados quando o backend
  ativo é SQLite.
- A fixture `client` usa uma transação isolada. `concurrent_client` usa conexões reais e deve ficar
  restrita aos testes de concorrência.
- A suíte usa `create_all` para montar o schema de teste. A validação das migrações Alembic deve
  continuar como etapa separada do CI (`alembic upgrade head` em banco descartável).
