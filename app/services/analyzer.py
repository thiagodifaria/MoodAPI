import time
import re
from typing import Dict, List, Optional, Tuple, Any
import json
from datetime import datetime
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.corpus import stopwords
from textblob import TextBlob
from textblob.exceptions import TranslatorError
import googletrans

# Garantir que os recursos necessários estão disponíveis
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('tokenizers/punkt_tab')  # Adicionado para resolver o erro
    nltk.data.find('sentiment/vader_lexicon.zip')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('punkt_tab')  # Adicionado para resolver o erro
    nltk.download('vader_lexicon')
    nltk.download('stopwords')

class SentimentAnalyzer:
    """Serviço para análise de sentimentos em textos"""
    
    def __init__(self):
        """Inicializa o analisador com os modelos necessários"""
        self.vader = SentimentIntensityAnalyzer()
        self.stop_words = {lang: set(stopwords.words(lang)) 
                          for lang in stopwords.fileids() 
                          if lang in ['english', 'portuguese', 'spanish']}
        
        # Adicionar stop words que podem não estar no NLTK
        self.stop_words['portuguese'].update(['é', 'pra', 'pro', 'ser', 'ter', 'está'])
        
        # Inicializar o tradutor Google
        self.translator = googletrans.Translator()
        
    def detect_language(self, text: str) -> str:
        """Detecta o idioma do texto de forma simples
        
        Retorna: código do idioma ('en', 'pt', 'es', etc)
        """
        try:
            # Usar TextBlob para detecção de idioma
            blob = TextBlob(text)
            return blob.detect_language()
        except TranslatorError:
            # Fallback para inglês se a detecção falhar
            return 'en'
        
    def _detect_language(self, text: str) -> str:
        """Método privado para detecção de idioma - chama o método público"""
        return self.detect_language(text)
        
    def _normalize_language_code(self, lang_code: str) -> str:
        """Normaliza o código de idioma para uso interno"""
        lang_map = {
            'en': 'english',
            'pt': 'portuguese', 
            'pt-br': 'portuguese',
            'es': 'spanish'
        }
        return lang_map.get(lang_code.lower(), 'english')
    
    def _get_stop_words(self, lang_code: str) -> set:
        """Retorna stop words para o idioma especificado"""
        normalized_lang = self._normalize_language_code(lang_code)
        return self.stop_words.get(normalized_lang, self.stop_words['english'])
        
    def _preprocess_text(self, text: str) -> str:
        """Pré-processa o texto removendo caracteres especiais e normalizando"""
        # Remover URLs
        text = re.sub(r'https?://\S+|www\.\S+', '', text)
        
        # Remover tags HTML
        text = re.sub(r'<.*?>', '', text)
        
        # Remover caracteres especiais e números
        text = re.sub(r'[^\w\s]', '', text)
        text = re.sub(r'\d+', '', text)
        
        # Normalizar espaços
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def _extract_keywords(self, text: str, lang_code: str, top_n: int = 5) -> List[str]:
        """Extrai palavras-chave do texto"""
        # Normalizar idioma
        normalized_lang = self._normalize_language_code(lang_code)
        
        # Tokenizar
        tokens = word_tokenize(text.lower())
        
        # Remover stop words
        stop_words = self._get_stop_words(lang_code)
        filtered_tokens = [token for token in tokens if token.isalpha() and token not in stop_words]
        
        # Contar frequência
        freq_dist = nltk.FreqDist(filtered_tokens)
        
        # Retornar as N palavras mais frequentes
        return [word for word, _ in freq_dist.most_common(top_n)]
    
    def _extract_entities(self, text: str, lang_code: str) -> List[Dict[str, Any]]:
        """Extrai entidades do texto (simplificado)
        
        Nota: Uma implementação mais robusta usaria spaCy ou outra biblioteca específica para NER
        """
        entities = []
        # Identificar possíveis entidades com base em letras maiúsculas
        # (isso é uma simplificação, para melhor precisão use spaCy)
        possible_entities = re.findall(r'\b[A-Z][a-zA-Z]*\b', text)
        
        processed_entities = set()
        for entity in possible_entities:
            if len(entity) > 1 and entity.lower() not in self._get_stop_words(lang_code) and entity not in processed_entities:
                # Detectar sentimento associado à entidade
                sentiment = self._get_sentiment_score(f"O {entity} é", lang_code)
                
                entities.append({
                    "text": entity,
                    "type": "UNKNOWN",  # Aqui seria necessário um modelo de NER real
                    "sentiment": self._score_to_label(sentiment[0]),
                    "score": sentiment[0]
                })
                processed_entities.add(entity)
                
                if len(entities) >= 5:  # Limitar a 5 entidades
                    break
                    
        return entities
    
    def _get_sentiment_score(self, text: str, lang_code: str) -> Tuple[float, float]:
        """Calcula a pontuação de sentimento e confiança
        
        Retorna: (score, confidence)
        """
        # Para idioma inglês, usamos VADER diretamente
        if lang_code == 'en':
            scores = self.vader.polarity_scores(text)
            compound = scores['compound']
            
            # Calcular confiança (valor absoluto, normalizado)
            confidence = abs(compound) if abs(compound) > 0.05 else 0.5
            confidence = min(1.0, confidence * 1.5)  # Normalizar para 0-1
            
            return compound, confidence
        
        # Para outros idiomas, tentar traduzir usando googletrans em vez de TextBlob
        else:
            try:
                # Traduzir para inglês usando googletrans
                translated = self.translator.translate(text, src=lang_code, dest='en').text
                scores = self.vader.polarity_scores(translated)
                compound = scores['compound']
            except Exception:
                # Se tradução falhar, usar análise direta com TextBlob
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                compound = polarity  # Range diferente do VADER (-1 a 1)
            
            # Calcular confiança
            confidence = min(1.0, abs(compound) * 1.2)
            if confidence < 0.5:
                confidence = 0.5  # Mínimo de confiança
                
            return compound, confidence
    
    def _score_to_label(self, score: float) -> str:
        """Converte score de sentimento para label"""
        if score >= 0.05:
            return "positive"
        elif score <= -0.05:
            return "negative"
        else:
            return "neutral"
            
    def _analyze_emotions(self, text: str, lang_code: str) -> Dict[str, float]:
        """Analisa emoções específicas no texto
        
        Nota: Uma implementação mais robusta usaria modelos específicos para emoções
        """
        # Lista de palavras-chave para emoções básicas (simplificado)
        emotion_keywords = {
            "joy": ["feliz", "alegre", "contente", "happy", "joy", "glad", "delight", "pleasant"],
            "sadness": ["triste", "melancólico", "infeliz", "sad", "unhappy", "sorrow", "miserable"],
            "anger": ["raiva", "bravo", "irritado", "anger", "angry", "mad", "furious", "outraged"],
            "fear": ["medo", "assustado", "temeroso", "fear", "afraid", "scared", "terrified"],
            "surprise": ["surpresa", "surpreendido", "inesperado", "surprise", "surprised", "unexpected", "astonished"]
        }
        
        # Tokenizar texto
        text_lower = text.lower()
        
        # Inicializar pontuações
        emotions = {emotion: 0.0 for emotion in emotion_keywords.keys()}
        
        # Analisar ocorrências de palavras-chave
        for emotion, keywords in emotion_keywords.items():
            score = 0.0
            for keyword in keywords:
                if keyword in text_lower:
                    score += 0.2  # Incrementar pontuação por palavra encontrada
            emotions[emotion] = min(1.0, score)  # Normalizar para 0-1
        
        # Refinar usando sentimento geral
        sentiment_score, _ = self._get_sentiment_score(text, lang_code)
        
        # Ajustar emoções com base no sentimento geral
        if sentiment_score > 0.2:
            emotions["joy"] = max(emotions["joy"], sentiment_score)
            emotions["sadness"] = min(emotions["sadness"], 0.3)
        elif sentiment_score < -0.2:
            emotions["sadness"] = max(emotions["sadness"], abs(sentiment_score))
            emotions["joy"] = min(emotions["joy"], 0.3)
            
        return emotions
        
    def analyze_basic(self, text: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Realiza análise básica de sentimento
        
        Args:
            text: Texto a ser analisado
            language: Código do idioma (opcional)
            
        Returns:
            Dicionário com resultado da análise
        """
        start_time = time.time()
        
        # Detectar idioma se não especificado
        lang_code = language or self.detect_language(text)
        
        # Pré-processar texto
        processed_text = self._preprocess_text(text)
        
        # Calcular sentimento
        sentiment_score, confidence = self._get_sentiment_score(processed_text, lang_code)
        sentiment_label = self._score_to_label(sentiment_score)
        
        # Calcular tempo de processamento
        processing_time = int((time.time() - start_time) * 1000)  # ms
        
        # Construir resultado
        result = {
            "id": f"analysis_{int(datetime.utcnow().timestamp())}",
            "timestamp": datetime.utcnow().isoformat(),
            "text": text,
            "language": lang_code,
            "sentiment": {
                "label": sentiment_label,
                "score": round(sentiment_score, 2),
                "confidence": round(confidence, 2)
            },
            "processing_time_ms": processing_time
        }
        
        return result
        
    def analyze_detailed(self, text: str, language: Optional[str] = None) -> Dict[str, Any]:
        """Realiza análise detalhada de sentimento
        
        Args:
            text: Texto a ser analisado
            language: Código do idioma (opcional)
            
        Returns:
            Dicionário com resultado detalhado da análise
        """
        start_time = time.time()
        
        # Obter análise básica primeiro
        basic_result = self.analyze_basic(text, language)
        lang_code = basic_result["language"]
        
        # Processar texto
        processed_text = self._preprocess_text(text)
        
        # Extrair emoções
        emotions = self._analyze_emotions(processed_text, lang_code)
        
        # Extrair entidades
        entities = self._extract_entities(text, lang_code)
        
        # Extrair palavras-chave
        keywords = self._extract_keywords(processed_text, lang_code)
        
        # Calcular tempo de processamento
        processing_time = int((time.time() - start_time) * 1000)  # ms
        
        # Construir resultado detalhado
        result = basic_result.copy()
        result.update({
            "emotions": {k: round(v, 2) for k, v in emotions.items()},
            "entities": entities,
            "keywords": keywords,
            "processing_time_ms": processing_time
        })
        
        return result
        
    def analyze_batch(self, texts: List[str], language: Optional[str] = None, 
                     analysis_type: str = "basic") -> List[Dict[str, Any]]:
        """Realiza análise em lote de múltiplos textos
        
        Args:
            texts: Lista de textos a serem analisados
            language: Código do idioma (opcional)
            analysis_type: Tipo de análise ("basic" ou "detailed")
            
        Returns:
            Lista de resultados da análise
        """
        results = []
        
        for text in texts:
            if analysis_type == "detailed":
                result = self.analyze_detailed(text, language)
            else:
                result = self.analyze_basic(text, language)
            results.append(result)
            
        return results
        
    def check_models_loaded(self) -> bool:
        """Verifica se todos os modelos necessários foram carregados corretamente
        
        Returns:
            bool: True se todos os modelos estão carregados, False caso contrário
        """
        try:
            # Verificar se VADER está disponível
            if not hasattr(self, 'vader') or self.vader is None:
                return False
                
            # Verificar se os recursos NLTK estão disponíveis
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('tokenizers/punkt_tab')  # Adicionado para resolver o erro
            nltk.data.find('sentiment/vader_lexicon.zip')
            nltk.data.find('corpora/stopwords')
            
            # Verificar se o tradutor está disponível
            if not hasattr(self, 'translator') or self.translator is None:
                return False
                
            # Fazer um teste simples com o VADER
            test_scores = self.vader.polarity_scores("This is a test.")
            if 'compound' not in test_scores:
                return False
                
            return True
        except Exception:
            return False