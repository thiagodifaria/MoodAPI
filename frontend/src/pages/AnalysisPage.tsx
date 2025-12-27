/**
 * Analysis Page - Análise de sentimentos (single e batch)
 */
import { useState, useEffect } from 'react';
import { Send, Layers, Plus, X, Loader2, CheckCircle, AlertCircle } from 'lucide-react';
import { IndustrialCard, SentimentBadge } from '../components';
import { api } from '../services/api';
import type { AnalysisResponse } from '../types';

// Default examples - can be customized in Settings
const DEFAULT_EXAMPLES = {
    pt: [
        'Estou muito feliz com o atendimento!',
        'Péssima experiência, não recomendo.',
        'O produto chegou dentro do prazo previsto.',
        'Adorei! Superou minhas expectativas.',
        'Infelizmente não funcionou como esperado.',
    ],
    en: [
        'I am very happy with this service!',
        'Terrible experience, would not recommend.',
        'The product arrived on time as expected.',
        'Amazing! Exceeded my expectations.',
        'Unfortunately it did not work as expected.',
    ],
};

interface AnalysisResultWithText extends AnalysisResponse {
    originalText: string;
}

export function AnalysisPage() {
    const [mode, setMode] = useState<'single' | 'batch'>('single');
    const [singleText, setSingleText] = useState('');
    const [batchTexts, setBatchTexts] = useState<string[]>(['']);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<AnalysisResultWithText[]>([]);
    const [error, setError] = useState<string | null>(null);
    const [examples, setExamples] = useState(DEFAULT_EXAMPLES);

    // Load examples from localStorage
    useEffect(() => {
        const saved = localStorage.getItem('moodapi_examples');
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                if (parsed.pt && parsed.en) {
                    setExamples(parsed);
                }
            } catch {
                console.error('Failed to parse saved examples');
            }
        }
    }, []);

    async function handleAnalyzeSingle() {
        if (!singleText.trim()) return;

        setLoading(true);
        setError(null);

        try {
            const result = await api.analyze(singleText);
            setResults([{ ...result, originalText: singleText }]);
        } catch (err) {
            setError('Falha ao analisar o texto. Tente novamente.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }

    async function handleAnalyzeBatch() {
        const validTexts = batchTexts.filter(t => t.trim());
        if (validTexts.length === 0) return;

        setLoading(true);
        setError(null);

        try {
            const result = await api.analyzeBatch(validTexts);
            const newResults: AnalysisResultWithText[] = result.results.map((r, idx) => ({
                ...r,
                originalText: validTexts[idx],
            }));
            setResults(newResults);
        } catch (err) {
            setError('Falha ao analisar em lote. Tente novamente.');
            console.error(err);
        } finally {
            setLoading(false);
        }
    }

    function addBatchInput() {
        setBatchTexts([...batchTexts, '']);
    }

    function removeBatchInput(index: number) {
        setBatchTexts(batchTexts.filter((_, i) => i !== index));
    }

    function updateBatchInput(index: number, value: string) {
        const updated = [...batchTexts];
        updated[index] = value;
        setBatchTexts(updated);
    }

    function loadExample(text: string) {
        if (mode === 'single') {
            setSingleText(text);
        } else {
            setBatchTexts([...batchTexts.filter(t => t.trim()), text]);
        }
    }

    function clearResults() {
        setResults([]);
        setError(null);
    }

    return (
        <div className="space-y-6 animate-slide-in-bottom">
            <div className="flex justify-between items-start">
                <div>
                    <h2 className="text-2xl font-bold text-slate-100">Análise de Sentimentos</h2>
                    <p className="text-slate-500 text-sm font-mono mt-1">
                        Analise textos individualmente ou em lote.
                    </p>
                </div>

                {/* Mode Toggle */}
                <div className="flex bg-slate-900 border border-slate-700 rounded-lg p-1">
                    <button
                        onClick={() => setMode('single')}
                        className={`px-4 py-2 rounded-md text-sm font-mono transition-all ${mode === 'single'
                            ? 'bg-amber-600 text-white'
                            : 'text-slate-400 hover:text-white'
                            }`}
                    >
                        Individual
                    </button>
                    <button
                        onClick={() => setMode('batch')}
                        className={`px-4 py-2 rounded-md text-sm font-mono transition-all flex items-center gap-2 ${mode === 'batch'
                            ? 'bg-amber-600 text-white'
                            : 'text-slate-400 hover:text-white'
                            }`}
                    >
                        <Layers size={14} /> Batch
                    </button>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-stretch">
                {/* Input Section */}
                <div className="lg:col-span-2 flex">
                    <IndustrialCard title={mode === 'single' ? 'Texto para Análise' : 'Textos para Análise em Lote'} icon={Send} className="flex-1 flex flex-col">
                        <div className="space-y-4 flex-1 flex flex-col">
                            {mode === 'single' ? (
                                <textarea
                                    value={singleText}
                                    onChange={(e) => setSingleText(e.target.value)}
                                    placeholder="Digite ou cole o texto para analisar o sentimento..."
                                    className="w-full flex-1 min-h-[200px] bg-slate-950 border border-slate-700 rounded-lg p-4 text-slate-200 placeholder-slate-600 font-mono text-sm resize-none focus:border-amber-500/50 focus:ring-1 focus:ring-amber-500/20 outline-none transition-all"
                                />
                            ) : (
                                <div className="space-y-3 max-h-80 overflow-y-auto pr-2">
                                    {batchTexts.map((text, idx) => (
                                        <div key={idx} className="flex gap-2">
                                            <span className="text-slate-600 font-mono text-xs w-6 pt-3">{idx + 1}.</span>
                                            <input
                                                type="text"
                                                value={text}
                                                onChange={(e) => updateBatchInput(idx, e.target.value)}
                                                placeholder={`Texto ${idx + 1}...`}
                                                className="flex-1 bg-slate-950 border border-slate-700 rounded px-3 py-2 text-slate-200 placeholder-slate-600 font-mono text-sm focus:border-amber-500/50 outline-none transition-all"
                                            />
                                            {batchTexts.length > 1 && (
                                                <button
                                                    onClick={() => removeBatchInput(idx)}
                                                    className="text-slate-600 hover:text-rose-500 transition-colors p-2"
                                                >
                                                    <X size={16} />
                                                </button>
                                            )}
                                        </div>
                                    ))}
                                    <button
                                        onClick={addBatchInput}
                                        className="flex items-center gap-2 text-amber-500 hover:text-amber-400 text-sm font-mono"
                                    >
                                        <Plus size={14} /> Adicionar texto
                                    </button>
                                </div>
                            )}

                            <div className="flex gap-3 pt-2">
                                <button
                                    onClick={mode === 'single' ? handleAnalyzeSingle : handleAnalyzeBatch}
                                    disabled={loading || (mode === 'single' ? !singleText.trim() : batchTexts.every(t => !t.trim()))}
                                    className="flex-1 bg-amber-600 hover:bg-amber-500 disabled:bg-slate-700 disabled:text-slate-500 text-white py-3 rounded-lg font-mono text-sm uppercase tracking-wide flex items-center justify-center gap-2 transition-colors"
                                >
                                    {loading ? (
                                        <>
                                            <Loader2 size={16} className="animate-spin" /> Analisando...
                                        </>
                                    ) : (
                                        <>
                                            <Send size={16} /> Analisar {mode === 'batch' && `(${batchTexts.filter(t => t.trim()).length})`}
                                        </>
                                    )}
                                </button>
                                {results.length > 0 && (
                                    <button
                                        onClick={clearResults}
                                        className="px-4 py-3 border border-slate-700 text-slate-400 hover:text-white hover:border-slate-600 rounded-lg font-mono text-sm transition-colors"
                                    >
                                        Limpar
                                    </button>
                                )}
                            </div>

                            {error && (
                                <div className="flex items-center gap-2 text-rose-400 text-sm bg-rose-500/10 border border-rose-500/30 rounded-lg p-3">
                                    <AlertCircle size={16} />
                                    {error}
                                </div>
                            )}
                        </div>
                    </IndustrialCard>
                </div>

                {/* Examples Section */}
                <div className="flex">
                    <IndustrialCard title="Exemplos Rápidos" icon={Layers} className="flex-1">
                        <div className="space-y-4">
                            <div>
                                <h4 className="text-xs text-slate-500 uppercase font-bold mb-2">Português</h4>
                                <div className="space-y-2">
                                    {examples.pt.map((ex, idx) => (
                                        <button
                                            key={idx}
                                            onClick={() => loadExample(ex)}
                                            className="w-full text-left text-xs text-slate-400 hover:text-amber-500 bg-slate-950 hover:bg-slate-900 border border-slate-800 hover:border-amber-500/30 rounded p-2 transition-all truncate"
                                        >
                                            "{ex}"
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div>
                                <h4 className="text-xs text-slate-500 uppercase font-bold mb-2">English</h4>
                                <div className="space-y-2">
                                    {examples.en.map((ex, idx) => (
                                        <button
                                            key={idx}
                                            onClick={() => loadExample(ex)}
                                            className="w-full text-left text-xs text-slate-400 hover:text-amber-500 bg-slate-950 hover:bg-slate-900 border border-slate-800 hover:border-amber-500/30 rounded p-2 transition-all truncate"
                                        >
                                            "{ex}"
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <p className="text-[10px] text-slate-600 text-center pt-2 border-t border-slate-800">
                                Configure exemplos em Configurações
                            </p>
                        </div>
                    </IndustrialCard>
                </div>
            </div>

            {/* Results Section */}
            {results.length > 0 && (
                <IndustrialCard title={`Resultados (${results.length})`} icon={CheckCircle}>
                    <div className="space-y-3">
                        {results.map((result, idx) => (
                            <div
                                key={idx}
                                className="bg-slate-950 border border-slate-800 rounded-lg p-4 hover:border-slate-700 transition-colors"
                            >
                                <div className="flex items-start justify-between gap-4">
                                    <div className="flex-1 min-w-0">
                                        <p className="text-slate-300 text-sm font-mono truncate mb-2">
                                            "{result.originalText}"
                                        </p>
                                        <div className="flex items-center gap-4 text-xs text-slate-500">
                                            {result.record_id && <span>ID: {result.record_id.slice(0, 8)}...</span>}
                                            <span>Idioma: {result.language?.toUpperCase()}</span>
                                            <span>Tempo: {result.response_time_ms?.toFixed(0) || 0}ms</span>
                                        </div>
                                    </div>
                                    <div className="text-right shrink-0">
                                        <SentimentBadge sentiment={result.sentiment} />
                                        <p className="text-xs text-slate-500 mt-1">
                                            {(result.confidence * 100).toFixed(1)}%
                                        </p>
                                    </div>
                                </div>

                                {/* Score breakdown */}
                                {result.all_scores && result.all_scores.length > 0 && (
                                    <div className="mt-3 pt-3 border-t border-slate-800">
                                        <div className="flex gap-2 flex-wrap">
                                            {result.all_scores.map((scoreItem) => (
                                                <div
                                                    key={scoreItem.label}
                                                    className="bg-slate-900 border border-slate-700 rounded px-2 py-1 text-xs"
                                                >
                                                    <span className="text-slate-500">{scoreItem.label}:</span>{' '}
                                                    <span className="text-slate-300 font-mono">{(scoreItem.score * 100).toFixed(1)}%</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </IndustrialCard>
            )}
        </div>
    );
}

export default AnalysisPage;
