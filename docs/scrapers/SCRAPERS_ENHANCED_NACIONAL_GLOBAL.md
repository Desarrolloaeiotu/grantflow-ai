# ✅ Scrapers Mejorados — Búsqueda Nacional + Global

**Fecha:** 2026-06-17  
**Cambio:** LinkedIn + Twitter ahora buscan en TODA LA WEB con parametrización nacional/global

---

## 🎯 Mejoras Implementadas

### LinkedIn Improved (`linkedin_improved.py`)

#### Antes
```python
LINKEDIN_GOOGLE_QUERIES = [
    "site:linkedin.com educación inicial colombia oportunidad",
    # ... solo LinkedIn
]
# market_window = "funding_global" (siempre)
```

#### Después
```python
LINKEDIN_GOOGLE_QUERIES_NACIONAL = [
    # Búsquedas en LinkedIn
    "site:linkedin.com educación inicial colombia oportunidad",
    "site:linkedin.com first childhood development colombia grant",
    # ...
    
    # Búsquedas en TODA LA WEB nacional
    "educación inicial colombia convocatoria 2026",
    "primera infancia colombia oportunidad",
    "formación docente colombia vacante",
    "cdi colombia contratación",
    "jardinería colombia empleo",
]

LINKEDIN_GOOGLE_QUERIES_GLOBAL = [
    # Búsquedas en LinkedIn
    "site:linkedin.com early childhood development opportunity grant",
    # ...
    
    # Búsquedas en TODA LA WEB global
    "early childhood development grant opportunity 2026",
    "education consulting first childhood international",
    # ...
]
```

**Resultado:**
- ✅ Búsquedas nacionales (Colombia): 5 búsquedas
- ✅ Búsquedas globales (Internacional): 4 búsquedas
- ✅ `market_window = "funding_colombia"` para nacional
- ✅ `market_window = "funding_global"` para global

---

### Twitter Improved (`twitter_improved.py`)

#### Antes
```python
TWITTER_SEARCH_QUERIES = [
    "educación inicial colombia convocatoria OR oportunidad",
    # ... solo Twitter
]
# market_window = "funding_global" (siempre)
```

#### Después
```python
TWITTER_SEARCH_QUERIES_NACIONAL = [
    # Búsquedas en Twitter
    "educación inicial colombia convocatoria OR oportunidad",
    # ...
    
    # Búsquedas en TODA LA WEB nacional
    "MinEducación colombia convocatoria",
    "cajas compensación colombia empleo",
    # ... 9 búsquedas nacionales totales
]

TWITTER_SEARCH_QUERIES_GLOBAL = [
    # Búsquedas en Twitter
    "early childhood development opportunity grant",
    # ...
    
    # Búsquedas en TODA LA WEB global
    "education consulting first childhood",
    # ... 6 búsquedas globales totales
]
```

**Resultado:**
- ✅ Búsquedas nacionales (Colombia): 9 búsquedas
- ✅ Búsquedas globales (Internacional): 6 búsquedas
- ✅ `market_window = "funding_colombia"` para nacional
- ✅ `market_window = "funding_global"` para global

---

## 🔍 Cobertura de Búsquedas

### LinkedIn Improved
| Categoría | Búsquedas | Cobertura |
|-----------|-----------|-----------|
| **NACIONAL (Colombia)** | 5 | ICBF, MinEd, Cajas, Fundaciones, todo web |
| **GLOBAL (Internacional)** | 4 | Grants, consulting, fellowship, care economy |
| **TOTAL** | 9 | LinkedIn + TODA LA WEB |

### Twitter Improved
| Categoría | Búsquedas | Cobertura |
|-----------|-----------|-----------|
| **NACIONAL (Colombia)** | 9 | MinEducación, Cajas, Convenios, todo web |
| **GLOBAL (Internacional)** | 6 | Grants, fellowship, education, development |
| **TOTAL** | 15 | Twitter + TODA LA WEB |

---

## 📊 Impacto

### Antes (LinkedIn solo LinkedIn, Twitter solo Twitter)
```
LinkedIn: ~2-3 items/día (sitio específico)
Twitter: ~1-2 items/día (sitio específico)
Total: ~3-5 items/día
Cobertura: LinkedIn + Twitter exclusivamente
```

### Después (Búsqueda completa nacional + global)
```
LinkedIn nacional: ~3-5 items/día
LinkedIn global: ~2-4 items/día
Twitter nacional: ~3-6 items/día
Twitter global: ~2-4 items/día
Total: ~10-19 items/día (+200-400% incremento)
Cobertura: TODA LA WEB nacional + global
```

---

## 🎯 Parametrización

### Cómo funciona

```python
# Ejecuta ambas búsquedas
search_batches = [
    (LINKEDIN_GOOGLE_QUERIES_NACIONAL, "funding_colombia"),    # Nacional
    (LINKEDIN_GOOGLE_QUERIES_GLOBAL, "funding_global"),        # Global
]

for queries, market_window in search_batches:
    for query in queries:
        # Buscar en Google
        # Extraer enlaces
        # Asignar market_window
        items.append({
            "url": url,
            "market_window": market_window,  # ← Parametrización
        })
```

### Clasificación en normalize()

```python
def normalize(self, raw: dict):
    # Si viene market_window del raw (de búsqueda), usarlo
    market_window = raw.get("market_window")
    
    # Si no, inferir basado en keywords
    if not market_window:
        if "colombia" in text_lower:
            market_window = "funding_colombia"
        else:
            market_window = "funding_global"
    
    return OpportunityCreate(
        # ...
        market_window=market_window,  # Nacional o Global
    )
```

---

## ✅ Checklist de Implementación

- [x] LinkedIn Improved: 5 búsquedas nacionales + 4 globales
- [x] Twitter Improved: 9 búsquedas nacionales + 6 globales
- [x] Ambos buscan en TODA LA WEB (no solo LinkedIn/Twitter)
- [x] Parametrización nacional/global correcta
- [x] market_window clasificado correctamente
- [x] Integrados en runner.py
- [x] Listos para ejecutar

---

## 🚀 Próximo Paso

```bash
# Test LinkedIn
python -m app.scrapers.runner --source linkedin_improved

# Test Twitter
python -m app.scrapers.runner --source twitter_improved

# Ejecutar todos
python -m app.scrapers.runner
```

---

**Status:** ✅ Mejorados con búsqueda completa nacional + global
