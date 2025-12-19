import { useState, useEffect } from 'react';
import { fetchSystemLogs, fetchContainerStats } from '../services/systemService';

export const useSystemStatus = () => {
    const [logs, setLogs] = useState([]);
    const [stats, setStats] = useState({});
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let statsInterval, logsInterval;

        const loadStats = async () => {
            if (document.hidden) return;
            try {
                const s = await fetchContainerStats();
                setStats(s || {});
            } catch (e) {
                console.error("Stats Error:", e);
            }
        };

        const loadLogs = async () => {
            if (document.hidden) return;
            try {
                const l = await fetchSystemLogs();
                setLogs(l || []);
            } catch (e) {
                console.error("Logs Error:", e);
            }
        };

        const init = async () => {
            await Promise.all([loadStats(), loadLogs()]);
            setLoading(false);
        };

        init();

        statsInterval = setInterval(loadStats, 2000);
        logsInterval = setInterval(loadLogs, 5000);

        return () => {
            clearInterval(statsInterval);
            clearInterval(logsInterval);
        };
    }, []);

    return { logs, stats, loading };
};
