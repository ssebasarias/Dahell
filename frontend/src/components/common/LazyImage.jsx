import React from 'react';
import { ShoppingBag } from 'lucide-react';

const LazyImage = ({ src, alt, style, className }) => {
    const [loaded, setLoaded] = React.useState(false);
    const [error, setError] = React.useState(false);

    if (error || !src) {
        return (
            <div className={`lazy-placeholder ${className}`} style={{ ...style, display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#334155' }}>
                <ShoppingBag size={24} color="#94a3b8" />
            </div>
        );
    }

    return (
        <img
            src={src}
            alt={alt}
            className={className}
            style={{ ...style, opacity: loaded ? 1 : 0, transition: 'opacity 0.3s' }}
            onLoad={() => setLoaded(true)}
            onError={() => setError(true)}
        />
    );
};

export default LazyImage;
