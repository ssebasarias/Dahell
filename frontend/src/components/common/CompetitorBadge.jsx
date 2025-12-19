import React from 'react';
import { Users } from 'lucide-react';

const CompetitorBadge = ({ count, showLabel = false }) => {
    let color = '#10b981'; // Green (Low)
    let label = 'Baja';

    if (count > 2) {
        color = '#f59e0b'; // Medium
        label = 'Media';
    }
    if (count > 5) {
        color = '#ef4444'; // High
        label = 'Alta';
    }

    return (
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Users size={16} color={color} />
            <span style={{ color: showLabel ? color : 'inherit', fontWeight: showLabel ? 'bold' : 'normal' }}>
                {count} {showLabel && `(${label})`}
            </span>
        </div>
    );
};

export default CompetitorBadge;
