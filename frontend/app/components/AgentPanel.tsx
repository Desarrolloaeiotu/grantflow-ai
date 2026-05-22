'use client'

import { useState, useRef, useEffect } from 'react'

interface Message {
  role: 'user' | 'assistant'
  content: string
}

export default function AgentPanel() {
  const [isOpen, setIsOpen] = useState(false)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleFileClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    const fileName = file.name
    setMessages((prev) => [
      ...prev,
      { role: 'user', content: `📎 Archivo cargado: ${fileName}` },
    ])
    setMessages((prev) => [
      ...prev,
      {
        role: 'assistant',
        content: `He recibido tu archivo: ${fileName}. Puedo ayudarte a procesarlo o responder preguntas sobre su contenido.`,
      },
    ])

    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const handleSend = async () => {
    if (!input.trim() || isLoading) return

    const userMessage = input.trim()
    setInput('')
    setMessages((prev) => [...prev, { role: 'user', content: userMessage }])
    setIsLoading(true)

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userMessage,
          history: messages,
        }),
      })

      if (!res.ok) {
        const error = await res.json()
        setMessages((prev) => [
          ...prev,
          {
            role: 'assistant',
            content: `Error: ${error.error || 'Algo salió mal'}`,
          },
        ])
        return
      }

      const data = await res.json()
      setMessages((prev) => [...prev, { role: 'assistant', content: data.reply }])
    } catch (error) {
      console.error('Chat error:', error)
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          content: 'Error de conexión. Intenta de nuevo.',
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <>
      {/* Floating button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="agent-btn"
        aria-label="Abrir asistente"
      >
        💬
      </button>

      {/* Panel */}
      <div className={`agent-panel ${isOpen ? 'open' : ''}`}>
        {/* Header */}
        <div className="agent-header">
          <h2>GrantFlow Asistente</h2>
          <button
            onClick={() => setIsOpen(false)}
            className="agent-close"
            aria-label="Cerrar"
          >
            ✕
          </button>
        </div>

        {/* Messages */}
        <div className="agent-messages">
          {messages.length === 0 && (
            <div className="agent-welcome">
              <p>Hola, soy GrantFlow Asistente.</p>
              <p>Puedo ayudarte a:</p>
              <ul>
                <li>Consultar oportunidades GO del pipeline</li>
                <li>Buscar historial de financiadores</li>
                <li>Recuperar lecciones aprendidas</li>
                <li>Verificar contactos</li>
              </ul>
              <p>¿En qué te ayudo?</p>
            </div>
          )}
          {messages.map((msg, idx) => (
            <div key={idx} className={`agent-msg ${msg.role}`}>
              <p>{msg.content}</p>
            </div>
          ))}
          {isLoading && (
            <div className="agent-msg assistant">
              <p>Escribiendo...</p>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="agent-input-area">
          <input
            type="text"
            placeholder="Escribe tu pregunta..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
            disabled={isLoading}
            className="agent-input"
          />
          <button
            onClick={handleFileClick}
            disabled={isLoading}
            className="agent-file-btn"
            aria-label="Cargar archivo"
            title="Cargar documento"
          >
            📎
          </button>
          <button
            onClick={handleSend}
            disabled={isLoading || !input.trim()}
            className="agent-send"
            aria-label="Enviar"
          >
            →
          </button>
          <input
            ref={fileInputRef}
            type="file"
            onChange={handleFileChange}
            className="agent-file-input"
            accept=".pdf,.doc,.docx,.txt,.xlsx"
            style={{ display: 'none' }}
          />
        </div>
      </div>
    </>
  )
}
