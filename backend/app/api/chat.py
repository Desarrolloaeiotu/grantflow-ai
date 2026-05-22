import json
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import anthropic
import structlog

from app.core.database import get_db
from app.models.opportunity import Opportunity
from app.models.funder import Funder
from app.services.rag_pipeline import RAGPipeline

logger = structlog.get_logger()
router = APIRouter()

client = anthropic.AsyncAnthropic()

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []

class ChatResponse(BaseModel):
    reply: str

SYSTEM_PROMPT = """Eres GrantFlow Asistente, el agente de aeioTU para prospección estratégica de oportunidades de financiamiento.

ROL: Apoyas a la Gerencia de Alianzas en la búsqueda y análisis de oportunidades. Tienes acceso al pipeline activo, historial de financiadores y lecciones aprendidas de 17 años de aeioTU.

CONTEXTO INSTITUCIONAL:
- 17 años trabajando en educación inicial (ECD) en Colombia
- 2.3 millones de niños alcanzados, 98.000 docentes formados
- 23 financiadores únicos (2018-2025): $45.048M acumulados
- Top: LEGO Foundation, Grand Challenges Canada, Fundación Hilton, Fundación Cargill, BID

CAPACIDADES:
1. Consultar el pipeline de oportunidades (GO, pending, no_go)
2. Buscar información de financiadores y su historial
3. Recuperar lecciones aprendidas de proyectos pasados
4. Generar borradores de propuestas para oportunidades específicas

RESTRICCIONES:
- Responde SIEMPRE en español
- Máximo 3 párrafos por respuesta
- Si no hay datos, dilo explícitamente
- Usa listas cuando haya 3+ items

Utiliza las herramientas disponibles para ayudar al usuario de manera precisa y contextualizada."""

TOOLS = [
    {
        "name": "get_opportunities",
        "description": "Obtiene oportunidades del pipeline con filtros opcionales",
        "input_schema": {
            "type": "object",
            "properties": {
                "decision": {
                    "type": "string",
                    "enum": ["go", "no_go", "pending"],
                    "description": "Filtrar por decisión"
                },
                "window": {
                    "type": "string",
                    "description": "Ventana de mercado"
                },
                "limit": {
                    "type": "integer",
                    "default": 10,
                    "description": "Cantidad de resultados"
                }
            },
            "required": []
        }
    },
    {
        "name": "search_funders",
        "description": "Busca financiadores por nombre o historial",
        "input_schema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Nombre del financiador"
                },
                "has_history": {
                    "type": "boolean",
                    "description": "Solo financiadores con historial en aeioTU"
                }
            },
            "required": ["name"]
        }
    },
    {
        "name": "search_knowledge",
        "description": "Busca en la base de conocimiento (lecciones aprendidas, propuestas exitosas)",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Tema a buscar"
                },
                "top_k": {
                    "type": "integer",
                    "default": 5,
                    "description": "Número de resultados"
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "generate_proposal",
        "description": "Genera un borrador de propuesta para una oportunidad",
        "input_schema": {
            "type": "object",
            "properties": {
                "opportunity_id": {
                    "type": "string",
                    "description": "ID de la oportunidad"
                },
                "opportunity_title": {
                    "type": "string",
                    "description": "Título de la oportunidad"
                },
                "opportunity_description": {
                    "type": "string",
                    "description": "Descripción de la oportunidad"
                }
            },
            "required": ["opportunity_title"]
        }
    }
]

async def call_tool(tool_name: str, tool_input: dict, db: AsyncSession):
    """Ejecuta una herramienta y retorna el resultado."""

    if tool_name == "get_opportunities":
        decision = tool_input.get("decision")
        window = tool_input.get("window")
        limit = tool_input.get("limit", 10)

        query = select(Opportunity)
        if decision:
            query = query.where(Opportunity.decision == decision)
        if window:
            query = query.where(Opportunity.market_window == window)

        query = query.order_by(Opportunity.score_total.desc()).limit(limit)
        rows = (await db.execute(query)).scalars().all()

        return {
            "count": len(rows),
            "opportunities": [
                {
                    "id": str(o.id),
                    "title": o.title[:100],
                    "funder": o.funder_id,
                    "score": o.score_total,
                    "decision": o.decision,
                    "deadline": o.deadline.isoformat() if o.deadline else None,
                }
                for o in rows
            ]
        }

    elif tool_name == "search_funders":
        name = tool_input.get("name")
        has_history = tool_input.get("has_history", False)

        query = select(Funder)
        if name:
            query = query.where(Funder.name.ilike(f"%{name}%"))
        if has_history:
            query = query.where(Funder.has_history == True)

        rows = (await db.execute(query)).scalars().all()

        return {
            "count": len(rows),
            "funders": [
                {
                    "name": f.name,
                    "country": f.country,
                    "has_history": f.has_history,
                    "ticket_range": f"{f.ticket_min_usd} - {f.ticket_max_usd} USD" if f.ticket_min_usd else "No definido"
                }
                for f in rows
            ]
        }

    elif tool_name == "search_knowledge":
        query = tool_input.get("query")
        top_k = tool_input.get("top_k", 5)

        rag = RAGPipeline(db)
        results = await rag.query(query, top_k=top_k)

        return {
            "query": query,
            "results_found": len(results),
            "results": results[:top_k] if results else []
        }

    elif tool_name == "generate_proposal":
        title = tool_input.get("opportunity_title", "")
        desc = tool_input.get("opportunity_description", "")

        # Claude va a generar un borrador en el siguiente turno
        return {
            "status": "ready",
            "opportunity": title,
            "instruction": "Se generará un borrador de propuesta en la siguiente respuesta"
        }

    return {"error": f"Herramienta desconocida: {tool_name}"}

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db)) -> ChatResponse:
    """Chat endpoint que orquesta con Claude API."""

    messages = [
        {"role": msg.role, "content": msg.content}
        for msg in request.history
    ]
    messages.append({"role": "user", "content": request.message})

    # Loop de agentic reasoning
    for _ in range(5):  # Max 5 iteraciones para evitar bucles infinitos
        response = await client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )

        # Verificar si Claude quiere usar herramientas
        if response.stop_reason == "tool_use":
            # Procesar tool_use blocks
            assistant_message = {"role": "assistant", "content": response.content}
            messages.append(assistant_message)

            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    tool_result = await call_tool(block.name, block.input, db)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": json.dumps(tool_result)
                    })

            # Agregar resultados de herramientas
            if tool_results:
                messages.append({"role": "user", "content": tool_results})
        else:
            # Claude terminó, extraer la respuesta
            reply = ""
            for block in response.content:
                if hasattr(block, "text"):
                    reply = block.text
                    break

            logger.info("Chat completed", user_message=request.message, reply=reply[:100])
            return ChatResponse(reply=reply)

    return ChatResponse(reply="No pude procesar tu solicitud. Intenta de nuevo con una pregunta más específica.")
