/**
 * Logs Page - Histórico completo com filtros e pesquisa
 */
import { useState, useEffect, useCallback } from 'react';
import { Search, Download, Filter, Terminal, Trash2, Eye } from 'lucide-react';
import { IndustrialCard, SentimentBadge, TextDetailModal } from '../components';
import { api } from '../services/api';
import type { HistoryItem, HistoryFilters, Sentiment } from '../types';

export function LogsPage() {
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [total, setTotal] = useState(0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null);

    // Filters
    const [searchTerm, setSearchTerm] = useState('');
    const [filterSentiment, setFilterSentiment] = useState<Sentiment | 'all'>('all');
    const [page, setPage] = useState(1);
    const limit = 15;

    const loadHistory = useCallback(async () => {
        setLoading(true);
        setError(null);

        try {
            const filters: HistoryFilters = {
                page,
                limit,
                sort_by: 'created_at',
                sort_order: 'desc'
            };

            if (filterSentiment !== 'all') {
                filters.sentiment = filterSentiment;
            }

            const response = await api.getHistory(filters);

            // Client-side text filter
            let items = response.items;
            if (searchTerm) {
                items = items.filter(item =>
                    item.text.toLowerCase().includes(searchTerm.toLowerCase()) ||
                    item.id.includes(searchTerm)
                );
            }

            setHistory(items);
            setTotal(response.pagination.total);
        } catch (err) {
            console.error('Failed to load history:', err);
            setError('Falha ao carregar histórico');
        } finally {
            setLoading(false);
        }
    }, [page, filterSentiment, searchTerm]);

    useEffect(() => {
        loadHistory();
    }, [loadHistory]);

    async function handleDelete(id: string) {
        if (!confirm('Tem certeza que deseja excluir esta análise?')) return;

        try {
            await api.deleteAnalysis(id);
            setHistory(prev => prev.filter(item => item.id !== id));
            setTotal(prev => prev - 1);
        } catch (err) {
            console.error('Failed to delete:', err);
            setError('Falha ao excluir análise');
        }
    }

    function handleExportCSV() {
        const headers = ['ID', 'Texto', 'Sentimento', 'Confiança', 'Idioma', 'Data'];
        const rows = history.map(item => [
            item.id,
            `"${item.text.replace(/"/g, '""')}"`,
            item.sentiment,
            item.confidence,
            item.language,
            item.created_at
        ]);

        const csv = [headers.join(','), ...rows.map(r => r.join(','))].join('\n');
        const blob = new Blob([csv], { type: 'text/csv' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `moodapi_history_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
        URL.revokeObjectURL(url);
    }

    const totalPages = Math.ceil(total / limit);

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex flex-col md:flex-row gap-4 justify-between items-end md:items-center">
                <div>
                    <h2 className="text-2xl font-bold text-slate-100">Histórico de Requisições</h2>
                    <p className="text-slate-500 text-sm font-mono mt-1">
                        Total de registros: {total.toLocaleString()}
                    </p>
                </div>
                <button
                    onClick={handleExportCSV}
                    className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-slate-300 px-3 py-2 rounded text-sm transition-colors border border-slate-700"
                >
                    <Download size={16} /> Exportar CSV
                </button>
            </div>

            {error && (
                <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 px-4 py-3 rounded text-sm">
                    {error}
                </div>
            )}

            {/* Filters */}
            <IndustrialCard title="Filtros & Pesquisa" icon={Filter} className="border-slate-800 bg-slate-900/50">
                <div className="flex flex-col md:flex-row gap-4">
                    <div className="flex-1 relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
                        <input
                            type="text"
                            placeholder="Buscar por ID ou conteúdo do texto..."
                            className="w-full bg-slate-950 border border-slate-700 rounded pl-10 pr-4 py-2 text-sm text-slate-300 focus:outline-none focus:border-amber-500 font-mono"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                    </div>
                    <div className="flex gap-2">
                        <select
                            className="bg-slate-950 border border-slate-700 rounded px-4 py-2 text-sm text-slate-300 focus:outline-none focus:border-amber-500 font-mono"
                            value={filterSentiment}
                            onChange={(e) => setFilterSentiment(e.target.value as Sentiment | 'all')}
                        >
                            <option value="all">Todos os Sentimentos</option>
                            <option value="positive">Positive</option>
                            <option value="neutral">Neutral</option>
                            <option value="negative">Negative</option>
                        </select>
                        <button
                            onClick={() => { setPage(1); loadHistory(); }}
                            className="bg-amber-600 hover:bg-amber-500 text-white px-4 py-2 rounded font-medium transition-colors"
                        >
                            Filtrar
                        </button>
                    </div>
                </div>
            </IndustrialCard>

            {/* Table */}
            <IndustrialCard title="Detalhes do Tráfego" icon={Terminal}>
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-slate-800 text-xs text-slate-500 uppercase font-mono tracking-wider">
                                <th className="p-3 font-medium">Status</th>
                                <th className="p-3 font-medium">Timestamp</th>
                                <th className="p-3 font-medium">ID</th>
                                <th className="p-3 font-medium">Idioma</th>
                                <th className="p-3 font-medium text-center">Sentimento</th>
                                <th className="p-3 font-medium text-right">Conf.</th>
                                <th className="p-3 font-medium text-center">Ações</th>
                            </tr>
                        </thead>
                        <tbody className="text-sm font-mono text-slate-400">
                            {loading ? (
                                <tr>
                                    <td colSpan={7} className="p-8 text-center text-slate-600">
                                        Carregando...
                                    </td>
                                </tr>
                            ) : history.length > 0 ? (
                                history.map((row) => (
                                    <tr key={row.id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors cursor-pointer" onClick={() => setSelectedItem(row)}>
                                        <td className="p-3">
                                            <div className={`w-2 h-2 rounded-full ${row.confidence > 0.8 ? 'bg-emerald-500' : 'bg-amber-500'
                                                }`} />
                                        </td>
                                        <td className="p-3 text-slate-500">
                                            {new Date(row.created_at).toLocaleString()}
                                        </td>
                                        <td className="p-3 text-xs opacity-70">{row.id.slice(0, 12)}...</td>
                                        <td className="p-3 uppercase text-xs">{row.language}</td>
                                        <td className="p-3 text-center">
                                            <SentimentBadge sentiment={row.sentiment} />
                                        </td>
                                        <td className="p-3 text-right">{(row.confidence * 100).toFixed(1)}%</td>
                                        <td className="p-3 text-center flex gap-1 justify-center">
                                            <button
                                                onClick={(e) => { e.stopPropagation(); setSelectedItem(row); }}
                                                className="text-slate-600 hover:text-amber-500 transition-colors p-1"
                                                title="Ver detalhes"
                                            >
                                                <Eye size={14} />
                                            </button>
                                            <button
                                                onClick={(e) => { e.stopPropagation(); handleDelete(row.id); }}
                                                className="text-slate-600 hover:text-rose-500 transition-colors p-1"
                                                title="Excluir"
                                            >
                                                <Trash2 size={14} />
                                            </button>
                                        </td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={7} className="p-8 text-center text-slate-600 italic">
                                        Nenhum registro encontrado para os filtros atuais.
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Pagination */}
                {totalPages > 1 && (
                    <div className="flex justify-center gap-2 mt-4 pt-4 border-t border-slate-800">
                        <button
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={page === 1}
                            className="px-3 py-1 bg-slate-800 text-slate-400 rounded disabled:opacity-50 text-sm"
                        >
                            Anterior
                        </button>
                        <span className="px-3 py-1 text-slate-500 text-sm font-mono">
                            {page} / {totalPages}
                        </span>
                        <button
                            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                            disabled={page === totalPages}
                            className="px-3 py-1 bg-slate-800 text-slate-400 rounded disabled:opacity-50 text-sm"
                        >
                            Próximo
                        </button>
                    </div>
                )}
            </IndustrialCard>

            {/* Text Detail Modal */}
            <TextDetailModal item={selectedItem} onClose={() => setSelectedItem(null)} />
        </div>
    );
}

export default LogsPage;
