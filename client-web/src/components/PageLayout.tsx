import React from 'react';
import { Code, Clock, CheckCircle2, Activity } from 'lucide-react';
import type { ApiPanelResponse, Sentiment } from '../types';

interface SentimentPayload {
  sentiment: Sentiment;
  confidence: number;
}

interface PageLayoutProps {
  title: string;
  method: string;
  path: string;
  children: React.ReactNode; // Request Builder
  response: ApiPanelResponse | null;
  loading: boolean;
  latency: number;
}

function isSentimentPayload(data: unknown): data is SentimentPayload {
  if (!data || typeof data !== 'object') {
    return false;
  }

  const payload = data as Partial<SentimentPayload>;
  return typeof payload.sentiment === 'string' && typeof payload.confidence === 'number';
}

const PageLayout: React.FC<PageLayoutProps> = ({
  title,
  method,
  path,
  children,
  response,
  loading,
  latency
}) => {
  const sentimentData = response && isSentimentPayload(response.data) ? response.data : null;

  return (
    <div className="flex-1 flex flex-col h-screen overflow-hidden">
      {/* Header do Content */}
      <header className="bg-white border-b border-slate-200 px-8 py-5 flex items-center justify-between shrink-0">
        <div>
          <h1 className="text-xl font-semibold text-slate-800">{title}</h1>
          <div className="flex items-center gap-2 mt-1">
            <span className={`px-2 py-0.5 rounded text-xs font-bold font-mono ${
              method === 'GET' ? 'bg-blue-100 text-blue-700' : 'bg-green-100 text-green-700'
            }`}>
              {method}
            </span>
            <span className="font-mono text-sm text-slate-500">{path}</span>
          </div>
        </div>
      </header>

      {/* Área de Request / Response */}
      <div className="flex-1 p-8 overflow-y-auto grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">
        
        {/* Lado Esquerdo: Request Builder */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 bg-slate-50/50">
            <h2 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <Code className="w-4 h-4 text-slate-400" /> Requisição
            </h2>
          </div>
          
          <div className="p-6 space-y-4">
            {children}
          </div>
        </div>

        {/* Lado Direito: Response */}
        <div className="bg-slate-900 rounded-xl shadow-sm overflow-hidden flex flex-col h-full min-h-[400px]">
          <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between bg-slate-900">
            <h2 className="text-sm font-semibold text-slate-300 flex items-center gap-2">
              Resposta da API
            </h2>
            {response && (
              <div className="flex items-center gap-3">
                <span className="text-xs text-slate-400 font-mono flex items-center gap-1">
                  <Clock className="w-3 h-3" /> {latency}ms
                </span>
                <span className={`px-2 py-0.5 rounded text-xs font-bold font-mono flex items-center gap-1 ${
                  response.status >= 200 && response.status < 300 ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'
                }`}>
                  {response.status >= 200 && response.status < 300 ? <CheckCircle2 className="w-3 h-3" /> : null}
                  {response.status}
                </span>
              </div>
            )}
          </div>

          <div className="p-6 flex-1 overflow-auto">
            {!response && !loading && (
              <div className="h-full flex items-center justify-center text-slate-600 text-sm italic">
                Aguardando envio da requisição...
              </div>
            )}
            
            {loading && (
              <div className="h-full flex flex-col items-center justify-center text-teal-500 gap-3">
                <Activity className="w-8 h-8 animate-pulse" />
                <span className="text-sm text-slate-400">Aguardando API Gateway...</span>
              </div>
            )}

            {response && !loading && (
              <div className="space-y-6">
                {/* Specific formatting for Analyze result if it exists */}
                {sentimentData && (
                   <div className={`p-4 rounded-lg border flex items-center justify-between ${
                    sentimentData.sentiment === 'positive' ? 'text-green-700 bg-green-50 border-green-200' :
                    sentimentData.sentiment === 'negative' ? 'text-red-700 bg-red-50 border-red-200' :
                    'text-slate-700 bg-slate-50 border-slate-200'
                   }`}>
                     <div>
                       <div className="text-xs font-bold uppercase tracking-wider opacity-70 mb-1">Sentimento Detectado</div>
                       <div className="text-lg font-semibold capitalize">{sentimentData.sentiment}</div>
                     </div>
                     <div className="text-right">
                       <div className="text-xs font-bold uppercase tracking-wider opacity-70 mb-1">Confiança</div>
                       <div className="text-lg font-mono">{(sentimentData.confidence * 100).toFixed(1)}%</div>
                     </div>
                   </div>
                )}

                {/* Raw JSON */}
                <div>
                  <div className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">Raw JSON Payload</div>
                  <pre className="text-sm font-mono text-slate-300 bg-slate-950 p-4 rounded-lg overflow-x-auto border border-slate-800">
                    {JSON.stringify(response.data, null, 2)}
                  </pre>
                </div>
              </div>
            )}
          </div>
        </div>

      </div>
    </div>
  );
};

export default PageLayout;
