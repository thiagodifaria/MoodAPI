"""
Utility functions for NLP tasks in the sentiment analysis API.
This module provides helper functions for text processing, language detection,
tokenization, stemming, lemmatization, and other NLP-related tasks.
"""
import re
from typing import List, Dict, Any, Tuple, Optional
import unicodedata

# For multilingual support we'll use these libraries
# You'll need to install them via pip
import nltk
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import PorterStemmer, WordNetLemmatizer
from nltk.corpus import stopwords
import spacy
import fasttext
import langdetect
from textblob import TextBlob

# Download necessary NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

try:
    nltk.data.find('corpora/wordnet')
except LookupError:
    nltk.download('wordnet')

# Initialize language detection model
# Note: This path should be updated based on your project setup
# and you'll need to download the model from https://fasttext.cc/docs/en/language-identification.html
LANGUAGE_MODEL_PATH = "models/lid.176.bin"
language_model = None

# Initialize spaCy models
# We'll load these on-demand to save memory
nlp_models = {}

def initialize_language_model(model_path: Optional[str] = None) -> None:
    """
    Initialize the language detection model.
    
    Args:
        model_path: Path to the FastText language model
    """
    global language_model
    
    path = model_path or LANGUAGE_MODEL_PATH
    try:
        language_model = fasttext.load_model(path)
    except Exception as e:
        print(f"Warning: Could not load language model from {path}: {e}")
        print("Falling back to langdetect library for language detection")

def get_spacy_model(lang_code: str) -> Any:
    """
    Get or load a spaCy model for the specified language.
    
    Args:
        lang_code: Two-letter language code (e.g., 'en', 'es', 'pt')
        
    Returns:
        Loaded spaCy model
    """
    # Map of language codes to spaCy model names
    lang_map = {
        'en': 'en_core_web_sm',
        'es': 'es_core_news_sm',
        'de': 'de_core_news_sm',
        'fr': 'fr_core_news_sm',
        'pt': 'pt_core_news_sm',
        'it': 'it_core_news_sm',
        # Add more languages as needed
    }
    
    # Default to English if language not supported
    model_name = lang_map.get(lang_code, 'en_core_web_sm')
    
    # Load model if not already loaded
    if model_name not in nlp_models:
        try:
            nlp_models[model_name] = spacy.load(model_name)
        except OSError:
            # If model not installed, provide instructions and fall back to English
            print(f"Model {model_name} not found. Install it with: python -m spacy download {model_name}")
            if model_name != 'en_core_web_sm':
                print("Falling back to English model")
                try:
                    nlp_models[model_name] = spacy.load('en_core_web_sm')
                except OSError:
                    print("English model not found. Install it with: python -m spacy download en_core_web_sm")
                    raise
                    
    return nlp_models[model_name]

def detect_language(text: str) -> str:
    """
    Detect the language of the given text.
    
    Args:
        text: Text to analyze
        
    Returns:
        Two-letter language code (e.g., 'en', 'es', 'pt')
    """
    if not text or len(text.strip()) == 0:
        return 'en'  # Default to English for empty text
    
    # Clean text to improve detection
    text = text.strip()
    
    # Try using FastText if available (more accurate)
    if language_model:
        try:
            predictions = language_model.predict(text.replace('\n', ' '))
            # FastText returns labels like '__label__en'
            lang_code = predictions[0][0].replace('__label__', '')
            return lang_code
        except Exception:
            pass
    
    # Fall back to langdetect
    try:
        return langdetect.detect(text)
    except langdetect.LangDetectException:
        # Fall back to TextBlob as a last resort
        try:
            return TextBlob(text).detect_language()
        except:
            return 'en'  # Default to English if detection fails

