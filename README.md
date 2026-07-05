# Social Platform Transparency Dashboard

Aplicação web para comparar Meta, TikTok e YouTube com base exclusivamente em dados oficiais publicados pelas próprias plataformas.

## Regras de dados

- Só entram dados oficiais.
- Se a métrica não existir na fonte oficial, o sistema exibe: `Não divulgado oficialmente.`
- As fontes priorizam CSV, JSON e APIs oficiais.
- Scraping só deve ser usado quando não houver alternativa estruturada.

## Stack

- Frontend: Next.js, React, TypeScript, TailwindCSS, Recharts
- Backend: FastAPI, SQLAlchemy, APScheduler
- Banco: SQLite
- Exportação: PDF, Excel, CSV
- Infra: Docker, Docker Compose, GitHub Actions

## Estrutura

- `backend/` - API, modelos, crawlers, exportação e scheduler
- `frontend/` - dashboard web
- `database/` - SQLite local e cache de coleta
- `crawler/` - espaço para extensões de coleta
- `reports/` - relatórios exportados
- `charts/` - artefatos gráficos
- `api/` - artefatos e contratos de integração

## Execução local

### Um comando para subir tudo

```bash
make dev
```

Esse comando:

- sobe backend e frontend localmente usando o virtualenv e o Node já instalados no repositório;
- espera o backend ficar saudável;
- executa a primeira coleta oficial automaticamente;
- entrega o frontend já apontando para o backend.

Se você preferir Docker, use:

```bash
make dev-docker
```

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker

```bash
docker compose up --build
```

Se você quiser parar a stack:

```bash
make down
```

## Endpoints

- `GET /health`
- `GET /dashboard/summary`
- `GET /metrics`
- `GET /reports`
- `GET /indicators`
- `GET /comparison`
- `POST /refresh`
- `GET /export/pdf`
- `GET /export/excel`
- `GET /export/csv`

## Notas de implementação

O backend foi preparado para:

- descobrir links oficiais nas páginas de transparência;
- baixar CSV, JSON, XLSX e páginas HTML oficiais;
- gravar plataformas, fontes, relatórios, métricas e indicadores em SQLite;
- calcular índices automáticos de transparência, LGPD e ECA Digital;
- agendar atualização periódica via APScheduler.

O frontend foi preparado para:

- tema claro e escuro;
- navegação por páginas;
- filtros de comparação;
- gráficos responsivos;
- exibição de estados vazios sem fabricar números.

## Próximos passos

1. Rodar `make dev`.
2. Abrir http://localhost:3000.
3. Se quiser forçar nova coleta manualmente, usar `make refresh`.
