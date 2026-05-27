'use server'

import { revalidatePath } from 'next/cache'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ActionResult {
  success: boolean
  error?: string
}

// Change opportunity status
export async function cambiarEstadoOportunidad(
  opportunityId: string,
  nuevoEstado: 'detected' | 'reviewed' | 'in_crm' | 'cerrada'
): Promise<ActionResult> {
  try {
    const res = await fetch(
      `${API_URL}/api/v1/opportunities/${opportunityId}/status`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status: nuevoEstado }),
      }
    )

    if (!res.ok) {
      return { success: false, error: `HTTP ${res.status}: ${res.statusText}` }
    }

    revalidatePath('/nacional')
    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

// Add note to opportunity
export async function agregarNotaOportunidad(
  opportunityId: string,
  nota: string
): Promise<ActionResult> {
  try {
    const res = await fetch(
      `${API_URL}/api/v1/opportunities/${opportunityId}/notes`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          content: nota,
          created_at: new Date().toISOString(),
        }),
      }
    )

    if (!res.ok) {
      return { success: false, error: `HTTP ${res.status}: ${res.statusText}` }
    }

    revalidatePath('/nacional')
    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

// Mark opportunity as priority
export async function marcarPrioridad(
  opportunityId: string,
  isPriority: boolean
): Promise<ActionResult> {
  try {
    const res = await fetch(
      `${API_URL}/api/v1/opportunities/${opportunityId}/priority`,
      {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_priority: isPriority }),
      }
    )

    if (!res.ok) {
      return { success: false, error: `HTTP ${res.status}: ${res.statusText}` }
    }

    revalidatePath('/nacional')
    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

// Mark contact as contacted
export async function marcarContactado(
  contactId: string,
  tipoInteraccion: 'llamada' | 'email' | 'reunion',
  nota?: string
): Promise<ActionResult> {
  try {
    const res = await fetch(
      `${API_URL}/api/v1/contacts/${contactId}/interaction`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          type: tipoInteraccion,
          note: nota || '',
          timestamp: new Date().toISOString(),
        }),
      }
    )

    if (!res.ok) {
      return { success: false, error: `HTTP ${res.status}: ${res.statusText}` }
    }

    revalidatePath('/nacional')
    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}
