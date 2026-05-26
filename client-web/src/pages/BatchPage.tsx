import React, { useState } from 'react';
import { Send, Clock } from 'lucide-react';
import { PageLayout } from '../components';
import api from '../services/api';
import type { ApiPanelResponse } from '../types';

const BatchPage: React.FC = () => {
  const [texts, setTexts] = useState('Produto excelente.\nA entrega atrasou e o suporte foi ruim.\nA experiencia foi normal.');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<ApiPanelResponse | null>(null);
  const [latency, setLatency] = useState(0);

  const handleExecute = async () => {
    setLoading(true);
    const start = performance.now();
    const textsArray = texts.split('\n').filter(t => t.trim() !== '');
    try {
      const data = await api.analyzeBatch(textsArray);
      setLatency(Math.round(performance.now() - start));
      setResponse({ status: 200, data });
    } catch (err: unknown) {
      const error = err as { response?: { status?: number; data?: unknown }; message?: string };
      setLatency(Math.round(performance.now() - start));
      setResponse({ 
        status: error.response?.status || 500, 
        data: error.response?.data || { detail: error.message || 'Erro inesperado' } 
      });
    } finally {
      setLoading(false);
    }
  };

  return (
    <PageLayout
      title="Análise em Lote"
      method="POST"
      path="/api/v1/sentiment/analyze-batch"
      response={response}
      loading={loading}
      latency={latency}
    >
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">Textos (um por linha)</label>
        <textarea 
          className="w-full border border-slate-300 rounded-lg p-3 text-sm focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none resize-y whitespace-pre"
          rows={6}
          value={texts}
          onChange={(e) => setTexts(e.target.value)}
        />
      </div>

      <div className="pt-4 border-t border-slate-100">
        <button 
          onClick={handleExecute}
          disabled={loading || !texts.trim()}
          className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-70 disabled:cursor-not-allowed w-full justify-center"
        >
          {loading ? <Clock className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          {loading ? 'Processando...' : 'Enviar Request'}
        </button>
      </div>
    </PageLayout>
  );
};

export default BatchPage;
