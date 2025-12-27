/**
 * Dashboard Page - Página principal com métricas, gráficos e logs
 */
import { useState, useEffect } from 'react';
import {
    Hash, Clock, Database, Cpu, Activity, Terminal,
    RefreshCw, CheckCircle2
} from 'lucide-react';
import {
    AreaChart, Area, XAxis, YAxis,
    CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar
} from 'recharts';
import { IndustrialCard, MetricValue, SentimentBadge, TextDetailModal } from '../components';
import { api } from '../services/api';
import type { HistoryItem, HealthResponse, StatsResponse } from '../types';

export function DashboardPage() {
    const [history, setHistory] = useState<HistoryItem[]>([]);
    const [stats, setStats] = useState<StatsResponse | null>(null);
    const [health, setHealth] = useState<HealthResponse | null>(null);
    const [timeData, setTimeData] = useState<Array<{ time: string; requests: number; confidence: number }>>([]);
    const [sentimentData, setSentimentData] = useState<Array<{ name: string; value: number; fill: string }>>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedItem, setSelectedItem] = useState<HistoryItem | null>(null);

    // Load initial data
    useEffect(() => {
        loadData();
        const interval = setInterval(loadData, 30000); // Refresh every 30s
        return () => clearInterval(interval);
    }, []);

    async function loadData() {
        try {
            setError(null);

            // Load in parallel
            const [historyRes, statsRes, healthRes] = await Promise.all([
                api.getHistory({ limit: 20, sort_by: 'created_at', sort_order: 'desc' }).catch(() => null),
                api.getStats(7).catch(() => null),
                api.getSentimentHealth().catch(() => null)
            ]);

            if (historyRes) setHistory(historyRes.items);
            if (statsRes) setStats(statsRes);
            if (healthRes) setHealth(healthRes);

            // Build time data from history
            if (historyRes?.items) {
                const timePoints = historyRes.items.slice(0, 12).reverse().map((item) => ({
                    time: new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                    requests: 1,
                    confidence: Math.round(item.confidence * 100)
                }));
                setTimeData(timePoints);

                // Build sentiment distribution
                const sentimentCount: Record<string, number> = {};
                historyRes.items.forEach(item => {
                    sentimentCount[item.sentiment] = (sentimentCount[item.sentiment] || 0) + 1;
                });

                const colors: Record<string, string> = {
                    'POSITIVE': '#10b981',
                    'NEGATIVE': '#ef4444',
                    'NEUTRAL': '#6b7280',
                    'positive': '#10b981',
                    'negative': '#ef4444',
                    'neutral': '#6b7280',
                };

                setSentimentData(Object.entries(sentimentCount).map(([name, value]) => ({
                    name: name.toUpperCase(),
                    value,
                    fill: colors[name] || '#f59e0b'
                })));

                // Fallback stats calculation from history if /stats failed
                if (!statsRes && historyRes.items.length > 0) {
                    const items = historyRes.items;
                    const totalAnalyses = historyRes.pagination?.total || items.length;
                    const avgConfidence = items.reduce((sum, item) => sum + item.confidence, 0) / items.length;
                    const highConfidenceCount = items.filter(item => item.confidence >= 0.8).length;
                    const highConfidencePercentage = (highConfidenceCount / items.length) * 100;

                    setStats({
                        total_analyses: totalAnalyses,
                        avg_confidence: avgConfidence,
                        high_confidence_percentage: highConfidencePercentage,
                        sentiment_distribution: {
                            positive: sentimentCount['positive'] || 0,
                            negative: sentimentCount['negative'] || 0,
                            neutral: sentimentCount['neutral'] || 0
                        },
                        top_languages: [],
                        period: '7d',
                        sentiment_trend: [],
                        timestamp: new Date().toISOString()
                    });
                }
            }

        } catch (err) {
            console.error('Failed to load data:', err);
            setError('Falha ao carregar dados. Verifique a conexão com a API.');
        } finally {
            setLoading(false);
        }
    }

    const systemStats = {
        requests: stats?.total_analyses || 0,
        avgConfidence: Math.round((stats?.avg_confidence || 0) * 100),
        highConfidenceRate: stats?.high_confidence_percentage || 0
    };

    const modelLoaded = health?.model_info?.model_loaded ?? false;
    const modelName = health?.model_info?.model_name?.split('/').pop() || 'roberta-base';

    return (
        <div className="space-y-6 animate-fade-in">
            {error && (
                <div className="bg-rose-500/10 border border-rose-500/30 text-rose-400 px-4 py-3 rounded text-sm">
                    {error}
                </div>
            )}

            {/* KPI ROW */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <IndustrialCard title="Total de Análises" icon={Hash}>
                    <MetricValue
                        label="Período"
                        value={systemStats.requests.toLocaleString()}
                        trend={12}
                        subLabel="Últimos 7 dias"
                    />
                </IndustrialCard>

                <IndustrialCard title="Confiança Média" icon={Clock}>
                    <MetricValue
                        label="Precisão"
                        value={systemStats.avgConfidence}
                        unit="%"
                        trend={5}
                        subLabel="Meta: >80%"
                    />
                </IndustrialCard>

                <IndustrialCard title="Alta Confiança" icon={Database}>
                    <MetricValue
                        label="Taxa >80%"
                        value={systemStats.highConfidenceRate.toFixed(1)}
                        unit="%"
                        subLabel="Análises precisas"
                    />
                    <div className="w-full bg-slate-800 h-1 mt-3 rounded-full overflow-hidden">
                        <div
                            className="bg-emerald-500 h-full transition-all duration-1000"
                            style={{ width: `${systemStats.highConfidenceRate}%` }}
                        />
                    </div>
                </IndustrialCard>

                <IndustrialCard title="Saúde do Modelo" icon={Cpu}>
                    <div className="flex flex-col h-full justify-between">
                        <div>
                            <span className="text-slate-500 text-xs font-mono uppercase">Status</span>
                            <div className={`font-mono font-bold flex items-center gap-2 mt-1 ${modelLoaded ? 'text-emerald-400' : 'text-amber-400'
                                }`}>
                                {modelLoaded ? (
                                    <>
                                        <CheckCircle2 size={16} /> OPERACIONAL
                                    </>
                                ) : (
                                    <>
                                        <RefreshCw size={16} className="animate-spin" /> CARREGANDO
                                    </>
                                )}
                            </div>
                        </div>
                        <div className="text-[10px] text-slate-500 font-mono border-t border-slate-800 pt-2 mt-2">
                            Modelo: {modelName}<br />
                            Device: {health?.model_info?.device || 'CPU'}
                        </div>
                    </div>
                </IndustrialCard>
            </div>

            {/* CHARTS ROW - Full Width */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                {/* CONFIDENCE TIMELINE CHART */}
                <IndustrialCard title="Histórico de Confiança" className="lg:col-span-2" icon={Activity}>
                    <div className="w-full" style={{ height: '280px' }}>
                        {timeData.length > 0 ? (
                            <ResponsiveContainer width="100%" height={280}>
                                <AreaChart data={timeData}>
                                    <defs>
                                        <linearGradient id="colorConfidence" x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                                    <XAxis
                                        dataKey="time"
                                        stroke="#64748b"
                                        tick={{ fontSize: 10, fontFamily: 'monospace' }}
                                        tickLine={false}
                                        axisLine={false}
                                    />
                                    <YAxis
                                        stroke="#64748b"
                                        tick={{ fontSize: 10, fontFamily: 'monospace' }}
                                        tickLine={false}
                                        axisLine={false}
                                        domain={[0, 100]}
                                    />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#cbd5e1' }}
                                        itemStyle={{ color: '#fbbf24', fontFamily: 'monospace' }}
                                        labelStyle={{ color: '#94a3b8', fontSize: '12px', marginBottom: '5px' }}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="confidence"
                                        stroke="#f59e0b"
                                        fillOpacity={1}
                                        fill="url(#colorConfidence)"
                                        strokeWidth={2}
                                        name="Confiança %"
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="flex items-center justify-center h-full text-slate-600 text-sm">
                                {loading ? 'Carregando...' : 'Sem dados disponíveis'}
                            </div>
                        )}
                    </div>
                </IndustrialCard>

                {/* SENTIMENT DISTRIBUTION CHART */}
                <IndustrialCard title="Distribuição de Sentimentos" icon={Activity}>
                    <div className="w-full" style={{ height: '280px' }}>
                        {sentimentData.length > 0 ? (
                            <ResponsiveContainer width="100%" height={280}>
                                <BarChart data={sentimentData} layout="vertical">
                                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" horizontal={false} />
                                    <XAxis type="number" stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} />
                                    <YAxis dataKey="name" type="category" stroke="#64748b" tick={{ fontSize: 10, fontFamily: 'monospace' }} width={80} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#0f172a', borderColor: '#334155', color: '#cbd5e1' }}
                                        itemStyle={{ fontFamily: 'monospace' }}
                                    />
                                    <Bar dataKey="value" name="Quantidade" radius={[0, 4, 4, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="flex items-center justify-center h-full text-slate-600 text-sm">
                                {loading ? 'Carregando...' : 'Sem dados disponíveis'}
                            </div>
                        )}
                    </div>
                </IndustrialCard>
            </div>

            {/* RECENT LOGS */}
            <IndustrialCard title="Análises Recentes" icon={Terminal}>
                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b border-slate-800 text-xs text-slate-500 uppercase font-mono tracking-wider">
                                <th className="p-3 font-medium">Horário</th>
                                <th className="p-3 font-medium">ID</th>
                                <th className="p-3 font-medium">Idioma</th>
                                <th className="p-3 font-medium text-center">Sentimento</th>
                                <th className="p-3 font-medium text-right">Confiança</th>
                            </tr>
                        </thead>
                        <tbody className="text-sm font-mono text-slate-400">
                            {history.length > 0 ? (
                                history.slice(0, 8).map((row) => (
                                    <tr key={row.id} className="border-b border-slate-800/50 hover:bg-slate-800/30 transition-colors cursor-pointer" onClick={() => setSelectedItem(row)}>
                                        <td className="p-3 text-slate-500">
                                            {new Date(row.created_at).toLocaleTimeString()}
                                        </td>
                                        <td className="p-3 text-xs opacity-70">{row.id.slice(0, 12)}...</td>
                                        <td className="p-3">
                                            <span className="px-2 py-0.5 rounded bg-slate-800 text-slate-300 text-[10px] uppercase border border-slate-700">
                                                {row.language}
                                            </span>
                                        </td>
                                        <td className="p-3 text-center">
                                            <SentimentBadge sentiment={row.sentiment} />
                                        </td>
                                        <td className="p-3 text-right">{(row.confidence * 100).toFixed(1)}%</td>
                                    </tr>
                                ))
                            ) : (
                                <tr>
                                    <td colSpan={5} className="p-8 text-center text-slate-600 italic">
                                        {loading ? 'Carregando...' : 'Nenhuma análise encontrada'}
                                    </td>
                                </tr>
                            )}
                        </tbody>
                    </table>
                </div>
            </IndustrialCard>

            {/* Text Detail Modal */}
            <TextDetailModal item={selectedItem} onClose={() => setSelectedItem(null)} />
        </div>
    );
}

export default DashboardPage;
