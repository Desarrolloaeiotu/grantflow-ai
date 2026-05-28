export default function LoadingState() {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', padding: '16px' }}>
      {[1, 2, 3].map((i) => (
        <div
          key={i}
          style={{
            height: '96px',
            backgroundColor: 'var(--bg3)',
            borderRadius: 'var(--r)',
            animation: 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
          }}
        />
      ))}
      <style>{`
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }
      `}</style>
    </div>
  )
}
