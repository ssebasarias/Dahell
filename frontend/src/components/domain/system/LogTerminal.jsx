import React from 'react';

const LogTerminal = ({ title, logs, color = '#10b981' }) => {
    const serviceLogs = logs.filter(l => l.service.toLowerCase() === title.toLowerCase());
    return (
        <div style={{
            background: '#09090b',
            borderRadius: 12,
            border: '1px solid rgba(255,255,255,0.08)',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            height: 320,
            boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.3)'
        }}>
            <div style={{
                padding: '0.75rem 1rem',
                borderBottom: '1px solid rgba(255,255,255,0.08)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                background: 'rgba(255,255,255,0.03)'
            }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: color, boxShadow: `0 0 8px ${color}` }}></div>
                    <span style={{ fontSize: '0.8rem', fontWeight: 'bold', color: '#e2e8f0', textTransform: 'uppercase' }}>{title}</span>
                </div>
                <span style={{ fontSize: '0.7rem', color: '#64748b', fontFamily: 'monospace' }}>
                    {serviceLogs.length > 0 ? 'LIVE' : 'IDLE'}
                </span>
            </div>
            <div className="terminal-body" style={{
                padding: '1rem',
                flex: 1,
                overflowY: 'auto',
                fontFamily: "'Fira Code', 'Consolas', monospace",
                fontSize: '0.75rem',
                color: '#e2e8f0',
                lineHeight: '1.5'
            }}>
                {serviceLogs.length === 0 && (
                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', color: '#334155' }}>
                        <span style={{ fontStyle: 'italic' }}>Waiting for logs...</span>
                    </div>
                )}
                {serviceLogs.slice(-30).map((log, i) => (
                    <div key={i} style={{ marginBottom: 4, whiteSpace: 'pre-wrap', wordBreak: 'break-word', display: 'flex' }}>
                        <span style={{ color: '#475569', marginRight: '0.5rem', userSelect: 'none' }}>$</span>
                        <span>{log.message}</span>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default LogTerminal;
