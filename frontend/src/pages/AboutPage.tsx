/**
 * About Page - Informações sobre o projeto e autor
 */
import { Github, ExternalLink, Code2, Cpu, Globe, Database, Zap } from 'lucide-react';
import { IndustrialCard } from '../components';

export function AboutPage() {
    const features = [
        { icon: Code2, title: 'NLP Avançado', desc: 'Modelos Transformer de última geração' },
        { icon: Globe, title: 'Multilíngue', desc: 'Suporte a múltiplos idiomas' },
        { icon: Cpu, title: 'Alta Precisão', desc: 'Classificação emocional robusta' },
        { icon: Database, title: 'Cache Inteligente', desc: 'Otimização de performance' },
        { icon: Zap, title: 'Analytics', desc: 'Métricas e histórico avançados' },
    ];

    return (
        <div className="space-y-6 animate-slide-in-bottom max-w-4xl mx-auto">
            <div className="text-center space-y-4">
                <h1 className="text-4xl font-bold text-slate-100">
                    Mood<span className="text-amber-500">API</span>
                </h1>
                <p className="text-slate-400 font-mono text-sm">
                    API de Análise de Sentimentos
                </p>
            </div>

            <IndustrialCard title="Sobre o Projeto" icon={Code2}>
                <div className="space-y-4">
                    <p className="text-slate-300 leading-relaxed">
                        API para análise de sentimentos em textos utilizando técnicas de{' '}
                        <span className="text-amber-500 font-semibold">Processamento de Linguagem Natural (NLP)</span>{' '}
                        e modelos Transformer de última geração.
                    </p>
                    <p className="text-slate-400 leading-relaxed">
                        Este projeto oferece uma solução completa para classificação emocional de textos,
                        incluindo análise multilíngue de sentimentos básicos e detalhados de forma robusta
                        com alta precisão, sistema de cache inteligente, analytics avançados, extração de
                        entidades, e armazenamento de histórico.
                    </p>
                </div>
            </IndustrialCard>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
                {features.map((feature, idx) => (
                    <div key={idx} className="bg-slate-900 border border-slate-800 rounded-xl p-4 text-center hover:border-amber-500/30 transition-colors">
                        <feature.icon size={24} className="text-amber-500 mx-auto mb-2" />
                        <h3 className="text-slate-200 text-sm font-semibold">{feature.title}</h3>
                        <p className="text-slate-500 text-xs mt-1">{feature.desc}</p>
                    </div>
                ))}
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <IndustrialCard title="Tecnologias" icon={Cpu}>
                    <div className="space-y-3">
                        <div className="flex items-center gap-3">
                            <span className="bg-emerald-500/20 text-emerald-400 px-2 py-1 rounded text-xs font-mono">Backend</span>
                            <span className="text-slate-300 text-sm">Python, FastAPI, Uvicorn</span>
                        </div>
                        <div className="flex items-center gap-3">
                            <span className="bg-blue-500/20 text-blue-400 px-2 py-1 rounded text-xs font-mono">ML</span>
                            <span className="text-slate-300 text-sm">Transformers, PyTorch, Hugging Face</span>
                        </div>
                        <div className="flex items-center gap-3">
                            <span className="bg-amber-500/20 text-amber-400 px-2 py-1 rounded text-xs font-mono">Frontend</span>
                            <span className="text-slate-300 text-sm">React, TypeScript, Tailwind CSS</span>
                        </div>
                        <div className="flex items-center gap-3">
                            <span className="bg-purple-500/20 text-purple-400 px-2 py-1 rounded text-xs font-mono">Cache</span>
                            <span className="text-slate-300 text-sm">Redis (opcional)</span>
                        </div>
                        <div className="flex items-center gap-3">
                            <span className="bg-rose-500/20 text-rose-400 px-2 py-1 rounded text-xs font-mono">Database</span>
                            <span className="text-slate-300 text-sm">SQLite / PostgreSQL</span>
                        </div>
                    </div>
                </IndustrialCard>

                <IndustrialCard title="Autor" icon={Github}>
                    <div className="space-y-4">
                        <div className="flex items-center gap-4">
                            <div className="w-16 h-16 bg-gradient-to-br from-amber-500 to-amber-600 rounded-xl flex items-center justify-center text-2xl font-bold text-slate-900">
                                TF
                            </div>
                            <div>
                                <h3 className="text-xl font-bold text-slate-100">Thiago Di Faria</h3>
                                <p className="text-slate-500 text-sm font-mono">Desenvolvedor Full-Stack</p>
                            </div>
                        </div>

                        <div className="space-y-2 pt-4 border-t border-slate-800">
                            <a
                                href="https://thiagodifaria.com"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-3 text-slate-300 hover:text-amber-500 transition-colors p-2 rounded hover:bg-slate-800"
                            >
                                <Globe size={18} />
                                <span className="font-mono text-sm">thiagodifaria.com</span>
                                <ExternalLink size={14} className="ml-auto text-slate-600" />
                            </a>
                            <a
                                href="https://github.com/thiagodifaria"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-3 text-slate-300 hover:text-amber-500 transition-colors p-2 rounded hover:bg-slate-800"
                            >
                                <Github size={18} />
                                <span className="font-mono text-sm">github.com/thiagodifaria</span>
                                <ExternalLink size={14} className="ml-auto text-slate-600" />
                            </a>
                            <a
                                href="https://github.com/thiagodifaria/MoodAPI"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="flex items-center gap-3 text-slate-300 hover:text-amber-500 transition-colors p-2 rounded hover:bg-slate-800"
                            >
                                <Code2 size={18} />
                                <span className="font-mono text-sm">Repositório do Projeto</span>
                                <ExternalLink size={14} className="ml-auto text-slate-600" />
                            </a>
                        </div>
                    </div>
                </IndustrialCard>
            </div>

            <div className="text-center pt-6 border-t border-slate-800">
                <p className="text-slate-600 text-xs font-mono">
                    MoodAPI v1.0.0 &copy; 2025 Thiago Di Faria. MIT License.
                </p>
            </div>
        </div>
    );
}

export default AboutPage;
