import React, { useState } from 'react';
import { Send, Clock } from 'lucide-react';
import { PageLayout } from '../components';
import api from '../services/api';
import type { ApiPanelResponse } from '../types';

const AnalyzePage: React.FC = () => {
  const [text, setText] = useState('Eu gostei muito da experiencia, o atendimento foi excelente.');
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<ApiPanelResponse | null>(null);
  const [latency, setLatency] = useState(0);

  const handleExecute = async () => {
    setLoading(true);
    const start = performance.now();
    try {
      const data = await api.analyze(text);
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
      title="Análise Unitária"
      method="POST"
      path="/api/v1/sentiment/analyze"
      response={response}
      loading={loading}
      latency={latency}
    >
      <div>
        <label className="block text-sm font-medium text-slate-700 mb-2">Texto para inferência</label>
        <textarea 
          className="w-full border border-slate-300 rounded-lg p-3 text-sm focus:ring-2 focus:ring-teal-500 focus:border-teal-500 outline-none resize-y"
          rows={4}
          value={text}
          onChange={(e) => setText(e.target.value)}
        />
      </div>

      <div className="pt-4 border-t border-slate-100">
        <button 
          onClick={handleExecute}
          disabled={loading || !text.trim()}
          className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-70 disabled:cursor-not-allowed w-full justify-center"
        >
          {loading ? <Clock className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          {loading ? 'Processando...' : 'Enviar Request'}
        </button>
      </div>
    </PageLayout>
  );
};

export default AnalyzePage;
