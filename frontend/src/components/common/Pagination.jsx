import React from 'react';

const Pagination = ({ currentPage, totalResults, itemsPerPage, onPageChange }) => {
    const totalPages = Math.ceil(totalResults / itemsPerPage);

    if (totalPages <= 1) return null;

    const getPageNumbers = () => {
        const pages = [];
        const maxVisible = 7;

        if (totalPages <= maxVisible) {
            for (let i = 1; i <= totalPages; i++) pages.push(i);
        } else {
            if (currentPage <= 4) {
                for (let i = 1; i <= 5; i++) pages.push(i);
                pages.push('...');
                pages.push(totalPages);
            } else if (currentPage >= totalPages - 3) {
                pages.push(1);
                pages.push('...');
                for (let i = totalPages - 4; i <= totalPages; i++) pages.push(i);
            } else {
                pages.push(1);
                pages.push('...');
                for (let i = currentPage - 1; i <= currentPage + 1; i++) pages.push(i);
                pages.push('...');
                pages.push(totalPages);
            }
        }
        return pages;
    };

    return (
        <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '0.5rem', padding: '1.5rem', borderTop: '1px solid rgba(255,255,255,0.1)' }}>
            <button
                onClick={() => onPageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="btn-pagination"
                style={{ opacity: currentPage === 1 ? 0.5 : 1, cursor: currentPage === 1 ? 'not-allowed' : 'pointer' }}
            >
                ← Anterior
            </button>

            {getPageNumbers().map((page, idx) => (
                page === '...' ? (
                    <span key={`ellipsis-${idx}`} style={{ color: '#64748b', padding: '0 0.5rem' }}>...</span>
                ) : (
                    <button
                        key={page}
                        onClick={() => onPageChange(page)}
                        className={`btn-pagination ${currentPage === page ? 'active' : ''}`}
                    >
                        {page}
                    </button>
                )
            ))}

            <button
                onClick={() => onPageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="btn-pagination"
                style={{ opacity: currentPage === totalPages ? 0.5 : 1, cursor: currentPage === totalPages ? 'not-allowed' : 'pointer' }}
            >
                Siguiente →
            </button>

            <style jsx>{`
                .btn-pagination {
                    padding: 0.5rem 0.75rem;
                    background: rgba(255,255,255,0.05);
                    border: 1px solid rgba(255,255,255,0.1);
                    color: #fff;
                    border-radius: 6px;
                    cursor: pointer;
                    font-size: 0.9rem;
                    min-width: 40px;
                    transition: all 0.2s;
                }
                .btn-pagination:hover:not(:disabled) {
                    background: rgba(255,255,255,0.1);
                }
                .btn-pagination.active {
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-color: #667eea;
                    font-weight: bold;
                }
            `}</style>
        </div>
    );
};

export default Pagination;
