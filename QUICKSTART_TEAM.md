# GrantFlow AI — Guía Rápida para Alianzas

**Para:** Equipo de Alianzas Internacionales  
**Fecha:** 12 mayo 2026  
**Sistema:** GrantFlow AI — Inteligencia comercial para prospección de grants

---

## 🚀 Cómo Acceder

### Dashboard Web
```
URL: http://localhost:3000
Usuario: No requiere credenciales (MVP)
```

**¿Qué ves?**
- Grid visual de **816 oportunidades detectadas**
- Filtros para encontrar lo que necesitas
- Información de CEO y organización
- Links directos a convocatorias y LinkedIn

---

## 🔍 Cómo Usar el Dashboard

### 1. Ver todas las oportunidades GO
1. Haz clic en el filtro **"GO"**
2. Veras **5 oportunidades** ya calificadas como viables
3. Score promedio: **7.8/10**

### 2. Filtrar por ventana de mercado
- **Funding Colombia:** 5 opp (gobierno, cajas, sector privado colombiano)
- **Funding Global:** 38 opp (fundaciones internacionales)
- **Estratégicas:** 5 opp (redes, coaliciones ECD)

Haz clic en cada ventana para enfocarte.

### 3. Buscar una oportunidad específica
Usa la barra de búsqueda arriba:
- Busca por nombre de financiador
- Busca por tema (ej: "educación inicial")
- Busca por país

---

## 👤 Información de Contactos

Cada oportunidad muestra:

### Organización
- **Email verificado:** 🟢 Verde = verificado | 🟡 Amarillo = pendiente
- **Sitio web:** Click directo a su página

### CEO / Representante
- **Nombre:** Obtenido automáticamente
- **Cargo:** Title/posición
- **Email:** Click para enviar correo
- **LinkedIn:** Click para ver perfil

**Nota:** Emails sin verificar aparecen con ⚠️. En Mes 5 activaremos verificación real vía Apollo.io.

---

## 🎯 Caso de Uso: Prospección

### Paso 1: Encontrar oportunidades GO
```
1. Filtro: Decisión = "GO"
2. Filtro: Ventana = "Funding Global" (o tu preferida)
3. Ver las 5 opciones disponibles
```

### Paso 2: Revisar información de contacto
```
1. Abre la tarjeta de oportunidad
2. Busca "CEO / Representante"
3. Si hay email: Click en "Contactar CEO"
4. Se abre tu cliente de email con asunto pre-llenado
```

### Paso 3: Acceder a documentos de la convocatoria
```
1. Haz clic en "Ver convocatoria" (↗ link)
2. Se abre directamente en la fuente (Grants.gov, BID, ONU, etc.)
```

---

## 📊 Interpretación de Scores

**Score total (0-10):**
- **9-10:** Alineación perfecta, viabilidad garantizada
- **7-8:** Muy buena oportunidad, perseguir
- **6-7:** Buena oportunidad, evaluar
- **4-5:** Pendiente revisión más profunda
- **0-3:** No recomendado en este momento

### Criterios de scoring (C1-C5):
- **C1 — Alineación estratégica:** ¿Es educación inicial?
- **C2 — Ajuste modelo:** ¿Busca modelos escalables?
- **C3 — Coherencia ticket:** ¿El monto es viable para aeioTU?
- **C4 — Viabilidad operativa:** ¿Tiempo suficiente para aplicar?
- **C5 — Potencial relacional:** ¿Financiador estratégico?

Cada criterio vale **máximo 2 puntos**. **GO si total ≥ 6**.

---

## ⚡ Filtros Disponibles

| Filtro | Valores | Para qué |
|--------|---------|----------|
| **Decisión** | GO, Pending, No-Go, Todas | Ver opp por etapa de evaluación |
| **Ventana** | Colombia, Global, LATAM, Estratégicas | Segmentar por mercado |
| **Urgencia** | Urgente, Media | Priorizar por cierre próximo |
| **Score** | ≥6, ≥8 | Ver solo opciones calificadas |

---

## 📞 Contactar

### Enviando emails directamente
1. Abre una tarjeta de oportunidad
2. Busca el email del CEO
3. Haz clic en "Contactar CEO"
4. Se abre con:
   - **Para:** Email del CEO
   - **Asunto:** "Oportunidad [nombre] - aeioTU"
   - **Cuerpo:** Escribe tu mensaje

### Copiando información
Cada campo es copiable — click y copia para llevar a Excel, CRM, etc.

---

## 🔄 Cómo se Actualiza la Información

| Fuente | Frecuencia | Qué obtiene |
|--------|-----------|-----------|
| **Grants.gov** | Diario 6am | Grants federales US |
| **BID** | Diario 7am | Oportunidades multilaterales |
| **ONU Mujeres** | Diario 8am | Programas de género |
| **DevelopmentAid** | Diario 9am | Cooperación internacional |
| **RSS feeds** | Diario 10am | Actualizaciones en vivo |

→ Sistema automático. Tú solo abres y explores lo nuevo cada día.

---

## ❓ Preguntas Frecuentes

### ¿Por qué algunos CEOs no tienen email?
Aún no se verificaron. En **Mes 5** activaremos Apollo.io para encontrar y verificar todos automáticamente.

### ¿Puedo exportar esto a Excel?
**Próximamente en S6.** Por ahora, copia/pega las tarjetas o toma screenshots.

### ¿Qué significa "Estratégica"?
Opp sin dinero directo, pero alto valor relacional. Ej: membresía en coalición ECD global.

### ¿Debo aplicar a todas las GO?
**No.** Filtra primero por Ventana (Colombia vs Global) y urgencia. Equipo evalúa cuáles perseguir.

---

## 📅 Próximos pasos (Junio 2026)

- **S6:** Dashboard Metabase con visualizaciones
- **S6:** Exportación CSV para importar a CRM
- **S7:** QA y ajustes basados en feedback del equipo
- **S8:** Onboarding oficial + capacitación

---

## 🎓 Contacto Técnico

Para preguntas técnicas o problemas:
- **Backend:** `http://localhost:8000/docs` (Swagger API docs)
- **Dashboard:** `http://localhost:3000`
- **Logs:** Ver sección de troubleshooting más abajo

---

## 🔧 Troubleshooting

### El dashboard dice "Sin oportunidades"
**Solución:** 
1. Verifica que el filtro "Decisión" no esté en "GO" solamente
2. Cambia a "Todas" para ver todo el pipeline
3. Si aún ves vacío, contacta al equipo técnico

### No veo emails de CEO
**Normal en Mes 1-4.** Se completarán automáticamente en Mes 5 con Apollo.io.

### ¿Por qué algunos scores son "—" (vacío)?
Oportunidades muy nuevas que aún no pasaron por el scoring automático. Se completarán en 5-10 minutos.

---

**¿Preguntas?** Contacta al equipo de desarrollo.
