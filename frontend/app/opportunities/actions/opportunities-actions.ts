'use server'

import { revalidatePath } from 'next/cache'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface ActionResult {
  success: boolean
  error?: string
}

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

    revalidatePath('/')
    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

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

    revalidatePath('/')
    return { success: true }
  } catch (error) {
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}
