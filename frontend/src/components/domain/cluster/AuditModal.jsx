import React, { useState } from 'react';
import { X, CheckCircle, XCircle, Layers, Eye, FileText } from 'lucide-react';
import LazyImage from '../../common/LazyImage';
import { saveClusterFeedback } from '../../../services/clusterService';

const AuditModal = ({ log, onClose }) => {
    const [status, setStatus] = useState('idle'); // idle, saving, success, error

    if (!log) return null;

    const handleFeedback = async (feedbackType) => {
        setStatus('saving');
        try {
            await saveClusterFeedback({
                product_id: log.product_id,
                candidate_id: log.candidate_id,
                decision: log.decision,
                feedback: feedbackType === 'correct' ? 'CORRECT' : 'INCORRECT',
                visual_score: log.visual_score,
                text_score: log.text_score,
                final_score: log.final_score,
                method: log.match_method,
                active_weights: log.active_weights
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
                        {/* 1. DECISION BANNER */}
                        <div className="decision-banner" style={{ background: headerBg, borderColor: headerBorder }}>
                            <div className="decision-icon">
                                {isMatch ? <CheckCircle size={32} color={decisionColor} /> : <XCircle size={32} color={decisionColor} />}
                            </div>
                            <div className="decision-text">
                                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
                                    <span className="decision-label">DECISIÓN DE LA IA:</span>
                                    <span style={{
                                        background: 'rgba(99, 102, 241, 0.2)',
                                        color: '#cbd5e1',
                                        padding: '2px 8px',
                                        borderRadius: 4,
                                        fontSize: '0.7rem',
                                        border: '1px solid rgba(99, 102, 241, 0.3)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: 4
                                    }}>
                                        <Layers size={10} /> {log.concept || 'UNKNOWN'}
                                    </span>
                                </div>
                                <h2 style={{ color: decisionColor, margin: 0 }}>{decisionText}</h2>
                                <p className="decision-reason">
                                    Motivo: <strong>{log.match_method}</strong> (Score: {(log.final_score * 100).toFixed(1)}%)
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
                                        <label><Eye size={14} /></label>
                                        <div className="progress-bar">
                                            <div className="fill" style={{ width: `${log.visual_score * 100}%`, background: '#3b82f6' }}></div>
                                        </div>
                                        <span>{Math.round(log.visual_score * 100)}%</span>
                                    </div>
                                    <div className="score-item">
                                        <label><FileText size={14} /></label>
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

                        {/* 3. HUMAN VEREDICT */}
                        <div className="veredict-section">
                            <h3>👨‍⚖️ Tu Veredicto Humano</h3>
                            <p className="instruction">Ayuda a corregir o reforzar a la IA:</p>

                            <div className="feedback-buttons">
                                <button className="btn-feedback agree" onClick={() => handleFeedback('correct')} disabled={status === 'saving'}>
                                    <div className="icon-box"><CheckCircle size={24} /></div>
                                    <div className="text-box">
                                        <span className="main-text">Estoy de Acuerdo</span>
                                        <span className="sub-text">
                                            {isMatch ? "Sí, son el mismo producto." : "Bien hecho, son distintos."}
                                        </span>
                                    </div>
                                </button>

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
                .product-card-compare h4 { font-size: 0.9rem; color: #e2e8f0; margin: 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }

                .vs-center { display: flex; flex-direction: column; align-items: center; justify-content: center; width: 140px; }
                .vs-badge { 
                    font-size: 1.5rem; font-weight: 900; color: #475569; margin-bottom: 1.5rem; 
                    background: rgba(255,255,255,0.05); padding: 0.5rem 1rem; border-radius: 8px;
                }
                .scores-grid { width: 100%; display: flex; flex-direction: column; gap: 0.75rem; }
                .score-item { display: flex; align-items: center; gap: 0.5rem; font-size: 0.8rem; color: #94a3b8; }
                .score-item label { width: 20px; display: flex; justify-content: center; }
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

export default AuditModal;
