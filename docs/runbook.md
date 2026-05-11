# Runbook — GrantFlow AI

## Comandos del día a día

```bash
make dev              # Levanta todo el stack local
make migrate          # Aplica migraciones pendientes
make scrape-all       # Ejecuta todos los scrapers manualmente
make test             # Corre los tests
make logs             # Logs del backend en producción
```

## Levantar el proyecto desde cero

```bash
# 1. Clonar y configurar
git clone <repo>
cd grantflow-ai
cp .env.example .env
# Editar .env con las credenciales reales

# 2. Levantar DB local
docker compose up -d db

# 3. Instalar dependencias backend
cd backend
pip install -e ".[dev]"

# 4. Aplicar migraciones
alembic upgrade head

# 5. Levantar backend
uvicorn main:app --reload

# 6. Frontend (nueva terminal)
cd frontend
npm install
npm run dev
```

## Ejecutar scrapers manualmente

```bash
# Todos
make scrape-all

# Solo Grants.gov
make scrape SOURCE=grantsgov
```

## Resetear base de datos (solo dev)

```bash
make db-reset
```

## Backup de base de datos

```bash
make db-backup
# Genera: backup_YYYYMMDD_HHMMSS.sql
```

## Verificar salud del sistema

```bash
curl http://localhost:8000/health
# Respuesta esperada: {"status": "ok", "version": "0.1.0"}
```

## Troubleshooting

### "pgvector extension not found"
Asegúrate de usar la imagen `pgvector/pgvector:pg16` en Docker, no `postgres:16` estándar.

### "ANTHROPIC_API_KEY not set"
Los criterios C1 y C2 del scoring usan el LLM. Sin la key, se puntúan con 0. Configurar en `.env`.

### n8n no conecta con el backend
En Docker, usar `host.docker.internal:8000` en lugar de `localhost:8000` en los workflows de n8n.
