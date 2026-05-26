import React, { useState } from 'react';
import { Send, Clock } from 'lucide-react';
import { PageLayout } from '../components';
import api from '../services/api';
import type { ApiPanelResponse } from '../types';

const HealthPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<ApiPanelResponse | null>(null);
  const [latency, setLatency] = useState(0);

  const handleExecute = async () => {
    setLoading(true);
    const start = performance.now();
    try {
      const data = await api.getHealth();
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
      title="Health Check"
      method="GET"
      path="/health"
      response={response}
      loading={loading}
      latency={latency}
    >
      <div className="text-sm text-slate-500 bg-slate-50 p-4 rounded-lg border border-slate-100">
        Verifica a saúde da API e suas conexões (PostgreSQL, Redis, RabbitMQ, Qdrant).
      </div>

      <div className="pt-4 border-t border-slate-100">
        <button 
          onClick={handleExecute}
          disabled={loading}
          className="flex items-center gap-2 bg-teal-600 hover:bg-teal-700 text-white px-5 py-2.5 rounded-lg text-sm font-medium transition-colors disabled:opacity-70 disabled:cursor-not-allowed w-full justify-center"
        >
          {loading ? <Clock className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          {loading ? 'Processando...' : 'Enviar Request'}
        </button>
      </div>
    </PageLayout>
  );
};

export default HealthPage;
