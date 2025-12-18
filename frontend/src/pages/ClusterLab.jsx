import React, { useState, useEffect } from 'react';
import {
    Activity, Box, Database, Search, Cpu, List, X,
    CheckCircle, XCircle, AlertTriangle, AlertCircle, Eye, FileText,
    Layers, Zap, BarChart2, Award, Trash2
} from 'lucide-react';
// import LazyImage from '../components/common/LazyImage.jsx';
const LazyImage = ({ src, alt, style, className }) => (
    <img src={src} alt={alt} className={className} style={{ ...style, width: '100%', height: '100%', objectFit: 'cover' }} />
);
import './ClusterLab.css';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Components
const AuditModal = ({ log, onClose }) => {
    const [status, setStatus] = useState('idle'); // idle, saving, success, error

    if (!log) return null;

    const handleFeedback = async (feedbackType) => {
        setStatus('saving');
        try {
            await fetch(`${API_URL}/api/cluster-lab/feedback/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    product_id: log.product_id,
                    candidate_id: log.candidate_id,
                    decision: log.decision,
                    feedback: feedbackType === 'correct' ? 'CORRECT' : 'INCORRECT',

                    // Rich Data for AI Trainer
                    visual_score: log.visual_score,
                    text_score: log.text_score,
                    final_score: log.final_score,
                    method: log.method,
                    active_weights: log.active_weights // Enviamos el snapshot que guardo el log
                })
            });
            setStatus('success');
            setTimeout(() => onClose(), 1000); // Close after 1s delay
        } catch (err) {
            console.error("Error saving feedback:", err);
            setStatus('error');
        }
    };

    const isMatch = log.decision === 'JOINED_CLUSTER' || log.decision === 'MATCH' || log.decision === 'VISUAL_MATCH' || log.decision === 'HYBRID_MATCH';
    const decisionText = isMatch ? 'UNIÓN REALIZADA' : 'CANDIDATO DESCARTADO';
    const decisionColor = isMatch ? '#10b981' : '#ef4444';
    const headerBg = isMatch ? 'rgba(16, 185, 129, 0.15)' : 'rgba(239, 68, 68, 0.15)';
    const headerBorder = isMatch ? 'rgba(16, 185, 129, 0.3)' : 'rgba(239, 68, 68, 0.3)';

    return (
        <div className="audit-modal-overlay" onClick={onClose}>
            <div className="audit-modal-content glass-panel" onClick={e => e.stopPropagation()}>
                <button className="close-btn" onClick={onClose}><X size={24} /></button>

                {status === 'success' ? (
                    <div className="success-message">
                        <CheckCircle size={64} color="#10b981" />
                        <h2>¡Entrenamiento Recibido!</h2>
                        <p>El cerebro digital ha ajustado sus pesos neuronales.</p>
                    </div>
                ) : (
                    <>
                        {/* 1. DECISION BANNER (The "Clear" Part) */}
                        <div className="decision-banner" style={{ background: headerBg, borderColor: headerBorder }}>
                            <div className="decision-icon">
                                {isMatch ? <CheckCircle size={32} color={decisionColor} /> : <XCircle size={32} color={decisionColor} />}
                            </div>
                            <div className="decision-text">
                                <span className="decision-label">DECISIÓN DE LA IA:</span>
                                <h2 style={{ color: decisionColor }}>{decisionText}</h2>
                                <p className="decision-reason">
                                    Motivo: <strong>{log.method}</strong> (Score: {(log.final_score * 100).toFixed(1)}%)
                                </p>
                            </div>
                        </div>

                        {/* 2. COMPARISON (Side by Side) */}
                        <div className="vs-container">
                            <div className="product-card-compare">
                                <span className="p-label">Producto A (Original)</span>
                                <div className="img-wrapper">
                                    <LazyImage src={log.image_a} alt="Base" />
                                </div>
                                <h4 title={log.title_a}>{log.title_a || 'Sin Título'}</h4>
                            </div>

                            <div className="vs-center">
                                <div className="vs-badge">VS</div>
                                <div className="scores-grid">
                                    <div className="score-item">
                                        <label>Visual</label>
                                        <div className="progress-bar">
                                            <div className="fill" style={{ width: `${log.visual_score * 100}%`, background: '#3b82f6' }}></div>
                                        </div>
                                        <span>{Math.round(log.visual_score * 100)}%</span>
                                    </div>
                                    <div className="score-item">
                                        <label>Texto</label>
                                        <div className="progress-bar">
                                            <div className="fill" style={{ width: `${log.text_score * 100}%`, background: '#8b5cf6' }}></div>
                                        </div>
                                        <span>{Math.round(log.text_score * 100)}%</span>
                                    </div>
                                </div>
                            </div>

                            <div className="product-card-compare">
                                <span className="p-label">Producto B (Candidato)</span>
                                <div className="img-wrapper">
                                    <LazyImage src={log.image_b} alt="Candidate" />
                                </div>
                                <h4 title={log.title_b}>{log.title_b || 'Sin Título'}</h4>
                            </div>
                        </div>

                        {/* 3. HUMAN VEREDICT (The Unambiguous Buttons) */}
                        <div className="veredict-section">
                            <h3>👨‍⚖️ Tu Veredicto Humano</h3>
                            <p className="instruction">Ayuda a corregir o reforzar a la IA:</p>

                            <div className="feedback-buttons">
                                {/* POSITIVE FEEDBACK (AGREE) */}
                                <button className="btn-feedback agree" onClick={() => handleFeedback('correct')} disabled={status === 'saving'}>
                                    <div className="icon-box"><CheckCircle size={24} /></div>
                                    <div className="text-box">
                                        <span className="main-text">Estoy de Acuerdo</span>
                                        <span className="sub-text">
                                            {isMatch ? "Sí, son el mismo producto." : "Bien hecho, son distintos."}
                                        </span>
                                    </div>
                                </button>

                                {/* NEGATIVE FEEDBACK (DISAGREE) */}
                                <button className="btn-feedback disagree" onClick={() => handleFeedback('incorrect')} disabled={status === 'saving'}>
                                    <div className="icon-box"><XCircle size={24} /></div>
                                    <div className="text-box">
                                        <span className="main-text">Equivocado</span>
                                        <span className="sub-text">
                                            {isMatch ? "Error, NO son el mismo." : "Mal, DEBERÍAN unirse."}
                                        </span>
                                    </div>
                                </button>
                            </div>
                        </div>
                    </>
                )}
            </div>
            <style jsx>{`
                .audit-modal-overlay {
                    position: fixed; top: 0; left: 0; width: 100vw; height: 100vh;
                    background: rgba(0,0,0,0.85); backdrop-filter: blur(5px);
                    display: flex; align-items: center; justify-content: center; z-index: 2000;
                }
                .audit-modal-content {
                    width: 95%; max-width: 850px; background: #1e293b; border-radius: 16px;
                    border: 1px solid rgba(255,255,255,0.1); overflow: hidden;
                    box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
                    animation: fadeIn 0.3s ease;
                }
                @keyframes fadeIn { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
                
                .close-btn { position: absolute; top: 1rem; right: 1rem; background: none; border: none; color: #64748b; cursor: pointer; transition: color 0.2s; }
                .close-btn:hover { color: #fff; }

                .success-message { padding: 4rem; text-align: center; color: #fff; }

                /* BANNER */
                .decision-banner {
                    display: flex; gap: 1.5rem; align-items: center; padding: 1.5rem 2rem;
                    border-bottom: 1px solid transparent;
                }
                .decision-text h2 { margin: 0; font-size: 1.5rem; font-weight: 800; letter-spacing: -0.5px; }
                .decision-label { font-size: 0.75rem; font-weight: bold; color: #94a3b8; letter-spacing: 1px; }
                .decision-reason { margin: 0.25rem 0 0; color: #cbd5e1; font-size: 0.9rem; }

                /* COMPARISON */
                .vs-container {
                    display: grid; grid-template-columns: 1fr auto 1fr; gap: 1rem; padding: 2rem;
                    background: rgba(0,0,0,0.2);
                }
                .product-card-compare { text-align: center; }
                .p-label { display: block; font-size: 0.75rem; color: #64748b; margin-bottom: 0.5rem; font-weight: bold; text-transform: uppercase; }
                .img-wrapper {
                    width: 100%; aspect-ratio: 1; background: #000; border-radius: 8px; overflow: hidden; margin-bottom: 0.75rem;
                    border: 1px solid rgba(255,255,255,0.1);
                }
                /* Use LazyImage styled if available, else simple img styles */
                .product-card-compare h4 { font-size: 0.9rem; color: #e2e8f0; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

                .vs-center { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 140px; }
                .vs-badge { 
                    font-size: 1.5rem; font-weight: 900; color: #475569; margin-bottom: 1.5rem; 
                    background: rgba(255,255,255,0.05); padding: 0.5rem 1rem; border-radius: 8px;
                }
                .scores-grid { width: 100%; display: flex; flex-direction: column; gap: 0.75rem; }
                .score-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; color: #94a3b8; }
                .score-item label { width: 40px; }
                .progress-bar { flex: 1; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; overflow: hidden; }
                .fill { height: 100%; border-radius: 3px; }

                /* VEREDICT */
                .veredict-section { padding: 2rem; background: #1e293b; text-align: center; }
                .veredict-section h3 { margin: 0 0 0.5rem; font-size: 1.1rem; color: #fff; }
                .instruction { color: #64748b; margin-bottom: 1.5rem; font-size: 0.9rem; }

                .feedback-buttons { display: flex; gap: 1rem; justify-content: center; }
                .btn-feedback {
                    flex: 1; max-width: 280px; padding: 1rem; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);
                    background: rgba(255,255,255,0.03); cursor: pointer; transition: all 0.2s;
                    display: flex; align-items: center; gap: 1rem; text-align: left;
                }
                .btn-feedback:hover { transform: translateY(-2px); }
                .btn-feedback.agree:hover { background: rgba(16, 185, 129, 0.1); border-color: rgba(16, 185, 129, 0.5); }
                .btn-feedback.disagree:hover { background: rgba(239, 68, 68, 0.1); border-color: rgba(239, 68, 68, 0.5); }

                .icon-box { display: flex; align-items: center; justify-content: center; color: #94a3b8; }
                .btn-feedback.agree .icon-box { color: #10b981; }
                .btn-feedback.disagree .icon-box { color: #ef4444; }

                .text-box { display: flex; flex-direction: column; }
                .main-text { font-weight: bold; font-size: 1rem; color: #e2e8f0; display: block; margin-bottom: 2px; }
                .sub-text { font-size: 0.75rem; color: #64748b; }
                
                .btn-feedback.agree:hover .main-text { color: #10b981; }
                .btn-feedback.disagree:hover .main-text { color: #ef4444; }
            `}</style>
        </div>
    );
};

const ClusterLab = () => {
    const [auditLogs, setAuditLogs] = useState([]);
    const [orphans, setOrphans] = useState([]);
    const [loading, setLoading] = useState(true);
    const [activeTab, setActiveTab] = useState('audit');
    const [filterTab, setFilterTab] = useState('ALL'); // ALL, MATCH, REJECT
    const [metrics, setMetrics] = useState(null);

    const [selectedLog, setSelectedLog] = useState(null); // For Modal 
    const [simulationData, setSimulationData] = useState(null); // For Orphan Simulation Modal

    const [orphanCandidates, setOrphanCandidates] = useState([]); // Stores the list of 15 candidates
    const [selectedMatches, setSelectedMatches] = useState([]); // IDs of candidates selected by user
    const [targetOrphan, setTargetOrphan] = useState(null); // The main orphan product being investigated
    const [isProcessingOrphan, setIsProcessingOrphan] = useState(false);

    const handleOpenOrphanInvestigator = async (orphan) => {
        setIsProcessingOrphan(true);
        try {
            const res = await fetch(`${API_URL}/api/cluster-lab/orphans/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ product_id: orphan.product_id })
            });
            if (res.ok) {
                const data = await res.json();
                setTargetOrphan(data.target);
                setOrphanCandidates(data.candidates); // Array of 15
                setSelectedMatches([]); // Reset selection
                // Ya no abrimos el modal de Logs, sino el de Investigador
            }
        } catch (err) {
            console.error(err);
        }
        setIsProcessingOrphan(false);
    };

    const toggleCandidateSelection = (candidateId) => {
        if (selectedMatches.includes(candidateId)) {
            setSelectedMatches(selectedMatches.filter(id => id !== candidateId));
        } else {
            setSelectedMatches([...selectedMatches, candidateId]);
        }
    };

    const executeOrphanAction = async (actionType) => {
        // actionType: 'MERGE_SELECTED' | 'CONFIRM_SINGLETON' | 'TRASH'
        setIsProcessingOrphan(true);

        try {
            const res = await fetch(`${API_URL}/api/cluster-lab/orphans/action/`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    product_id: targetOrphan.id,
                    action: actionType,
                    candidates: selectedMatches
                })
            });

            if (res.ok) {
                // OPTIMISTIC UPDATE: Remover el huérfano procesado de la lista local inmediatamente
                setOrphans(prev => prev.filter(o => o.product_id !== targetOrphan.id));

                // Cerrar Modal con delay mínimo para feedback visual
                setTimeout(() => {
                    setTargetOrphan(null);
                    setOrphanCandidates([]);
                    setSelectedMatches([]);
                }, 500);
            } else {
                console.error("Action failed");
            }

        } catch (err) {
            console.error("Error executing action:", err);
        } finally {
            setIsProcessingOrphan(false);
        }
    };




    // Polling function for logs
    useEffect(() => {
        const fetchLogs = async () => {
            try {
                const res = await fetch(`${API_URL}/api/cluster-lab/audit-logs/`);
                if (res.ok) {
                    const data = await res.json();
                    setAuditLogs(data);
                }
            } catch (err) {
                console.error("Error fetching audit logs", err);
            }
        };

        const fetchOrphans = async () => {
            try {
                const res = await fetch(`${API_URL}/api/cluster-lab/orphans/`);
                if (res.ok) {
                    const data = await res.json();
                    setOrphans(data);
                }
            } catch (err) {
                console.error("Error fetching orphans", err);
            }
            setLoading(false);
        };

        const fetchMetrics = async () => {
            try {
                const res = await fetch(`${API_URL}/api/cluster-lab/stats/`);
                if (res.ok) {
                    const data = await res.json();
                    setMetrics(data);
                }
            } catch (err) {
                console.error("Error metrics", err);
            }
        };

        fetchLogs();
        fetchOrphans();
        fetchMetrics();

        // Refresh logs and metrics every 3 seconds
        const interval = setInterval(() => {
            fetchLogs();
            fetchMetrics();
        }, 3000);

        return () => clearInterval(interval);
    }, []);

    const getScoreColor = (score) => {
        if (score >= 0.8) return '#10b981'; // Green
        if (score >= 0.5) return '#f59e0b'; // Amber
        return '#ef4444'; // Red
    };

    return (
        <div style={{ padding: '2rem', maxWidth: '1600px', margin: '0 auto', color: '#fff' }}>

            {/* Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
                <div>
                    <h1 className="text-gradient" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontSize: '2rem' }}>
                        <Layers size={32} /> Cluster Lab <span style={{ fontSize: '0.8rem', background: '#6366f1', padding: '0.2rem 0.5rem', borderRadius: 4, verticalAlign: 'middle' }}>V3 HYBRID</span>
                    </h1>
                    <p style={{ color: '#94a3b8', marginTop: '0.5rem' }}>
                        Centro de Auditoría Neuronal: Visualización en tiempo real del motor de clustering.
                    </p>
                </div>

                <div className="glass-panel" style={{ padding: '0.5rem', display: 'flex', gap: '0.5rem' }}>
                    <button
                        className={`btn-tab ${activeTab === 'audit' ? 'active' : ''}`}
                        onClick={() => setActiveTab('audit')}
                        style={{ background: activeTab === 'audit' ? 'rgba(99, 102, 241, 0.2)' : 'transparent', border: 'none', color: '#fff', padding: '0.5rem 1rem', borderRadius: 6, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                    >
                        <Activity size={18} /> Consola en Vivo
                    </button>
                    <button
                        className={`btn-tab ${activeTab === 'orphans' ? 'active' : ''}`}
                        onClick={() => setActiveTab('orphans')}
                        style={{ background: activeTab === 'orphans' ? 'rgba(99, 102, 241, 0.2)' : 'transparent', border: 'none', color: '#fff', padding: '0.5rem 1rem', borderRadius: 6, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                    >
                        <AlertCircle size={18} /> Huérfanos ({orphans.length})
                    </button>
                </div>
            </div>

            {/* LIVE CONSOLE TAB */}
            {activeTab === 'audit' && (
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
                            {auditLogs.filter(log => {
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
                                auditLogs
                                    .filter(log => {
                                        if (filterTab === 'ALL') return true;
                                        const isMatch = ['JOINED_CLUSTER', 'MATCH', 'VISUAL_MATCH', 'HYBRID_MATCH'].includes(log.decision);
                                        return filterTab === 'MATCH' ? isMatch : !isMatch;
                                    })
                                    .map((log, idx) => (
                                        <div
                                            onClick={() => setSelectedLog(log)}
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
                        {/* XP Counter */}
                        <div className="glass-card" style={{ padding: '1.5rem', textAlign: 'center', position: 'relative', overflow: 'hidden' }}>
                            <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '4px', background: 'linear-gradient(90deg, #6366f1, #a855f7)' }}></div>
                            <h4 style={{ color: '#94a3b8', marginBottom: '0.5rem', fontSize: '0.85rem', textTransform: 'uppercase', letterSpacing: '1px' }}>
                                Tu Nivel de Entrenador
                            </h4>
                            <div style={{ fontSize: '3rem', fontWeight: '800', color: '#fff', textShadow: '0 0 20px rgba(99,102,241,0.5)', lineHeight: 1 }}>
                                {metrics ? metrics.xp_audits : 0}
                            </div>

                            {/* Daily XP Badge */}
                            {metrics && metrics.xp_today > 0 && (
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

                        {/* System Health / Knowledge */}
                        <div className="glass-card" style={{ padding: '1.5rem', display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
                            <h4 style={{ color: '#fff', fontSize: '0.9rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem', margin: 0 }}>
                                <BarChart2 size={16} style={{ verticalAlign: 'middle', marginRight: 5 }} />
                                Salud del Sistema
                            </h4>

                            {/* Precision Bar */}
                            <div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.8rem', marginBottom: '0.25rem' }}>
                                    <span style={{ color: '#94a3b8' }}>Precisión Humano/IA</span>
                                    <span style={{ color: '#fff' }}>
                                        {metrics ? Math.round((metrics.feedback_correct / (metrics.xp_audits || 1)) * 100) : 0}%
                                    </span>
                                </div>
                                <div style={{ width: '100%', height: '8px', background: 'rgba(239, 68, 68, 0.4)', borderRadius: 4, overflow: 'hidden', display: 'flex' }}>
                                    {/* Green Part (Correct) */}
                                    <div style={{
                                        width: `${metrics ? (metrics.feedback_correct / (metrics.xp_audits || 1)) * 100 : 0}%`,
                                        background: '#10b981',
                                        height: '100%'
                                    }}></div>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#64748b', marginTop: 2 }}>
                                    <span>Acuerdos: {metrics?.feedback_correct || 0}</span>
                                    <span>Corregidos: {metrics?.feedback_incorrect || 0}</span>
                                </div>
                            </div>

                            {/* Pending Orphans */}
                            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(255,255,255,0.05)', padding: '0.75rem', borderRadius: 8 }}>
                                <div style={{ display: 'flex', flexDirection: 'column' }}>
                                    <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Huérfanos Pendientes</span>
                                    <span style={{ fontSize: '1.1rem', fontWeight: 'bold', color: '#f59e0b' }}>
                                        {metrics ? metrics.pending_orphans : 0}
                                    </span>
                                </div>
                                <div style={{ textAlign: 'right' }}>
                                    <span style={{ fontSize: '0.7rem', color: '#64748b' }}>de {metrics?.total_products} productos</span>
                                </div>
                            </div>
                        </div>

                        <div className="glass-card" style={{ padding: '1.5rem' }}>
                            <h4 style={{ color: '#fff', fontSize: '0.9rem', marginBottom: '1rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '0.5rem' }}>
                                Leyenda de Métodos
                            </h4>
                            <ul style={{ listStyle: 'none', padding: 0, margin: 0, fontSize: '0.85rem', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                                <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#3b82f6' }}></div>
                                    <span><strong>Visual Match:</strong> Foto idéntica (92%+)</span>
                                </li>
                                <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#8b5cf6' }}></div>
                                    <span><strong>Text Rescue:</strong> Texto idéntico salvó foto distinta.</span>
                                </li>
                                <li style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    <div style={{ width: 8, height: 8, borderRadius: '50%', background: '#f59e0b' }}></div>
                                    <span><strong>Hybrid Score:</strong> Promedio ponderado.</span>
                                </li>
                            </ul>
                        </div>
                    </div>
                </div>
            )}

            {/* ORPHANS TAB - INVESTIGATOR */}
            {activeTab === 'orphans' && (
                <div>
                    <div className="glass-panel" style={{ padding: '2rem', textAlign: 'center', marginBottom: '1rem' }}>
                        <Search size={48} color="#6366f1" style={{ marginBottom: '1rem' }} />
                        <h2>Investigador de Solitarios</h2>
                        <p style={{ color: '#94a3b8', maxWidth: '600px', margin: '0 auto' }}>
                            Estos productos no encontraron pareja. Haz clic en uno para forzar una búsqueda de candidatos profundos.
                        </p>
                    </div>

                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(250px, 1fr))', gap: '1rem' }}>
                        {orphans.map(orphan => (
                            <div key={orphan.cluster_id} className="glass-card" style={{ padding: '1rem', position: 'relative' }}>
                                <div style={{ width: '100%', height: '180px', borderRadius: 8, overflow: 'hidden', marginBottom: '1rem', background: '#000' }}>
                                    <img src={orphan.image} alt="" style={{ width: '100%', height: '100%', objectFit: 'contain' }} />
                                </div>
                                <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', lineHeight: '1.4' }}>{orphan.title}</h4>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', color: '#94a3b8' }}>
                                    <span>ID: {orphan.product_id}</span>
                                    <span>${orphan.price}</span>
                                </div>
                                <button onClick={() => handleOpenOrphanInvestigator(orphan)} style={{
                                    width: '100%',
                                    marginTop: '1rem',
                                    padding: '0.5rem',
                                    background: 'rgba(99, 102, 241, 0.1)',
                                    border: '1px solid rgba(99, 102, 241, 0.3)',
                                    color: '#818cf8',
                                    borderRadius: 6,
                                    cursor: 'pointer'
                                }}>
                                    Investigar (Grid V3)
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* AUDIT MODAL (EXISTENTE) */}
            {selectedLog && (
                <AuditModal log={selectedLog} onClose={() => setSelectedLog(null)} />
            )}

            {/* NEW: ORPHAN INVESTIGATOR MODAL (GRID V3) - REDESIGNED */}
            {targetOrphan && (
                <div className="audit-modal-overlay" onClick={() => setTargetOrphan(null)}>
                    <div className="investigator-modal glass-panel" onClick={e => e.stopPropagation()}>

                        {/* 1. HEADER SUTIL COMPACTO */}
                        <div className="glass-header">
                            <div className="header-title">
                                <span className="icon-diamond">💎</span>
                                <div>
                                    <h3>Investigador de Diamantes</h3>
                                    <span className="subtitle">ID: {targetOrphan.id} • {targetOrphan.title}</span>
                                </div>
                            </div>
                            <button className="close-btn-round" onClick={() => setTargetOrphan(null)}><X size={20} /></button>
                        </div>

                        <div className="investigator-body">
                            {/* LEFT: TARGET PRODUCT (SOLO INFO VISUAL) */}
                            <div className="target-sidebar">
                                <div className="img-frame">
                                    <LazyImage
                                        src={orphans.find(o => o.product_id === targetOrphan.id)?.image || targetOrphan.image || 'https://via.placeholder.com/300?text=No+Image'}
                                        alt="Target"
                                    />
                                    <span className="badge-target">ORIGINAL</span>
                                </div>
                                <div className="target-meta">
                                    <h4 className="target-title" title={targetOrphan.title}>{targetOrphan.title}</h4>
                                    <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', alignItems: 'center', marginBottom: '0.5rem' }}>
                                        <span style={{ fontFamily: 'monospace', color: '#64748b', fontSize: '0.9rem', background: 'rgba(255,255,255,0.05)', padding: '2px 6px', borderRadius: 4 }}>#{targetOrphan.id}</span>
                                        <p className="price-tag" style={{ margin: 0 }}>${targetOrphan.price || 'N/A'}</p>
                                    </div>
                                    <p className="helper-text">Busca gemelos en la red derecha 👉</p>
                                </div>
                            </div>

                            {/* RIGHT: CANDIDATES GRID (SCROLLABLE) */}
                            <div className="grid-container">
                                <div className="candidates-grid">
                                    {orphanCandidates.map(cand => (
                                        <div
                                            key={cand.id}
                                            className={`candidate-card-mini ${selectedMatches.includes(cand.id) ? 'selected' : ''}`}
                                            onClick={() => toggleCandidateSelection(cand.id)}
                                        >
                                            <div className="mini-img">
                                                <LazyImage src={cand.image} alt={cand.title} />

                                                {/* SELECTION OVERLAY (CHECK) */}
                                                {selectedMatches.includes(cand.id) && (
                                                    <div className="selection-overlay">
                                                        <CheckCircle size={32} color="#fff" fill="#10b981" />
                                                    </div>
                                                )}

                                                <div className="match-percent" style={{ background: getScoreColor(cand.scores.final) }}>
                                                    {Math.round(cand.scores.final * 100)}%
                                                </div>
                                            </div>
                                            <div className="mini-details">
                                                <p className="mini-title" title={cand.title}>{cand.title}</p>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                                    <span className="mini-id" style={{ fontSize: '0.7rem', color: '#64748b', fontFamily: 'monospace' }}>#{cand.id}</span>
                                                    <p className="mini-price">${cand.price}</p>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>

                        {/* 3. FOOTER DE ACCIONES GLOBAL (DOS BOTONES CLAROS) */}
                        <div className="investigator-footer">
                            <div className="status-msg">
                                {selectedMatches.length === 0 ? (
                                    <span style={{ color: '#f59e0b' }}>⚠️ No has seleccionado coincidencias.</span>
                                ) : (
                                    <span style={{ color: '#10b981' }}>✅ {selectedMatches.length} productos seleccionados para unir.</span>
                                )}
                            </div>

                            <div className="action-buttons">
                                <button
                                    className="btn-danger"
                                    onClick={() => executeOrphanAction('TRASH')}
                                    disabled={isProcessingOrphan}
                                    title="Descartar producto (Basura/Irrelevante)"
                                >
                                    <Trash2 size={18} />
                                </button>
                                <button
                                    className="btn-secondary"
                                    onClick={() => executeOrphanAction('CONFIRM_SINGLETON')}
                                    disabled={isProcessingOrphan || selectedMatches.length > 0}
                                    title="Marca este producto como único en su tipo (Diamante)"
                                >
                                    <Award size={18} />
                                    Confirmar como Único (Diamante)
                                </button>

                                <button
                                    className="btn-primary"
                                    onClick={() => executeOrphanAction('MERGE_SELECTED')}
                                    disabled={isProcessingOrphan || selectedMatches.length === 0}
                                >
                                    <CheckCircle size={18} />
                                    Revisión Terminada (Unir)
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ClusterLab;
