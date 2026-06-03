# GrantFlow v2 — Módulo Organizaciones (Opción B: Seed + Apollo.io)

## Estrategia Arquitectónica

**NO hacemos web scraping** de fundaciones (frágil + mantenimiento alto).

**SÍ hacemos:**
1. **Seed manual:** Importar 23 financiadores históricos aeioTU a `funders` table
2. **Apollo.io enriquecimiento:** POST request a `/api/v1/organizations/{id}/enrich` busca contactos verificados
3. **Workflow:** Crear org → Apollo verifica emails → Crea contactos con role_category

---

## Paso 1: Cargar 23 Financiadores Históricos

### Opción A: Script automático
```bash
cd backend
python -m app.scrapers.seed_organizations --load
```

**Qué hace:**
- Lee 23 fundadores de `STRATEGIC_FUNDERS` en `seed_organizations.py`
- Inserta en tabla `funders` con campos v2 (access_type, strategic_obj, invests_colombia, etc.)
- Evita duplicados

**Resultado:**
```
INFO: Added funder: LEGO Foundation
INFO: Added funder: Grand Challenges Canada
...
INFO: Organizations seed complete, total=23
```

### Opción B: Manual via API
```bash
curl -X POST http://localhost:8000/api/v1/organizations \
  -H "Content-Type: application/json" \
  -d '{
    "name": "LEGO Foundation",
    "country": "Denmark",
    "org_type": "Filantropía",
    "website": "https://www.legoforumdation.com",
    "access_type": "convocatoria",
    "strategic_obj": "exportacion_modelo",
    "invests_colombia": true,
    "invests_latam": true,
    "aeiotu_role": "financiador",
    "general_objective": "Innovación y escalabilidad en educación inicial"
  }'
```

---

## Paso 2: Enriquecer Organización con Contactos (Apollo.io)

### Endpoint
```bash
POST /api/v1/organizations/{org_id}/enrich
```

### Ejemplo
```bash
# 1. Obtener org_id (de la respuesta del seed o GET /api/v1/organizations)
ORG_ID="550e8400-e29b-41d4-a716-446655440000"

# 2. Llamar endpoint de enriquecimiento
curl -X POST http://localhost:8000/api/v1/organizations/$ORG_ID/enrich

# Respuesta:
{
  "status": "success",
  "org_id": "550e8400-e29b-41d4-a716-446655440000",
  "org_name": "LEGO Foundation",
  "contacts_found": 8,
  "contacts": [
    {
      "name": "John Smith",
      "email": "john.smith@lego.com",
      "title": "Director of Partnerships",
      "role_category": "partnerships"
    },
    {
      "name": "Jane Doe",
      "email": "jane.doe@lego.com",
      "title": "Grants Manager",
      "role_category": "grants"
    },
    ...
  ]
}
```

### Qué hace:
1. Toma el nombre de la organización
2. Busca en Apollo.io por personas asociadas a esa empresa
3. **Infiere role_category** del título:
   - `"partnerships"` → Partnership Manager, Strategic Director, Alliance Officer
   - `"grants"` → Grants Manager, Funding Officer, Head of Grants
   - `"cooperation"` → Cooperation Officer, International Specialist
   - `"innovation"` → Innovation Manager, R&D, Tech Officer
   - `"development"` → Program Officer, Development Director, CSR Manager
4. Crea registros en tabla `contacts` con:
   - full_name, email, title, linkedin_url (si disponible)
   - role_category (inferido)
   - aeiotu_connection = False (usuario puede cambiar después)
   - source = "apollo"

---

## Paso 3: Ver Organizaciones + Contactos

### Listar organizaciones
```bash
GET /api/v1/organizations?page=1&size=25&country=Colombia&invests_colombia=true
```

Parámetros opcionales:
- `org_type`: Filantropía, ONG, Multilateral, Público, Privado, Banco, Cooperación, Tercer sector
- `country`: país
- `invests_colombia`: true|false
- `invests_latam`: true|false
- `access_type`: convocatoria, mixto, relacional, invitacion

### Detalle de organización + contactos
```bash
GET /api/v1/organizations/{org_id}
```

