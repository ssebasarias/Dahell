import React from 'react';
import { Server, Database, Activity, Cpu, Power, AlertCircle } from 'lucide-react';
import { useSystemStatus } from '../hooks/useSystemStatus';
import ServiceCard from '../components/domain/system/ServiceCard';
import LogTerminal from '../components/domain/system/LogTerminal';
import './Dashboard.css';

const SystemStatus = () => {
    const { logs, stats, loading } = useSystemStatus();

    const serviceConfig = [
        { id: 'scraper', name: 'Web Scraper', icon: Activity, actions: ['restart'] },
        { id: 'loader', name: 'Data Loader', icon: Database, actions: ['restart'] },
        { id: 'vectorizer', name: 'AI Vectorizer', icon: Cpu, actions: ['restart'] },
        { id: 'classifier', name: 'Agent 1: Classifier', icon: Server, actions: ['restart'] },
        { id: 'clusterizer', name: 'Agent 2: Clusterizer', icon: Server, actions: ['restart'] },
        { id: 'market_agent', name: 'Agent 3: Market (MELI)', icon: Activity, actions: ['restart'] },
        { id: 'amazon_explorer', name: 'Agent 4: Amazon US', icon: Activity, actions: ['restart'] },
        { id: 'ai_trainer', name: 'AI Trainer (Cerebro)', icon: Activity, actions: ['restart'] },
    ];

    if (loading && Object.keys(stats).length === 0) return <div style={{ padding: '2rem', color: '#fff' }}>Connecting to Command Center...</div>;

    return (
        <div className="dashboard-container" style={{ maxWidth: '1600px', margin: '0 auto', padding: '2rem' }}>
            <div className="header-greeting" style={{ textAlign: 'center', marginBottom: '3rem' }}>
                <h1 style={{ fontSize: '2.5rem', background: 'linear-gradient(to right, #fff, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                    Command Center
                </h1>
                <p style={{ color: '#64748b' }}>Infraestructure Management & Real-time Telemetry</p>
            </div>

            {/* CONTROL PANEL */}
            <div style={{
                background: 'rgba(255,255,255,0.02)',
                borderRadius: '16px',
                padding: '2rem',
                border: '1px solid rgba(255,255,255,0.05)',
                marginBottom: '3rem'
            }}>
                <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#e2e8f0' }}>
                    <Power size={20} color="#3b82f6" /> Active Services Control
                </h3>

                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem' }}>
                    {serviceConfig.map(svc => (
                        <ServiceCard
                            key={svc.id}
                            {...svc}
                            displayParams={stats[svc.id]}
                        />
                    ))}
                </div>
            </div>

            {/* LOGS SECTION */}
            <div>
                <h3 style={{ marginBottom: '1.5rem', color: '#e2e8f0', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <AlertCircle size={20} color="#f59e0b" /> Live Execution Logs
                </h3>
                <div style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
                    gap: '1.5rem'
                }}>
                    <LogTerminal title="scraper" logs={logs} color="#f59e0b" />
                    <LogTerminal title="loader" logs={logs} color="#3b82f6" />
                    <LogTerminal title="vectorizer" logs={logs} color="#a855f7" />
                    <LogTerminal title="classifier" logs={logs} color="#ec4899" />
                    <LogTerminal title="clusterizer" logs={logs} color="#10b981" />
                    <LogTerminal title="market_agent" logs={logs} color="#FACC15" />
                    <LogTerminal title="amazon_explorer" logs={logs} color="#F97316" />
                    <LogTerminal title="ai_trainer" logs={logs} color="#ec4899" />
                </div>
            </div>
        </div>
    );
};

export default SystemStatus;
