# Apollo.io Integration — Sprint S5

## Endpoints Implementados

### 1. **POST /api/v1/contacts/verify**
Verifica un email individual vía Apollo.io.

```bash
curl -X POST http://localhost:8000/api/v1/contacts/verify \
  -H "Content-Type: application/json" \
  -d '{
    "email": "ceo@fundacion.org",
    "name": "John Doe"
  }'
```

**Response:**
```json
{
  "verified": true,
  "confidence": "high",
  "email": "ceo@fundacion.org",
  "first_name": "John",
  "last_name": "Doe",
  "title": "Executive Director",
  "linkedin_url": "https://linkedin.com/in/johndoe",
  "company": "Fundación XYZ",
  "raw_response": { ... }
}
```

---

### 2. **POST /api/v1/contacts/enrich**
Busca contactos en una organización financiadora.

```bash
curl -X POST "http://localhost:8000/api/v1/contacts/enrich?funder_id={uuid}&limit=10"
```

**Response:**
```json
{
  "status": "success",
  "funder_id": "550e8400-e29b-41d4-a716-446655440000",
  "funder_name": "LEGO Foundation",
  "contacts_found": 3,
  "contacts": [
    {
      "email": "ceo@legofoundation.org",
      "first_name": "Rasmus",
      "last_name": "Nyrup",
      "title": "CEO",
      "linkedin_url": "https://linkedin.com/in/rasmusnyrup",
      "company": "LEGO Foundation",
      "verified": true
    }
    // ... más contactos
  ]
}
```

---

### 3. **POST /api/v1/opportunities/{id}/enrich-contacts**
Enriquece una oportunidad específica con datos de contacto.

```bash
curl -X POST "http://localhost:8000/api/v1/opportunities/{opportunity_id}/enrich-contacts"
```

**Response:**
```json
{
  "opportunity_id": "550e8400-e29b-41d4-a716-446655440001",
  "status": "success",
  "enhancements": [
    "org_email_verified",
    "ceo_email_verified",
    "ceo_name_enriched",
    "ceo_title_enriched"
  ],
  "enhancements_count": 4
}
```

---

## Integración con n8n

### Flujo recomendado: `enrich-on-scoring`

Después de que una oportunidad es **scored** (cuando `score_total` se asigna):

1. **Trigger:** Schedule o HTTP POST (cuando se ejecuta `/api/v1/scoring/{opp_id}`)
2. **Nodo 1:** Fetch opportunity de la DB
3. **Nodo 2:** IF `decision == 'go'` → continúe
4. **Nodo 3:** HTTP POST a `/api/v1/opportunities/{id}/enrich-contacts`
5. **Nodo 4:** Slack notification: "✅ Opp enriquecida: {ceo_name} ({ceo_email})"

### Configuración en n8n:

```javascript
// En el nodo HTTP que llama enrich-contacts:
{
  method: "POST",
  url: "http://host.docker.internal:8000/api/v1/opportunities/{{$json.id}}/enrich-contacts",
  authentication: "none",
  headers: {
    "Content-Type": "application/json"
  },
  returnFullResponse: true
}
```

---

## Requisitos

### Activación de Apollo.io (Mes 5+)

1. **Obtén API Key de Apollo.io:**
   - Ir a https://app.apollo.io/settings/api
   - Copiar tu `API Key`

2. **Configura en .env:**
   ```bash
   APOLLO_API_KEY=your_api_key_here
   ```

3. **Costos:**
   - Plan Basic: $49/mes → 10k credits/mes (1 email = 1 credit)
   - Con 816 oportunidades: ~$50/mes

4. **Límites de rate:**
   - Apollo.io: 10 requests/min recomendado
   - Backend aplica automáticamente esperas

---

## Esquema de datos actualizado

Las siguientes columnas en `opportunities` se actualizan automáticamente:

| Campo | Tipo | Se actualiza | Verificado por |
|-------|------|---|---|
| `ceo_email` | TEXT | ✅ Si Apollo encuentra | Apollo.io |
| `ceo_email_verified` | BOOL | ✅ Si Apollo confirma | Apollo.io |
| `ceo_email_verified_at` | TIMESTAMPTZ | ✅ Timestamp UTC | Sistema |
| `ceo_name` | TEXT | ✅ Si no existe | Apollo.io |
| `ceo_title` | TEXT | ✅ Si no existe | Apollo.io |
| `ceo_linkedin_url` | TEXT | ✅ Si Apollo proporciona | Apollo.io |
| `org_email_verified` | BOOL | ✅ Si Apollo confirma | Apollo.io |
| `org_email_verified_at` | TIMESTAMPTZ | ✅ Timestamp UTC | Sistema |

---

## Ejemplos de uso

### En Python (backend test):

```python
from app.services.apollo_service import apollo

# Verificar email
result = await apollo.verify_email("ceo@org.com", "John Doe")
print(result["verified"])  # True si Apollo confirmó

# Buscar contactos
people = await apollo.search_people(
    company_name="LEGO Foundation",
    title="CEO",
    limit=5
)
for person in people:
    print(f"{person['first_name']} {person['last_name']} ({person['email']})")
```

### Llamada manual (curl):

```bash
# Enriquecer una oportunidad
OPP_ID="550e8400-e29b-41d4-a716-446655440001"
curl -X POST "http://localhost:8000/api/v1/opportunities/$OPP_ID/enrich-contacts" \
  -H "Content-Type: application/json"

# Verificar resultado
curl -X GET "http://localhost:8000/api/v1/opportunities/$OPP_ID" | jq '.ceo_email_verified'
```

---

## Próximos pasos (S6)

- Dashboard Metabase con visualización de emails verificados
- Reporte automático de oportunidades GO con contactos verificados
- Exportación para CRM con campos de contacto enriquecidos
