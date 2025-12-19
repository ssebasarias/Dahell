import React from 'react';
import { Eye, FileText, BarChart2 } from 'lucide-react';

const LiveConsole = ({ logs, filterTab, setFilterTab, onSelectLog, metrics }) => {
    const getScoreColor = (score) => {
        if (score >= 0.8) return '#10b981';
        if (score >= 0.5) return '#f59e0b';
        return '#ef4444';
    };

    return (
        <div style={{ display: 'grid', gridTemplateColumns: '3fr 1fr', gap: '1.5rem' }}>
            {/* Main Log Feed */}
            <div className="glass-panel" style={{ padding: '0', overflow: 'hidden', height: '70vh', display: 'flex', flexDirection: 'column' }}>

                {/* HEADER CON FILTROS */}
                <div style={{
                    padding: '1rem',
                    borderBottom: '1px solid rgba(255,255,255,0.05)',
                    background: 'rgba(0,0,0,0.2)',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center'
                }}>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                        <button
                            onClick={() => setFilterTab('ALL')}
                            className={`filter-tab ${filterTab === 'ALL' ? 'active' : ''}`}
                        >
                            Todos
                        </button>
                        <button
                            onClick={() => setFilterTab('MATCH')}
                            className={`filter-tab match ${filterTab === 'MATCH' ? 'active' : ''}`}
                        >
                            ✅ Matches (Revisar Errores)
                        </button>
                        <button
                            onClick={() => setFilterTab('REJECT')}
                            className={`filter-tab reject ${filterTab === 'REJECT' ? 'active' : ''}`}
                        >
                            ❌ Rechazados (Buscar Oportunidades)
                        </button>
                    </div>

                    <span style={{ fontSize: '0.8rem', color: '#10b981', display: 'flex', alignItems: 'center', gap: 4 }}>
                        <span className="pulse-dot"></span> Online
                    </span>
                </div>

                {/* LISTA FILTRADA */}
                <div className="custom-scrollbar" style={{ flex: 1, overflowY: 'auto', padding: '0' }}>
                    {logs.filter(log => {
                        if (filterTab === 'ALL') return true;
                        const isMatch = ['JOINED_CLUSTER', 'MATCH', 'VISUAL_MATCH', 'HYBRID_MATCH'].includes(log.decision);
                        return filterTab === 'MATCH' ? isMatch : !isMatch;
                    }).length === 0 ? (
                        <div style={{ padding: '4rem', textAlign: 'center', color: '#64748b' }}>
                            {filterTab === 'MATCH'
                                ? "No hay uniones recientes para revisar."
                                : filterTab === 'REJECT'
                                    ? "No hay rechazos recientes. ¡La IA está siendo inclusiva!"
                                    : "Esperando nuevos eventos del Clusterizer..."}
                        </div>
                    ) : (
                        logs
                            .filter(log => {
                                if (filterTab === 'ALL') return true;
                                const isMatch = ['JOINED_CLUSTER', 'MATCH', 'VISUAL_MATCH', 'HYBRID_MATCH'].includes(log.decision);
                                return filterTab === 'MATCH' ? isMatch : !isMatch;
                            })
                            .map((log, idx) => (
                                <div
                                    onClick={() => onSelectLog(log)}
                                    key={idx}
                                    style={{
                                        padding: '0.85rem 1rem',
                                        borderBottom: '1px solid rgba(255,255,255,0.03)',
                                        background: log.decision === 'JOINED_CLUSTER' ? 'rgba(16, 185, 129, 0.02)' : 'transparent',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '1rem',
                                        fontSize: '0.9rem',
                                        cursor: 'pointer',
                                        transition: 'all 0.2s',
                                        borderLeft: log.decision === 'JOINED_CLUSTER' ? '3px solid #10b981' : '3px solid transparent'
                                    }}
                                    className="log-row"
                                >
                                    {/* Time */}
                                    <div style={{ color: '#64748b', fontSize: '0.75rem', minWidth: '40px' }}>
                                        {new Date(log.timestamp * 1000).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                    </div>

                                    {/* Decision Badge */}
                                    <div style={{ minWidth: '90px' }}>
                                        {log.decision === 'JOINED_CLUSTER' ? (
                                            <span style={{ background: 'rgba(16, 185, 129, 0.2)', color: '#10b981', padding: '2px 8px', borderRadius: 4, fontSize: '0.7rem', fontWeight: 'bold' }}>MATCH</span>
                                        ) : log.decision === 'CANDIDATE' ? (
                                            <span style={{ background: 'rgba(245, 158, 11, 0.2)', color: '#f59e0b', padding: '2px 8px', borderRadius: 4, fontSize: '0.7rem', fontWeight: 'bold' }}>CANDIDATO</span>
                                        ) : (
                                            <span style={{ background: 'rgba(239, 68, 68, 0.2)', color: '#ef4444', padding: '2px 8px', borderRadius: 4, fontSize: '0.7rem', fontWeight: 'bold' }}>REJECT</span>
                                        )}
                                    </div>

                                    {/* Products Info */}
                                    <div style={{ flex: 1, overflow: 'hidden' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: 2 }}>
                                            <span style={{ color: '#fff', fontWeight: 500 }}>{log.title_a}</span>
                                            {/* Concept Tag in List */}
                                            <span style={{ fontSize: '0.65rem', background: '#334155', color: '#94a3b8', padding: '1px 4px', borderRadius: 2 }}>
                                                {log.concept || '?'}
                                            </span>
                                            <span style={{ color: '#64748b' }}>vs</span>
                                        </div>
                                        <div style={{ color: '#94a3b8', fontSize: '0.8rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                            {log.title_b}
                                        </div>
                                    </div>

                                    {/* Scores */}
                                    <div style={{ display: 'flex', gap: '1rem', minWidth: '180px' }}>
                                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                            <div style={{ width: '40px', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: 2, overflow: 'hidden' }}>
                                                <div style={{ width: `${log.visual_score * 100}%`, height: '100%', background: '#3b82f6' }}></div>
                                            </div>
                                            <span style={{ fontSize: '0.7rem', color: '#64748b', marginTop: 2 }}><Eye size={10} style={{ marginRight: 2 }} /> {Math.round(log.visual_score * 100)}%</span>
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                            <div style={{ width: '40px', height: '4px', background: 'rgba(255,255,255,0.1)', borderRadius: 2, overflow: 'hidden' }}>
                                                <div style={{ width: `${log.text_score * 100}%`, height: '100%', background: '#8b5cf6' }}></div>
                                            </div>
                                            <span style={{ fontSize: '0.7rem', color: '#64748b', marginTop: 2 }}><FileText size={10} style={{ marginRight: 2 }} /> {Math.round(log.text_score * 100)}%</span>
                                        </div>
                                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
                                            <span style={{ color: getScoreColor(log.final_score), fontWeight: 'bold' }}>
                                                {(log.final_score * 100).toFixed(0)}%
                                            </span>
                                            <span style={{ fontSize: '0.65rem', color: '#64748b' }}>FINAL</span>
                                        </div>
                                    </div>
                                </div>
                            ))
                    )}
                </div>
            </div>

            {/* Sidebar Stats */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                {metrics && (
                    <>
                        <div className="glass-card" style={{ padding: '1.5rem', textAlign: 'center', position: 'relative', overflow: 'hidden' }}>
                            <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '4px', background: 'linear-gradient(90deg, #6366f1, #a855f7)' }}></div>
                            <h4 style={{ color: '#94a3b8', marginBottom: '0.5rem', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                                Tu Nivel de Entrenador
                            </h4>
                            <div style={{ fontSize: '3rem', fontWeight: '800', color: '#fff', textShadow: '0 0 20px rgba(99,102,241,0.5)', lineHeight: 1 }}>
                                {metrics.xp_audits}
                            </div>
                            {metrics.xp_today > 0 && (
                                <div style={{
                                    display: 'inline-block',
                                    background: 'rgba(16, 185, 129, 0.2)',
                                    color: '#10b981',
                                    padding: '4px 12px',
                                    borderRadius: '20px',
                                    fontSize: '0.8rem',
                                    fontWeight: 'bold',
                                    marginTop: '0.5rem'
                                }}>
                                    HOY: +{metrics.xp_today}
                                </div>
                            )}
                        </div>

                        <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                            <h4 style={{ color: '#fff', fontSize: '0.9rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem', margin: 0 }}>
                                <BarChart2 size={16} style={{ verticalAlign: 'middle', marginRight: 5 }} />
                                Salud del Sistema
                            </h4>
                            <div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.25rem' }}>
                                    <span style={{ color: '#94a3b8' }}>Precisión Humano/IA</span>
                                    <span style={{ color: '#fff' }}>
                                        {Math.round((metrics.feedback_correct / (metrics.xp_audits || 1)) * 100)}%
                                    </span>
                                </div>
                                <div style={{ width: '100%', height: '8px', background: 'rgba(239, 68, 68, 0.4)', borderRadius: 4, overflow: 'hidden', display: 'flex' }}>
                                    <div style={{
                                        width: `${(metrics.feedback_correct / (metrics.xp_audits || 1)) * 100}%`,
                                        background: '#10b981',
                                        height: '100%'
                                    }}></div>
                                </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(255,255,255,0.05)', padding: '0.75rem', borderRadius: 8 }}>
                                <div style={{ display: 'flex', flexDirection: 'column' }}>
                                    <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Huérfanos Pendientes</span>
                                    <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#f59e0b' }}>
                                        {metrics.pending_orphans}
                                    </span>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                    <span style={{ fontSize: '0.7rem', color: '#64748b' }}>de {metrics.total_products} productos</span>
                                </div>
                            </div>
                        </div>
                    </>
                )}
            </div>
        </div>
    );
};

export default LiveConsole;
