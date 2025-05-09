# API de Análise de Sentimentos

API para análise de sentimentos em textos utilizando técnicas de Processamento de Linguagem Natural (NLP). Este projeto oferece uma solução completa para classificação emocional de textos, incluindo análise de sentimentos básica e detalhada, extração de entidades, e armazenamento de histórico.

## 🎯 Funcionalidades

- ✅ **Análise básica de sentimento**: Classificação positivo/negativo/neutro com pontuação de confiança
- ✅ **Análise detalhada de emoções**: Detecção de alegria, tristeza, medo, surpresa, raiva
- ✅ **Extração de entidades e palavras-chave**: Identificação de elementos importantes no texto
- ✅ **Histórico de análises**: Armazenamento e consulta de análises anteriores
- ✅ **Processamento em lote**: Análise de múltiplos textos em uma única requisição
- ✅ **Suporte a múltiplos idiomas**: Detecção automática ou especificação de idioma

## 🔧 Tecnologias

- **Python 3.10+**: Linguagem de programação principal
- **FastAPI**: Framework moderno para criação de APIs
- **SQLAlchemy**: ORM para interação com o banco de dados
- **NLTK/TextBlob**: Bibliotecas para processamento de linguagem natural
- **SQLite**: Banco de dados para armazenamento
- **Pydantic**: Validação de dados e configurações
- **Uvicorn**: Servidor ASGI para execução da API

## 📋 Pré-requisitos

- Python 3.10 ou superior
- Poetry (recomendado) ou pip

## 🚀 Instalação

### Com Poetry (recomendado)

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/sentiment-api.git
cd sentiment-api

# Instalar dependências
poetry install

# Ativar ambiente virtual
poetry shell

# Baixar recursos do NLTK
python -c "import nltk; nltk.download('punkt'); nltk.download('vader_lexicon'); nltk.download('stopwords')"
```

### Com Pip

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/sentiment-api.git
cd sentiment-api

# Criar ambiente virtual
python -m venv venv

# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Instalar dependências
pip install -r requirements.txt

# Baixar recursos do NLTK
python -c "import nltk; nltk.download('punkt'); nltk.download('vader_lexicon'); nltk.download('stopwords')"
```

## ⚙️ Configuração

1. Copie o arquivo `.env.example` para `.env`:
   ```bash
   cp .env.example .env
   ```

2. Ajuste as configurações no arquivo `.env` conforme necessário:
   ```
   # Ambiente (development, testing, production)
   ENVIRONMENT=development
   
   # Configuração de banco de dados
   DATABASE_URL=sqlite:///./sentiment_analysis.db
   
   # Configurações da API
   API_TITLE="Sentiment Analysis API"
   API_VERSION="0.1.0"
   API_DESCRIPTION="API para análise de sentimentos em textos"
   
   # Configurações de log
   LOG_LEVEL=INFO
   ```

## 🖥️ Executando a API

```bash
# Método 1: Usando o Uvicorn diretamente
uvicorn app.main:app --reload

# Método 2: Usando o script Python
python -m app.main
```

Acesse a documentação interativa da API em:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 📊 Uso da API

### Exemplo de análise básica de sentimento

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/basic" \
     -H "Content-Type: application/json" \
     -d '{"text": "Estou muito feliz com o resultado deste projeto!", "language": "pt"}'
```

Resposta:
```json
{
  "id": "analysis_123456",
  "timestamp": "2025-05-07T14:30:00Z",
  "text": "Estou muito feliz com o resultado deste projeto!",
  "language": "pt",
  "sentiment": {
    "label": "positive",
    "score": 0.87,
    "confidence": 0.92
  },
  "processing_time_ms": 78
}
```

### Exemplo de análise detalhada

```bash
curl -X POST "http://localhost:8000/api/v1/analyze/detailed" \
     -H "Content-Type: application/json" \
     -d '{"text": "Estou muito feliz com o resultado deste projeto!", "language": "pt"}'
```

### Consulta do histórico

```bash
curl -X GET "http://localhost:8000/api/v1/history?limit=10&page=1"
```

## 🧪 Testes

```bash
# Executar todos os testes
pytest

# Executar testes com cobertura
pytest --cov=app tests/

# Executar testes específicos
pytest tests/test_analyzer.py
```

## 📝 Documentação

A documentação completa da API está disponível em:

- `/docs`: Documentação interativa com Swagger UI
- `/redoc`: Documentação alternativa com ReDoc

## 🔄 Fluxo de Desenvolvimento

1. Clone o repositório
2. Crie uma branch para sua feature (`git checkout -b feature/nome-da-feature`)
3. Implemente suas alterações
4. Execute os testes (`pytest`)
5. Formate o código (`black .` e `isort .`)
6. Faça commit das alterações (`git commit -m 'feat: adiciona nova funcionalidade'`)
7. Envie para a branch (`git push origin feature/nome-da-feature`)
8. Abra um Pull Request

## 🚢 Deployment

### Com Docker

```bash
# Construir a imagem
docker build -t sentiment-api .

# Executar o container
docker run -d -p 8000:8000 sentiment-api
```

### Manual

Para ambiente de produção, recomenda-se:

1. Usar Gunicorn como gerenciador de processos
2. Configurar um proxy reverso (Nginx/Apache)
3. Usar um banco de dados mais robusto (PostgreSQL/MySQL)

## 🛣️ Roadmap

- [ ] Suporte a mais idiomas
- [ ] Modelos de ML personalizados
- [ ] Interface web de administração
- [ ] Sistema de autenticação e autorização
- [ ] Cache de resultados para textos similares
- [ ] Exportação de relatórios em diversos formatos

## 📜 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 📞 Contato

Thiago Di Faria - [thiagodifaria@gmail.com](mailto:thiagodifaria@gmail.com)

Link do projeto: [https://github.com/thiagodifaria/MoodAPI](https://github.com/thiagodifaria/MoodAPI)