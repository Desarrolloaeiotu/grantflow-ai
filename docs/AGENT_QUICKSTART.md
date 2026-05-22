# GrantFlow Asistente — Guía Rápida de Uso

> Para usuarios del dashboard de GrantFlow AI  
> Mayo 2026

---

## 🎯 ¿Qué es GrantFlow Asistente?

Es un **asistente conversacional con IA** integrado en el dashboard que te ayuda a:
- 📊 Consultar oportunidades de financiamiento
- 🔍 Buscar información de financiadores
- 📚 Recuperar lecciones aprendidas
- ✉️ Verificar contactos
- 💡 Generar borradores de propuestas

---

## 🚀 Cómo Empezar

### 1. Abre el Dashboard
```
http://localhost:3001
```

### 2. Busca el Botón 💬
Está en la **esquina inferior derecha** de la pantalla.

### 3. Haz Clic para Abrir el Panel
El panel se desliza desde la derecha. Escriba tu pregunta en el input de abajo.

### 4. Presiona Enter o Haz Clic en →
El asistente responderá en segundos.

---

## 💬 Ejemplos de Preguntas

### Consultar Oportunidades
```
"¿Qué oportunidades GO tenemos?"
"¿Qué vence esta semana?"
"Muéstrame oportunidades con score ≥ 7"
"¿Cuántas oportunidades PENDING hay?"
```

### Buscar Financiadores
```
"¿Tenemos historial con LEGO?"
"¿Cuál es el ticket mínimo de Fundación Hilton?"
"¿Quiénes son nuestros top 5 financiadores?"
"¿Tiene historia con nosotros la Fundación Cargill?"
```

### Lecciones Aprendidas
```
"¿Qué aprendimos de proyectos con BID?"
"¿Hay propuestas exitosas en zonas rurales?"
"¿Qué funcionó bien en el proyecto con LEGO?"
"Necesito referencias de formación docente"
```

### Verificar Contactos
```
"¿El email de Juan es válido?"
"Verifica este contacto: ceo@fundacion.org"
```

### Generar Propuestas
```
"Genera una propuesta para LEGO Foundation"
"Crea un borrador de propuesta para la oportunidad de MinEducación"
```

---

## 📎 Cargar Archivos

1. Haz clic en el botón **📎** (entre el input y el botón de envío)
2. Selecciona un archivo (PDF, DOC, DOCX, TXT, XLSX)
3. El asistente confirma que recibió el archivo
4. Puedes hacer preguntas sobre el contenido

> **Nota:** El procesamiento completo de documentos está en desarrollo.

---

## ⌨️ Atajos de Teclado

| Atajo | Acción |
|-------|--------|
| `Enter` | Envía el mensaje |
| `Ctrl+Shift+R` | Recarga el navegador (si algo no funciona) |

---

## 🎨 Interfaz

```
┌─────────────────────────────────┐
│  GrantFlow Asistente        [×] │  ← Título y botón cerrar
├─────────────────────────────────┤
│                                 │
│  Bienvenida inicial o           │
│  historial de conversación      │
│                                 │
│                                 │
│  💬 Mensajes del asistente      │  ← Burbujas grises a la izquierda
│                                 │
│                                 │
│                    Tus mensajes 💭  ← Burbujas verdes a la derecha
│                                 │
├─────────────────────────────────┤
│ [Escribe tu pregunta...] [📎][→]│  ← Input + Cargar archivo + Enviar
└─────────────────────────────────┘
```

---

## ⚡ Consejos

1. **Sé específico:** En lugar de "¿Oportunidades?", pregunta "¿Qué oportunidades GO vencen en junio?"

2. **Contextualiza:** El asistente entiende español, así que puedes escribir en tu idioma natural.

3. **Combina preguntas:** Puedes hacer múltiples preguntas en una sesión. El asistente recuerda el contexto.

4. **Revisa respuestas:** Las respuestas pueden ser largas. Scrollea para ver todo.

5. **Cierra el panel:** Haz clic en el X arriba a la derecha o en el botón 💬 de nuevo.

---

## ❓ Preguntas Frecuentes

### P: ¿Es seguro usar el asistente?
**R:** Sí. El asistente solo accede a datos públicos del pipeline de GrantFlow. No comparte información confidencial sin tu consentimiento.

### P: ¿Qué pasa si hago una pregunta que no entiende?
**R:** El asistente responderá honestamente: *"No tengo información sobre eso en el sistema."*

### P: ¿Funciona sin internet?
**R:** No. Necesita conexión a internet para comunicarse con el servidor.

### P: ¿Los mensajes se guardan?
**R:** Actualmente no. Cada sesión es independiente. En producción habrá historial persistente.

### P: ¿Puedo pedirle que genere una propuesta completa?
**R:** Sí, pero por ahora genera borradores. En la próxima versión serán más completos (incluirán presupuesto, timeline, etc.).

---

## 🚨 Si Algo Falla

### El botón 💬 no aparece
- [ ] Recarga la página: `Ctrl+Shift+R`
- [ ] Cierra el navegador y reabre
- [ ] Verifica que el frontend esté corriendo en `http://localhost:3001`

### El asistente dice "Error: Backend error"
- [ ] El backend podría no estar corriendo
- [ ] Pide a un administrador que verifique que `python -m uvicorn main:app` esté ejecutando

### Las respuestas son lentas
- [ ] Espera un poco (Claude API puede tardar 2-5 segundos)
- [ ] Intenta una pregunta más simple
- [ ] Verifica tu conexión a internet

---

## 📞 Soporte

Si encuentras problemas:
1. Revisa esta guía
2. Consulta la documentación técnica: `docs/AGENT_INTEGRATION.md`
3. Contacta al equipo de desarrollo

---

**Versión:** 1.0  
**Última actualización:** Mayo 21, 2026  
**Estado:** En producción local (requiere ANTHROPIC_API_KEY)
