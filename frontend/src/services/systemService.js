// URL Base del Backend
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const fetchSystemLogs = async () => {
    try {
        const response = await fetch(`${API_URL}/system-logs/`);
        if (!response.ok) throw new Error('Network response was not ok');
        return await response.json();
    } catch (error) {
        return []; // Return empty on error to avoid crashing UI
    }
};

export const fetchContainerStats = async () => {
    try {
        const response = await fetch(`${API_URL}/control/stats/`);
        if (!response.ok) throw new Error('Stats fetch failed');
        return await response.json();
    } catch (error) {
        console.error("Error fetching container stats:", error);
        return {};
    }
};

export const controlContainer = async (service, action) => {
    try {
        const response = await fetch(`${API_URL}/control/container/${service}/${action}/`, {
            method: 'POST'
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.error || 'Action failed');
        return data;
    } catch (error) {
        console.error(`Error controlling ${service}:`, error);
        throw error;
    }
};