Respuesta:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "LEGO Foundation",
  "country": "Denmark",
  "org_type": "Filantropía",
  "website": "https://www.legoforumdation.com",
  "access_type": "convocatoria",
  "strategic_obj": "exportacion_modelo",
  "invests_colombia": true,
  "invests_latam": true,
  "aeiotu_role": "financiador",
  "general_objective": "Innovación y escalabilidad en educación inicial",
  "has_history": true,
  "created_at": "2026-06-02T10:30:00Z",
  "contacts": [
    {
      "id": "...",
      "full_name": "John Smith",
      "title": "Director of Partnerships",
      "email": "john.smith@lego.com",
      "linkedin_url": "https://linkedin.com/in/johnsmith",
      "role_category": "partnerships"
    },
    ...
  ]
}
```

### Exportar a CSV
```bash
GET /api/v1/organizations/export/csv?country=Colombia
```

Devuelve:
```
{
  "filename": "organizations.csv",
  "content_base64": "SWQsIE5vbWJyZSwgVGlwbyxB..."
}
```

---

## Paso 4: Listar Contactos (con filtros)

### Por organización
```bash
GET /api/v1/contacts?funder_id={org_id}
```

### Por rol
```bash
GET /api/v1/contacts?role_category=grants
```

### Exportar contactos
```bash
GET /api/v1/contacts/export/csv?role_category=partnerships
```

---

## Flujo Completo: De cero a producción

### Dev environment
```bash
# 1. Ejecutar migraciones (v2 BD schema)
cd backend
alembic upgrade head

# 2. Cargar 23 financiadores
python -m app.scrapers.seed_organizations --load

# 3. Enriquecer 3 organizaciones de prueba
curl -X POST http://localhost:8000/api/v1/organizations/{id1}/enrich
curl -X POST http://localhost:8000/api/v1/organizations/{id2}/enrich
curl -X POST http://localhost:8000/api/v1/organizations/{id3}/enrich

# 4. Validar en OpenAPI Swagger
# http://localhost:8000/docs → POST /organizations/{id}/enrich
```

### Producción
```bash
# 1. Asegurar que SUPABASE_URL y APOLLO_API_KEY están en .env
# 2. Ejecutar migraciones (via Alembic o SQL directamente en Supabase)
# 3. Seed: ejecutar script una sola vez
# 4. Workflow operativo:
#    - Equipo agrega nuevas orgs via POST /organizations
#    - N8n workflow semanal: GET /organizations sin contactos → POST /{id}/enrich
#    - Contactos aparecen automáticamente en dashboard
```

---

## Limitaciones + Próximos Pasos

### Limitaciones Opción B:
- ⚠️ Datos no se actualizan automáticamente (requiere API call)
- ⚠️ Dependencia de Apollo.io (requiere API key + cuota)
- ⚠️ Algunos contactos pueden no encontrarse (Apollo tiene coverage variable)

### Próximos pasos (Fase 2.1):
- **Web scraping selectivo** para 3 fundaciones clave donde sabemos publican equipo:
  - LEGO Foundation: sitio muy actualizado
  - Grand Challenges Canada: directorio público
  - Cargill: página de contactos
- Usar esta data como **fallback** si Apollo no encuentra personas
- Mantener seed manual como **fuente de verdad** principal

---

## API Reference

### Endpoints disponibles

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/v1/organizations` | Listar con filtros |
| GET | `/api/v1/organizations/{id}` | Detalle + contactos |
| POST | `/api/v1/organizations` | Crear manual |
| PATCH | `/api/v1/organizations/{id}` | Actualizar |
| POST | `/api/v1/organizations/{id}/enrich` | Llamar Apollo.io |
| GET | `/api/v1/organizations/export/csv` | Exportar CSV |
| GET | `/api/v1/contacts` | Listar contactos |
| GET | `/api/v1/contacts/export/csv` | Exportar contactos CSV |

---

## Testing

### Unit test: seed
```bash
python -c "
from app.scrapers.seed_organizations import STRATEGIC_FUNDERS
print(f'Seed data: {len(STRATEGIC_FUNDERS)} funders')
assert len(STRATEGIC_FUNDERS) == 23, 'Expected 23'
"
```

### E2E: seed + API + Apollo
```bash
# 1. Cargar seed
python -m app.scrapers.seed_organizations --load

# 2. Listar orgs
curl http://localhost:8000/api/v1/organizations?size=5

# 3. Enriquecer 1 org
curl -X POST http://localhost:8000/api/v1/organizations/{id}/enrich

# 4. Verificar contactos creados
curl http://localhost:8000/api/v1/contacts?funder_id={id}
```

---

*Última actualización: 2 junio 2026*