def preprocess_text(text: str) -> str:
    """
    Clean and normalize text for analysis.
    
    Args:
        text: Raw text input
        
    Returns:
        Preprocessed text
    """
    if not text:
        return ""
        
    # Convert to lowercase
    text = text.lower()
    
    # Normalize unicode characters
    text = unicodedata.normalize('NFKD', text)
    
    # Remove URLs
    text = re.sub(r'https?://\S+|www\.\S+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove numbers
    text = re.sub(r'\d+', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def tokenize_text(text: str, lang: str = 'en') -> List[str]:
    """
    Tokenize text into words.
    
    Args:
        text: Text to tokenize
        lang: Language code
        
    Returns:
        List of tokens (words)
    """
    if not text:
        return []
        
    # Try using spaCy for better tokenization
    try:
        nlp = get_spacy_model(lang)
        doc = nlp(text)
        return [token.text for token in doc]
    except:
        # Fall back to NLTK
        return word_tokenize(text)

def sentence_tokenize(text: str, lang: str = 'en') -> List[str]:
    """
    Split text into sentences.
    
    Args:
        text: Text to split
        lang: Language code
        
    Returns:
        List of sentences
    """
    if not text:
        return []
        
    # Try using spaCy for better sentence segmentation
    try:
        nlp = get_spacy_model(lang)
        doc = nlp(text)
        return [sent.text for sent in doc.sents]
    except:
        # Fall back to NLTK
        return sent_tokenize(text)

def remove_stopwords(tokens: List[str], lang: str = 'en') -> List[str]:
    """
    Remove stopwords from a list of tokens.
    
    Args:
        tokens: List of tokens (words)
        lang: Language code
        
    Returns:
        List of tokens with stopwords removed
    """
    if not tokens:
        return []
        
    try:
        # Try to get stopwords for the specified language
        stops = set(stopwords.words(lang))
    except:
        # Fall back to English stopwords
        stops = set(stopwords.words('english'))
        
    return [token for token in tokens if token.lower() not in stops]

def stem_tokens(tokens: List[str]) -> List[str]:
    """
    Apply stemming to tokens (English only).
    
    Args:
        tokens: List of tokens
        
    Returns:
        List of stemmed tokens
    """
    if not tokens:
        return []
        
    stemmer = PorterStemmer()
    return [stemmer.stem(token) for token in tokens]

def lemmatize_tokens(tokens: List[str], lang: str = 'en') -> List[str]:
    """
    Apply lemmatization to tokens.
    
    Args:
        tokens: List of tokens
        lang: Language code
        
    Returns:
        List of lemmatized tokens
    """
    if not tokens:
        return []
        
    # Try using spaCy for better lemmatization with language support
    try:
        nlp = get_spacy_model(lang)
        doc = nlp(" ".join(tokens))
        return [token.lemma_ for token in doc]
    except:
        # Fall back to NLTK WordNet lemmatizer (English only)
        lemmatizer = WordNetLemmatizer()
        return [lemmatizer.lemmatize(token) for token in tokens]

def extract_entities(text: str, lang: str = 'en') -> List[Dict[str, Any]]:
    """
    Extract named entities from text.
    
    Args:
        text: Text to analyze
        lang: Language code
        
    Returns:
        List of entities with type and text
    """
    if not text:
        return []
        
    try:
        nlp = get_spacy_model(lang)
        doc = nlp(text)
        
        entities = []
        for ent in doc.ents:
            entities.append({
                'text': ent.text,
                'type': ent.label_,
                'start': ent.start_char,
                'end': ent.end_char
            })
        
        return entities
    except Exception as e:
        print(f"Entity extraction error: {e}")
        return []

def extract_keywords(text: str, lang: str = 'en', top_n: int = 10) -> List[str]:
    """
    Extract important keywords from text.
    
    Args:
        text: Text to analyze
        lang: Language code
        top_n: Number of keywords to return
        
    Returns:
        List of keywords
    """
    if not text:
        return []
        
    try:
        # Use spaCy for keyword extraction
        nlp = get_spacy_model(lang)
        doc = nlp(text)
        
        # Filter for meaningful parts of speech and remove stopwords
        keywords = [token.text for token in doc if not token.is_stop and 
                    not token.is_punct and token.pos_ in ('NOUN', 'ADJ', 'VERB')]
        
        # Get frequency distribution and return top N
        from collections import Counter
        counter = Counter(keywords)
        return [word for word, _ in counter.most_common(top_n)]
    except:
        # Simple fallback if spaCy fails
        words = tokenize_text(text, lang)
        words = remove_stopwords(words, lang)
        from collections import Counter
        counter = Counter(words)
        return [word for word, _ in counter.most_common(top_n)]

def calculate_sentiment_score(text: str, lang: str = 'en') -> Dict[str, Any]:
    """
    Calculate sentiment score using TextBlob.
    
    Args:
        text: Text to analyze
        lang: Language code
        
    Returns:
        Dictionary with polarity and subjectivity scores
    """
    if not text:
        return {'polarity': 0.0, 'subjectivity': 0.0}
    
    # TextBlob works best with English, but can handle other languages to some extent
    try:
        blob = TextBlob(text)
        sentiment = blob.sentiment
        
        return {
            'polarity': sentiment.polarity,  # Range: -1.0 to 1.0
            'subjectivity': sentiment.subjectivity  # Range: 0.0 to 1.0
        }
    except Exception as e:
        print(f"Sentiment analysis error: {e}")
        return {'polarity': 0.0, 'subjectivity': 0.0}

def categorize_sentiment(polarity: float) -> str:
    """
    Convert numerical polarity to sentiment category.
    
    Args:
        polarity: Sentiment polarity score (-1.0 to 1.0)
        
    Returns:
        Sentiment category: 'positive', 'negative', or 'neutral'
    """
    if polarity > 0.1:
        return 'positive'
    elif polarity < -0.1:
        return 'negative'
    else:
        return 'neutral'

def detect_emotion(text: str, lang: str = 'en') -> Dict[str, float]:
    """
    Detect emotions in text.
    This is a simplified implementation. For production use,
    consider using dedicated sentiment/emotion analysis libraries or models.
    
    Args:
        text: Text to analyze
        lang: Language code
        
    Returns:
        Dictionary mapping emotions to their scores
    """
    # Basic emotion lexicon (English-centric)
    # In a real implementation, you'd use a more sophisticated approach
    emotion_lexicon = {
        'joy': ['happy', 'happiness', 'joy', 'delighted', 'pleased', 'glad', 'cheerful', 'excited'],
        'sadness': ['sad', 'unhappy', 'depressed', 'miserable', 'gloomy', 'heartbroken', 'disappointed'],
        'anger': ['angry', 'mad', 'furious', 'outraged', 'annoyed', 'irritated', 'enraged'],
        'fear': ['afraid', 'scared', 'frightened', 'terrified', 'anxious', 'worried', 'nervous'],
        'surprise': ['surprised', 'shocked', 'amazed', 'astonished', 'startled', 'unexpected'],
        'disgust': ['disgusted', 'revolted', 'repulsed', 'sickened', 'offended', 'appalled']
    }
    
    # Initialize scores
    emotion_scores = {emotion: 0.0 for emotion in emotion_lexicon}
    
    # Preprocess and tokenize
    tokens = tokenize_text(preprocess_text(text), lang)
    tokens = [token.lower() for token in tokens]
    
    # Count emotion words
    total_emotion_words = 0
    for emotion, words in emotion_lexicon.items():
        count = sum(1 for token in tokens if token in words)
        emotion_scores[emotion] = count
        total_emotion_words += count
    
    # Normalize scores
    if total_emotion_words > 0:
        for emotion in emotion_scores:
            emotion_scores[emotion] /= total_emotion_words
    
    # If no emotions are detected, set a default
    if total_emotion_words == 0:
        # Set neutral as default
        emotion_scores['neutral'] = 1.0
    
    return emotion_scores

def calculate_text_stats(text: str) -> Dict[str, Any]:
    """
    Calculate basic text statistics.
    
    Args:
        text: Text to analyze
        
    Returns:
        Dictionary with text statistics
    """
    if not text:
        return {
            'char_count': 0,
            'word_count': 0,
            'sentence_count': 0,
            'avg_word_length': 0,
            'avg_sentence_length': 0
        }
    
    # Count characters (excluding whitespace)
    char_count = len(text.replace(" ", ""))
    
    # Tokenize into words and sentences
    words = tokenize_text(text)
    sentences = sentence_tokenize(text)
    
    # Count words and sentences
    word_count = len(words)
    sentence_count = len(sentences)
    
    # Calculate averages
    avg_word_length = char_count / word_count if word_count > 0 else 0
    avg_sentence_length = word_count / sentence_count if sentence_count > 0 else 0
    
    return {
        'char_count': char_count,
        'word_count': word_count,
        'sentence_count': sentence_count,
        'avg_word_length': avg_word_length,
        'avg_sentence_length': avg_sentence_length
    }

def summarize_text(text: str, lang: str = 'en', sentences: int = 3) -> str:
    """
    Generate a simple extractive summary of the text.
    
    Args:
        text: Text to summarize
        lang: Language code
        sentences: Number of sentences to include in summary
        
    Returns:
        Summary text
    """
    if not text:
        return ""
    
    try:
        # Split into sentences
        all_sentences = sentence_tokenize(text, lang)
        
        if len(all_sentences) <= sentences:
            return text
            
        # For a simple approach, we'll use the first sentence and then select others based on length
        # A more sophisticated approach would use TF-IDF or other metrics
        
        # Always include the first sentence
        selected_sentences = [all_sentences[0]]
        
        # Score other sentences (here we just use length as a simple heuristic)
        other_sentences = [(i, len(s.split())) for i, s in enumerate(all_sentences[1:])]
        
        # Sort by length (longer sentences often contain more information)
        other_sentences.sort(key=lambda x: x[1], reverse=True)
        
        # Select top sentences
        for i, _ in other_sentences[:sentences-1]:
            selected_sentences.append(all_sentences[i+1])  # +1 because we skipped the first sentence
        
        # Sort by original position
        selected_sentences.sort(key=lambda x: all_sentences.index(x))
        
        # Join into a summary
        return " ".join(selected_sentences)
        
    except Exception as e:
        print(f"Text summarization error: {e}")
        return text[:500] + "..." if len(text) > 500 else text  # Fallback to simple truncation