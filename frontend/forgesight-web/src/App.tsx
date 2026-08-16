import React from 'react'

export default function App() {
  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif', backgroundColor: '#0f172a', color: '#f8fafc', minHeight: '100vh' }}>
      <header style={{ borderBottom: '1px solid #334155', pb: '1rem', mb: '2rem' }}>
        <h1 style={{ color: '#38bdf8' }}>ForgeSight AI</h1>
        <p style={{ color: '#94a3b8' }}>A2A-Powered Multimodal Manufacturing Intelligence Platform</p>
      </header>

      <main style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
        <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <h2 style={{ color: '#f1f5f9' }}>🔍 Visual Inspection</h2>
          <p style={{ color: '#94a3b8' }}>Real-time defect detection and visual evidence correlation.</p>
        </div>

        <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <h2 style={{ color: '#f1f5f9' }}>🤝 Agent Collaboration (A2A)</h2>
          <p style={{ color: '#94a3b8' }}>Supervisor, Vision, Quality, and Root Cause agent orchestration.</p>
        </div>

        <div style={{ background: '#1e293b', padding: '1.5rem', borderRadius: '8px', border: '1px solid #334155' }}>
          <h2 style={{ color: '#f1f5f9' }}>⚡ MCP Operational Tools</h2>
          <p style={{ color: '#94a3b8' }}>Seamless access to QMS, inventory, and maintenance telemetries.</p>
        </div>
      </main>
    </div>
  )
}
