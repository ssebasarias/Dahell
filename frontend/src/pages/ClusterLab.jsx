import React, { useState } from 'react';
import { Layers, Activity, AlertCircle, Search } from 'lucide-react';
import { useClusterLab } from '../hooks/useClusterLab';
import { investigateOrphan } from '../services/clusterService';
import AuditModal from '../components/domain/cluster/AuditModal';
import OrphanInvestigator from '../components/domain/cluster/OrphanInvestigator';
import LiveConsole from '../components/domain/cluster/live_console/LiveConsole';
import LazyImage from '../components/common/LazyImage';
import './ClusterLab.css';

const ClusterLab = () => {
    const { logs, orphans, metrics, loading, refreshData } = useClusterLab();

    const [activeTab, setActiveTab] = useState('audit');
    const [filterTab, setFilterTab] = useState('ALL');
    const [selectedLog, setSelectedLog] = useState(null);
    const [targetOrphan, setTargetOrphan] = useState(null);
    const [orphanCandidates, setOrphanCandidates] = useState([]);

    const handleOpenOrphanInvestigator = async (orphan) => {
        try {
            const data = await investigateOrphan(orphan.product_id);
            setTargetOrphan(data.target);
            setOrphanCandidates(data.candidates);
        } catch (err) {
            console.error(err);
        }
    };

    if (loading && !metrics) return <div style={{ padding: '2rem', color: '#fff' }}>Conectando al Núcleo Neuronal...</div>;

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
                <LiveConsole
                    logs={logs}
                    filterTab={filterTab}
                    setFilterTab={setFilterTab}
                    onSelectLog={setSelectedLog}
                    metrics={metrics}
                />
            )}

            {/* ORPHANS TAB */}
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
                                    <LazyImage src={orphan.image} alt="" />
                                </div>
                                <h4 style={{ fontSize: '0.9rem', marginBottom: '0.5rem', lineHeight: '1.4' }}>{orphan.title}</h4>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '0.8rem', color: '#94a3b8' }}>
                                    <span>ID: {orphan.product_id}</span>
                                    <span>${orphan.price}</span>
                                </div>
                                <button onClick={() => handleOpenOrphanInvestigator(orphan)} style={{
                                    width: '100%', margin: '1rem 0 0', padding: '0.5rem',
                                    background: 'rgba(99, 102, 241, 0.1)', border: '1px solid rgba(99, 102, 241, 0.3)',
                                    color: '#818cf8', borderRadius: 6, cursor: 'pointer'
                                }}>
                                    Investigar (Grid V3)
                                </button>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* MODALS */}
            {selectedLog && (
                <AuditModal log={selectedLog} onClose={() => setSelectedLog(null)} />
            )}

            {targetOrphan && (
                <OrphanInvestigator
                    orphan={targetOrphan}
                    candidates={orphanCandidates}
                    onClose={() => setTargetOrphan(null)}
                    onActionComplete={refreshData}
                />
            )}
        </div>
    );
};

export default ClusterLab;
