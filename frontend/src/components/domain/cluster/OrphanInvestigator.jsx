import React, { useState } from 'react';
import { X, CheckCircle, Trash2 } from 'lucide-react';
import LazyImage from '../../common/LazyImage';
import { executeOrphanAction } from '../../../services/clusterService';

const OrphanInvestigator = ({ orphan, candidates, onClose, onActionComplete }) => {
    const [selectedMatches, setSelectedMatches] = useState([]);
    const [isProcessing, setIsProcessing] = useState(false);

    const toggleCandidateSelection = (candidateId) => {
        if (selectedMatches.includes(candidateId)) {
            setSelectedMatches(selectedMatches.filter(id => id !== candidateId));
        } else {
            setSelectedMatches([...selectedMatches, candidateId]);
        }
    };

    const handleAction = async (actionType) => {
        setIsProcessing(true);
        try {
            await executeOrphanAction({
                product_id: orphan.id,
                action: actionType,
                candidates: selectedMatches
            });
            onActionComplete(orphan.id); // Notify parent to update state
            onClose();
        } catch (err) {
            console.error("Action failed:", err);
            // Optionally show error toast here
        } finally {
            setIsProcessing(false);
        }
    };

    const getScoreColor = (score) => {
        if (score >= 0.8) return '#10b981';
        if (score >= 0.5) return '#f59e0b';
        return '#ef4444';
    };

    return (
        <div className="audit-modal-overlay" onClick={onClose}>
            <div className="investigator-modal glass-panel" onClick={e => e.stopPropagation()}>

                {/* HEADER */}
                <div className="glass-header">
                    <div className="header-title">
                        <span className="icon-diamond">💎</span>
                        <div>
                            <h3>Investigador de Diamantes</h3>
                            <span className="subtitle">ID: {orphan.id} • {orphan.title}</span>
                        </div>
                    </div>
                    <button className="close-btn-round" onClick={onClose}><X size={20} /></button>
                </div>

                <div className="investigator-body">
                    {/* LEFT: TARGET PRODUCT */}
                    <div className="target-sidebar">
                        <div className="img-frame">
                            <LazyImage
                                src={orphan.image || 'https://via.placeholder.com/300?text=No+Image'}
                                alt="Target"
                            />
                            <span className="badge-target">ORIGINAL</span>
                        </div>
                        <div className="target-meta">
                            <h4 className="target-title" title={orphan.title}>{orphan.title}</h4>
                            <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', alignItems: 'center', marginBottom: '0.5rem' }}>
                                <span className="id-tag">#{orphan.id}</span>
                                <p className="price-tag" style={{ margin: 0 }}>${orphan.price || 'N/A'}</p>
                            </div>
                            <p className="helper-text">Busca gemelos en la lista 👉</p>
                        </div>
                    </div>

                    {/* RIGHT: CANDIDATES GRID */}
                    <div className="grid-container">
                        <div className="candidates-grid">
                            {candidates.map(cand => (
                                <div
                                    key={cand.id}
                                    className={`candidate-card-mini ${selectedMatches.includes(cand.id) ? 'selected' : ''}`}
                                    onClick={() => toggleCandidateSelection(cand.id)}
                                >
                                    <div className="mini-img">
                                        <LazyImage src={cand.image} alt={cand.title} />
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
                                            <span className="mini-id">#{cand.id}</span>
                                            <p className="mini-price">${cand.price}</p>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>

                {/* FOOTER ACTIONS */}
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
                            onClick={() => handleAction('TRASH')}
                            disabled={isProcessing}
                            title="Descartar producto (Basura/Irrelevante)"
                        >
                            <Trash2 size={18} />
                        </button>
                        <button
                            className="btn-secondary"
                            onClick={() => handleAction('CONFIRM_SINGLETON')}
                            disabled={isProcessing || selectedMatches.length > 0}
                            title="Es único en el mercado"
                        >
                            Confirmar como Único
                        </button>
                        <button
                            className="btn-primary"
                            onClick={() => handleAction('MERGE_SELECTED')}
                            disabled={isProcessing || selectedMatches.length === 0}
                        >
                            Unir Seleccionados
                        </button>
                    </div>
                </div>
            </div>

            <style jsx>{`
                /* MODAL SHELL */
                .audit-modal-overlay {
                    position: fixed; inset: 0; background: rgba(0,0,0,0.85); backdrop-filter: blur(5px);
                    display: flex; align-items: center; justify-content: center; z-index: 2000;
                }
                .investigator-modal {
                    width: 95vw; max-width: 1200px; height: 85vh; display: flex; flexDirection: column;
                    background: #0f172a; border-radius: 16px; border: 1px solid rgba(255,255,255,0.1); overflow: hidden;
                }

                /* HEADER */
                .glass-header {
                    padding: 1rem 1.5rem; background: rgba(255,255,255,0.03); border-bottom: 1px solid rgba(255,255,255,0.05);
                    display: flex; justify-content: space-between; align-items: center;
                }
                .header-title { display: flex; gap: 1rem; align-items: center; }
                .icon-diamond { font-size: 1.5rem; }
                .glass-header h3 { margin: 0; color: #fff; font-size: 1.1rem; }
                .subtitle { font-size: 0.8rem; color: #64748b; font-family: monospace; }
                .close-btn-round {
                    background: rgba(255,255,255,0.1); border: none; color: #fff; width: 32px; height: 32px;
                    border-radius: 50%; cursor: pointer; display: flex; align-items: center; justify-content: center;
                }
                .close-btn-round:hover { background: rgba(239, 68, 68, 0.8); }

                /* BODY LAYOUT */
                .investigator-body { flex: 1; display: flex; overflow: hidden; }
                
                /* SIDEBAR (TARGET) */
                .target-sidebar {
                    width: 300px; background: rgba(0,0,0,0.2); border-right: 1px solid rgba(255,255,255,0.05);
                    padding: 2rem; display: flex; flexDirection: column; align-items: center; text-align: center;
                }
                .img-frame {
                    width: 100%; aspect-ratio: 1; background: #000; border-radius: 12px; overflow: hidden;
                    border: 2px solid #6366f1; position: relative; margin-bottom: 1.5rem;
                }
                .badge-target {
                    position: absolute; top: 10px; left: 10px; background: #6366f1; color: #fff;
                    font-size: 0.7rem; font-weight: bold; padding: 2px 8px; border-radius: 4px;
                }
                .target-title { color: #fff; margin-bottom: 0.5rem; line-height: 1.4; font-size: 1rem; }
                .id-tag { font-family: monospace; color: #64748b; background: rgba(255,255,255,0.05); padding: 2px 6px; borderRadius: 4; font-size: 0.8rem; }
                .helper-text { font-size: 0.8rem; color: #6366f1; margin-top: auto; opacity: 0.8; }

                /* GRID (CANDIDATES) */
                .grid-container { flex: 1; padding: 2rem; overflow-y: auto; background: linear-gradient(to bottom right, #0f172a, #1e293b); }
                .candidates-grid {
                    display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1.5rem;
                }
                .candidate-card-mini {
                    background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.05);
                    border-radius: 12px; overflow: hidden; cursor: pointer; transition: all 0.2s;
                }
                .candidate-card-mini:hover { transform: translateY(-4px); background: rgba(255,255,255,0.05); }
                .candidate-card-mini.selected { border-color: #10b981; box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.3); }

                .mini-img { height: 160px; position: relative; background: #000; }
                .selection-overlay {
                    position: absolute; inset: 0; background: rgba(16, 185, 129, 0.4);
                    display: flex; align-items: center; justify-content: center;
                }
                .match-percent {
                    position: absolute; bottom: 5px; right: 5px; color: #fff; font-size: 0.7rem;
                    font-weight: bold; padding: 2px 6px; border-radius: 4px;
                }
                .mini-details { padding: 0.75rem; }
                .mini-title { color: #cbd5e1; font-size: 0.8rem; margin-bottom: 0.5rem; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
                .mini-id { color: #64748b; font-family: monospace; font-size: 0.7rem; }
                .mini-price { color: #fff; font-weight: bold; font-size: 0.9rem; margin: 0; }

                /* FOOTER */
                .investigator-footer {
                    padding: 1.5rem 2rem; background: rgba(255,255,255,0.03); border-top: 1px solid rgba(255,255,255,0.05);
                    display: flex; justify-content: space-between; align-items: center;
                }
                .status-msg { font-size: 0.9rem; font-weight: 500; }
                .action-buttons { display: flex; gap: 1rem; }
                button:disabled { opacity: 0.5; cursor: not-allowed; }
                
                .btn-primary { background: #6366f1; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 8px; font-weight: bold; cursor: pointer; }
                .btn-secondary { background: transparent; color: #94a3b8; border: 1px solid rgba(255,255,255,0.1); padding: 0.75rem 1.5rem; border-radius: 8px; cursor: pointer; }
                .btn-secondary:hover { background: rgba(255,255,255,0.05); color: #fff; }
                .btn-danger { background: rgba(239, 68, 68, 0.1); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.3); padding: 0.75rem; border-radius: 8px; cursor: pointer; width: 42px; display: flex; align-items: center; justify-content: center;}
                .btn-danger:hover { background: #ef4444; color: #fff; }
            `}</style>
        </div>
    );
};

export default OrphanInvestigator;
