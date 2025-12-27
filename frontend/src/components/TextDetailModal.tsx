/**
 * TextDetailModal - Modal para exibir detalhes de uma análise
 */
import { X, Copy, Check } from 'lucide-react';
import { useState } from 'react';
import { SentimentBadge } from './SentimentBadge';
import type { HistoryItem } from '../types';

interface TextDetailModalProps {
    item: HistoryItem | null;
    onClose: () => void;
}

export function TextDetailModal({ item, onClose }: TextDetailModalProps) {
    const [copied, setCopied] = useState(false);

    if (!item) return null;

    function handleCopy() {
        navigator.clipboard.writeText(item!.text);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    }

    return (
        <div className="fixed inset-0 bg-black/70 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
            <div
                className="bg-slate-900 border border-slate-700 rounded-xl max-w-2xl w-full max-h-[80vh] overflow-hidden shadow-2xl"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-slate-800">
                    <div className="flex items-center gap-3">
                        <SentimentBadge sentiment={item.sentiment} />
                        <span className="text-slate-400 text-xs font-mono">
                            {(item.confidence * 100).toFixed(1)}% confiança
                        </span>
                    </div>
                    <button
                        onClick={onClose}
                        className="text-slate-500 hover:text-white transition-colors p-1"
                    >
                        <X size={20} />
                    </button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-4 overflow-y-auto max-h-[60vh]">
                    {/* Text */}
                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <h4 className="text-xs text-slate-500 uppercase font-bold">Texto Analisado</h4>
                            <button
                                onClick={handleCopy}
                                className="flex items-center gap-1 text-xs text-slate-500 hover:text-amber-500 transition-colors"
                            >
                                {copied ? (
                                    <>
                                        <Check size={12} className="text-emerald-500" />
                                        <span className="text-emerald-500">Copiado!</span>
                                    </>
                                ) : (
                                    <>
                                        <Copy size={12} />
                                        Copiar
                                    </>
                                )}
                            </button>
                        </div>
                        <p className="text-slate-200 bg-slate-950 border border-slate-800 rounded-lg p-4 font-mono text-sm leading-relaxed">
                            {item.text}
                        </p>
                    </div>

                    {/* Metadata */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t border-slate-800">
                        <div>
                            <span className="text-[10px] text-slate-600 uppercase block">ID</span>
                            <span className="text-xs text-slate-400 font-mono">{item.id.slice(0, 12)}...</span>
                        </div>
                        <div>
                            <span className="text-[10px] text-slate-600 uppercase block">Idioma</span>
                            <span className="text-xs text-slate-300 font-mono uppercase">{item.language}</span>
                        </div>
                        <div>
                            <span className="text-[10px] text-slate-600 uppercase block">Data</span>
                            <span className="text-xs text-slate-400 font-mono">
                                {new Date(item.created_at).toLocaleDateString()}
                            </span>
                        </div>
                        <div>
                            <span className="text-[10px] text-slate-600 uppercase block">Hora</span>
                            <span className="text-xs text-slate-400 font-mono">
                                {new Date(item.created_at).toLocaleTimeString()}
                            </span>
                        </div>
                    </div>

                    {/* Scores */}
                    {item.all_scores && item.all_scores.length > 0 && (
                        <div className="pt-4 border-t border-slate-800">
                            <h4 className="text-xs text-slate-500 uppercase font-bold mb-3">Scores Detalhados</h4>
                            <div className="flex gap-3">
                                {item.all_scores.map((score) => (
                                    <div
                                        key={score.label}
                                        className="flex-1 bg-slate-950 border border-slate-800 rounded-lg p-3 text-center"
                                    >
                                        <span className="text-[10px] text-slate-500 uppercase block">{score.label}</span>
                                        <span className="text-lg font-bold text-slate-200 font-mono">
                                            {(score.score * 100).toFixed(1)}%
                                        </span>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

export default TextDetailModal;
