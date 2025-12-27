/**
 * Settings Page - Configurações do sistema
 */
import { useState, useEffect } from 'react';
import { Shield, Cpu, Database, Settings, RefreshCw, Save, MessageSquare, Plus, X } from 'lucide-react';
import { IndustrialCard } from '../components';
import { api } from '../services/api';
import type { HealthResponse } from '../types';

// Default examples
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

export function SettingsPage() {
    const [health, setHealth] = useState<HealthResponse | null>(null);
    const [loading, setLoading] = useState(true);
    const [settings, setSettings] = useState({
        highPrecision: true,
        notifications: false,
        autoRefresh: true
    });
    const [examples, setExamples] = useState(DEFAULT_EXAMPLES);
    const [examplesModified, setExamplesModified] = useState(false);

    useEffect(() => {
        loadHealth();
        loadExamples();
    }, []);

    async function loadHealth() {
        try {
            const healthRes = await api.getSentimentHealth();
            setHealth(healthRes);
        } catch (err) {
            console.error('Failed to load health:', err);
        } finally {
            setLoading(false);
        }
    }

    function loadExamples() {
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
    }

    function saveExamples() {
        localStorage.setItem('moodapi_examples', JSON.stringify(examples));
        setExamplesModified(false);
    }

    function resetExamples() {
        setExamples(DEFAULT_EXAMPLES);
        localStorage.removeItem('moodapi_examples');
        setExamplesModified(false);
    }

    function updateExample(lang: 'pt' | 'en', index: number, value: string) {
        setExamples(prev => ({
            ...prev,
            [lang]: prev[lang].map((ex, i) => i === index ? value : ex)
        }));
        setExamplesModified(true);
    }

    function addExample(lang: 'pt' | 'en') {
        setExamples(prev => ({
            ...prev,
            [lang]: [...prev[lang], '']
        }));
        setExamplesModified(true);
    }

    function removeExample(lang: 'pt' | 'en', index: number) {
        if (examples[lang].length <= 1) return;
        setExamples(prev => ({
            ...prev,
            [lang]: prev[lang].filter((_, i) => i !== index)
        }));
        setExamplesModified(true);
    }

    const modelInfo = health?.model_info;

    return (
        <div className="space-y-6 animate-slide-in-bottom">
            <div>
                <h2 className="text-2xl font-bold text-slate-100">Configurações do Sistema</h2>
                <p className="text-slate-500 text-sm font-mono mt-1">
                    Gerencie parâmetros da API e recursos de infraestrutura.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                {/* API Keys */}
                <IndustrialCard title="Autenticação & API" icon={Shield}>
                    <div className="space-y-4">
                        <div>
                            <label className="text-xs text-slate-500 uppercase font-bold block mb-2">
                                Status da Autenticação
                            </label>
                            <div className="flex gap-2 items-center">
                                <div className={`w-2 h-2 rounded-full ${api.isAuthenticated() ? 'bg-emerald-500' : 'bg-amber-500'
                                    }`} />
                                <span className="text-slate-300 font-mono text-sm">
                                    {api.isAuthenticated() ? 'Autenticado' : 'Não autenticado'}
                                </span>
                            </div>
                        </div>

                        <div>
                            <label className="text-xs text-slate-500 uppercase font-bold block mb-2">
                                Endpoint da API
                            </label>
                            <code className="bg-slate-950 border border-slate-700 rounded px-3 py-2 text-emerald-400 font-mono text-sm block">
                                {import.meta.env.VITE_API_URL || '/api/v1'}
                            </code>
                        </div>

                        <div className="pt-4 border-t border-slate-800">
                            <button
                                onClick={() => window.open('http://localhost:8000/docs', '_blank')}
                                className="text-amber-500 text-xs hover:text-amber-400 font-mono uppercase flex items-center gap-2"
                            >
                                <Shield size={12} /> Ver Docs da API
                            </button>
                        </div>
                    </div>
                </IndustrialCard>

                {/* Model Configuration */}
                <IndustrialCard title="Parâmetros ML Engine" icon={Cpu}>
                    <div className="space-y-4">
                        <div>
                            <label className="text-xs text-slate-500 uppercase font-bold block mb-2">
                                Modelo Selecionado
                            </label>
                            <div className="bg-slate-950 border border-slate-700 rounded px-3 py-2 text-slate-300 text-sm font-mono">
                                {loading ? 'Carregando...' : modelInfo?.model_name || 'N/A'}
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="text-xs text-slate-500 uppercase font-bold block mb-2">
                                    Device
                                </label>
                                <div className="bg-slate-950 border border-slate-700 rounded px-3 py-2 text-slate-300 font-mono text-sm uppercase">
                                    {modelInfo?.device || 'CPU'}
                                </div>
                            </div>
                            <div>
                                <label className="text-xs text-slate-500 uppercase font-bold block mb-2">
                                    Status
                                </label>
                                <div className={`bg-slate-950 border border-slate-700 rounded px-3 py-2 font-mono text-sm ${modelInfo?.model_loaded ? 'text-emerald-400' : 'text-amber-400'
                                    }`}>
                                    {modelInfo?.model_loaded ? 'LOADED' : 'NOT LOADED'}
                                </div>
                            </div>
                        </div>
                    </div>
                </IndustrialCard>

                {/* Health Status */}
                <IndustrialCard title="Status dos Serviços" icon={Database}>
                    <div className="space-y-4">
                        <div className="space-y-2">
                            {loading ? (
                                <div className="text-slate-500 text-sm">Carregando...</div>
                            ) : health?.services ? (
                                Object.entries(health.services).map(([service, status]) => (
                                    <div key={service} className="flex justify-between items-center bg-slate-950 p-3 rounded border border-slate-800">
                                        <span className="text-slate-300 text-sm font-bold capitalize">{service}</span>
                                        <span className={`text-xs font-mono uppercase ${status === 'healthy' ? 'text-emerald-500' :
                                            status === 'degraded' ? 'text-amber-500' : 'text-rose-500'
                                            }`}>
                                            {status}
                                        </span>
                                    </div>
                                ))
                            ) : (
                                <div className="text-slate-600 text-sm">Dados não disponíveis</div>
                            )}
                        </div>

                        <div className="flex gap-3">
                            <button
                                onClick={loadHealth}
                                className="flex-1 bg-amber-600/20 hover:bg-amber-600/30 text-amber-500 border border-amber-500/50 py-2 rounded text-xs font-mono uppercase transition-colors flex items-center justify-center gap-2"
                            >
                                <RefreshCw size={12} /> Atualizar Status
                            </button>
                        </div>
                    </div>
                </IndustrialCard>

                {/* Interface Preferences */}
                <IndustrialCard
                    title="Preferências da Interface"
                    icon={Settings}
                    actions={
                        <button className="text-emerald-500 hover:text-emerald-400">
                            <Save size={16} />
                        </button>
                    }
                >
                    <div className="space-y-3">
                        <div className="flex items-center justify-between p-2 hover:bg-slate-800/30 rounded transition-colors cursor-pointer">
                            <span className="text-slate-300 text-sm">Modo de Alta Precisão</span>
                            <button
                                onClick={() => setSettings(s => ({ ...s, highPrecision: !s.highPrecision }))}
                                className={`w-10 h-5 rounded-full relative transition-colors ${settings.highPrecision ? 'bg-amber-600' : 'bg-slate-700'
                                    }`}
                            >
                                <div className={`w-3 h-3 bg-white rounded-full absolute top-1 transition-all ${settings.highPrecision ? 'right-1' : 'left-1'
                                    }`} />
                            </button>
                        </div>

                        <div className="flex items-center justify-between p-2 hover:bg-slate-800/30 rounded transition-colors cursor-pointer">
                            <span className="text-slate-300 text-sm">Notificações de Erro</span>
                            <button
                                onClick={() => setSettings(s => ({ ...s, notifications: !s.notifications }))}
                                className={`w-10 h-5 rounded-full relative transition-colors ${settings.notifications ? 'bg-amber-600' : 'bg-slate-700'
                                    }`}
                            >
                                <div className={`w-3 h-3 bg-white rounded-full absolute top-1 transition-all ${settings.notifications ? 'right-1' : 'left-1'
                                    }`} />
                            </button>
                        </div>

                        <div className="flex items-center justify-between p-2 hover:bg-slate-800/30 rounded transition-colors cursor-pointer">
                            <span className="text-slate-300 text-sm">Refresh Automático</span>
                            <button
                                onClick={() => setSettings(s => ({ ...s, autoRefresh: !s.autoRefresh }))}
                                className={`w-10 h-5 rounded-full relative transition-colors ${settings.autoRefresh ? 'bg-amber-600' : 'bg-slate-700'
                                    }`}
                            >
                                <div className={`w-3 h-3 bg-white rounded-full absolute top-1 transition-all ${settings.autoRefresh ? 'right-1' : 'left-1'
                                    }`} />
                            </button>
                        </div>
                    </div>
                </IndustrialCard>
            </div>

            {/* Analysis Examples Configuration */}
            <IndustrialCard
                title="Exemplos de Análise"
                icon={MessageSquare}
                actions={
                    <div className="flex gap-2">
                        {examplesModified && (
                            <button
                                onClick={saveExamples}
                                className="text-emerald-500 hover:text-emerald-400 flex items-center gap-1 text-xs"
                            >
                                <Save size={14} /> Salvar
                            </button>
                        )}
                        <button
                            onClick={resetExamples}
                            className="text-slate-500 hover:text-slate-300 text-xs"
                        >
                            Restaurar
                        </button>
                    </div>
                }
            >
                <p className="text-slate-500 text-xs mb-4">
                    Configure os exemplos exibidos na página de Análises.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Portuguese Examples */}
                    <div>
                        <h4 className="text-xs text-slate-400 uppercase font-bold mb-3 flex items-center gap-2">
                            <span className="bg-emerald-500/20 text-emerald-400 px-2 py-0.5 rounded">PT</span>
                            Português
                        </h4>
                        <div className="space-y-2">
                            {examples.pt.map((ex, idx) => (
                                <div key={idx} className="flex gap-2">
                                    <input
                                        type="text"
                                        value={ex}
                                        onChange={(e) => updateExample('pt', idx, e.target.value)}
                                        className="flex-1 bg-slate-950 border border-slate-700 rounded px-3 py-2 text-slate-300 text-sm focus:border-amber-500/50 outline-none"
                                        placeholder={`Exemplo ${idx + 1}...`}
                                    />
                                    {examples.pt.length > 1 && (
                                        <button
                                            onClick={() => removeExample('pt', idx)}
                                            className="text-slate-600 hover:text-rose-500 p-2"
                                        >
                                            <X size={14} />
                                        </button>
                                    )}
                                </div>
                            ))}
                            <button
                                onClick={() => addExample('pt')}
                                className="text-amber-500 hover:text-amber-400 text-xs flex items-center gap-1"
                            >
                                <Plus size={12} /> Adicionar exemplo
                            </button>
                        </div>
                    </div>

                    {/* English Examples */}
                    <div>
                        <h4 className="text-xs text-slate-400 uppercase font-bold mb-3 flex items-center gap-2">
                            <span className="bg-blue-500/20 text-blue-400 px-2 py-0.5 rounded">EN</span>
                            English
                        </h4>
                        <div className="space-y-2">
                            {examples.en.map((ex, idx) => (
                                <div key={idx} className="flex gap-2">
                                    <input
                                        type="text"
                                        value={ex}
                                        onChange={(e) => updateExample('en', idx, e.target.value)}
                                        className="flex-1 bg-slate-950 border border-slate-700 rounded px-3 py-2 text-slate-300 text-sm focus:border-amber-500/50 outline-none"
                                        placeholder={`Example ${idx + 1}...`}
                                    />
                                    {examples.en.length > 1 && (
                                        <button
                                            onClick={() => removeExample('en', idx)}
                                            className="text-slate-600 hover:text-rose-500 p-2"
                                        >
                                            <X size={14} />
                                        </button>
                                    )}
                                </div>
                            ))}
                            <button
                                onClick={() => addExample('en')}
                                className="text-amber-500 hover:text-amber-400 text-xs flex items-center gap-1"
                            >
                                <Plus size={12} /> Add example
                            </button>
                        </div>
                    </div>
                </div>
            </IndustrialCard>
        </div>
    );
}

export default SettingsPage;
