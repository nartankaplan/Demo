import google.generativeai as genai
import re
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import Counter
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize

@dataclass
class ContentAnalysisResult:
    content_completeness_score: float
    missing_topics: List[str]
    key_concepts: List[str]
    concept_density: Dict[str, float]
    topic_flow_score: float
    interaction_examples_count: int
    educational_structure_score: float
    overall_content_score: float
    topic_heatmap: List[Dict[str, any]]  # segment-wise topic analysis

class ContentAnalyzer:
    def __init__(self, api_key: str):
        """Gemini API anahtarı ile başlat"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # NLTK verilerini indir (ilk çalıştırma için)
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('punkt_tab', quiet=True)
            nltk.download('stopwords', quiet=True)
        except:
            pass
        
        # Türkçe stopwords
        try:
            self.turkish_stopwords = set(stopwords.words('turkish'))
        except:
            # Eğer Türkçe stopwords yoksa, temel olanları tanımla
            self.turkish_stopwords = {
                'bir', 'bu', 'da', 'de', 'den', 'ile', 'için', 'gibi', 'daha',
                've', 'var', 'yok', 'olan', 'olan', 'çok', 'tüm', 'her'
            }
    
    def analyze_content(self, transcription: str, subject_topic: str = None) -> ContentAnalysisResult:
        """Ana içerik analiz fonksiyonu"""
        
        try:
            # İçerik bütünlüğü analizi
            completeness_score, missing_topics = self._analyze_content_completeness(
                transcription, subject_topic
            )
        except Exception as e:
            print(f"İçerik bütünlüğü analizi hatası: {e}")
            completeness_score, missing_topics = 75.0, []
        
        # Anahtar kavram analizi
        key_concepts, concept_density = self._extract_key_concepts(transcription)
        
        # Konu akışı analizi
        topic_flow_score = self._analyze_topic_flow(transcription)
        
        # Etkileşim ve örneklendirme analizi
        interaction_count = self._count_interaction_examples(transcription)
        
        # Eğitimsel yapı analizi
        structure_score = self._analyze_educational_structure(transcription)
        
        # Konu yoğunluk haritası
        topic_heatmap = self._create_topic_heatmap(transcription, key_concepts)
        
        # Genel içerik skoru
        overall_score = self._calculate_overall_content_score(
            completeness_score, topic_flow_score, structure_score, 
            interaction_count, len(key_concepts)
        )
        
        return ContentAnalysisResult(
            content_completeness_score=completeness_score,
            missing_topics=missing_topics,
            key_concepts=key_concepts,
            concept_density=concept_density,
            topic_flow_score=topic_flow_score,
            interaction_examples_count=interaction_count,
            educational_structure_score=structure_score,
            overall_content_score=overall_score,
            topic_heatmap=topic_heatmap
        )
    
    def _analyze_content_completeness(self, transcription: str, subject_topic: str = None) -> Tuple[float, List[str]]:
        """İçerik bütünlüğü ve eksik konuları analiz et"""
        
        prompt = f"""
        Aşağıdaki eğitim videosu transkriptini analiz et:
        
        "{transcription}"
        
        Eğer bir konu belirtilmişse: {subject_topic if subject_topic else "Genel eğitim içeriği"}
        
        Lütfen şunları değerlendir:
        1. İçeriğin bütünlüğü (0-100 puan)
        2. Eksik olabilecek önemli konular
        3. Anlatımda atlanan kritik noktalar
        
        Cevabını şu formatta ver:
        BÜTÜNLÜK SKORU: [0-100 arası sayı]
        EKSİK KONULAR: [eksik konuları virgülle ayırarak listele]
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            # Skoru parse et
            score_match = re.search(r'BÜTÜNLÜK SKORU:\s*(\d+)', result_text)
            completeness_score = float(score_match.group(1)) if score_match else 70.0
            
            # Eksik konuları parse et
            missing_match = re.search(r'EKSİK KONULAR:\s*(.+)', result_text)
            missing_topics = []
            if missing_match:
                missing_text = missing_match.group(1).strip()
                if missing_text and missing_text.lower() not in ['yok', 'bulunmuyor', 'eksik yok']:
                    missing_topics = [topic.strip() for topic in missing_text.split(',')]
            
            return completeness_score, missing_topics
            
        except Exception as e:
            print(f"İçerik bütünlüğü analizi hatası: {e}")
            return 70.0, []  # Varsayılan değerler
    
    def _extract_key_concepts(self, transcription: str) -> Tuple[List[str], Dict[str, float]]:
        """Anahtar kavramları çıkar ve yoğunluklarını hesapla"""
        
        # Basit NLP ile anahtar kelime çıkarma
        words = word_tokenize(transcription.lower())
        
        # Stopwords ve kısa kelimeleri filtrele
        filtered_words = [
            word for word in words 
            if len(word) > 3 and word.isalpha() and word not in self.turkish_stopwords
        ]
        
        # Kelime sıklığı
        word_freq = Counter(filtered_words)
        
        # En sık kullanılan kelimeleri al (anahtar kavramlar)
        key_concepts = [word for word, freq in word_freq.most_common(10) if freq > 1]
        
        # Kavram yoğunluğu hesapla
        total_words = len(filtered_words)
        concept_density = {
            concept: (word_freq[concept] / total_words * 100) 
            for concept in key_concepts
        }
        
        return key_concepts, concept_density
    
    def _analyze_topic_flow(self, transcription: str) -> float:
        """Konu akışı ve mantıksal geçişleri analiz et"""
        
        prompt = f"""
        Bu eğitim içeriğinin konu akışını analiz et:
        
        "{transcription}"
        
        Şunları değerlendir:
        1. Konuların mantıksal sırası
        2. Geçişlerin akıcılığı
        3. Giriş-gelişme-sonuç yapısı
        4. Konular arası bağlantılar
        
        0-100 arası bir akış skoru ver:
        AKIŞ SKORU: [sayı]
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            # Skoru parse et
            score_match = re.search(r'AKIŞ SKORU:\s*(\d+)', result_text)
            flow_score = float(score_match.group(1)) if score_match else 75.0
            
            return flow_score
            
        except Exception as e:
            print(f"Konu akışı analizi hatası: {e}")
            return 75.0  # Varsayılan değer
    
    def _count_interaction_examples(self, transcription: str) -> int:
        """Etkileşim ve örneklendirme sayısını hesapla"""
        
        # Etkileşim belirten ifadeler
        interaction_patterns = [
            r'\b(örnek|örneğin|mesela|şöyle|böyle)\b',
            r'\b(soru|soruyor|düşünelim|bakalım)\b',
            r'\b(gördüğünüz|dikkat|fark ettiniz)\b',
            r'\b(yapabiliriz|deneyebiliriz|uygulayalım)\b'
        ]
        
        interaction_count = 0
        for pattern in interaction_patterns:
            matches = re.findall(pattern, transcription.lower())
            interaction_count += len(matches)
        
        return interaction_count
    
    def _analyze_educational_structure(self, transcription: str) -> float:
        """Eğitimsel yapı ve metodoloji analizi"""
        
        prompt = f"""
        Bu eğitim içeriğinin pedagojik yapısını analiz et:
        
        "{transcription}"
        
        Şunları değerlendir:
        1. Açık hedef belirleme
        2. Sistematik anlatım
        3. Tekrar ve pekiştirme
        4. Değerlendirme soruları
        5. Özet ve sonuç
        
        0-100 arası eğitimsel yapı skoru:
        YAPI SKORU: [sayı]
        """
        
        try:
            response = self.model.generate_content(prompt)
            result_text = response.text
            
            # Skoru parse et
            score_match = re.search(r'YAPI SKORU:\s*(\d+)', result_text)
            structure_score = float(score_match.group(1)) if score_match else 70.0
            
            return structure_score
            
        except Exception as e:
            print(f"Eğitimsel yapı analizi hatası: {e}")
            return 70.0  # Varsayılan değer
    
    def _create_topic_heatmap(self, transcription: str, key_concepts: List[str]) -> List[Dict[str, any]]:
        """Konu yoğunluk haritası oluştur"""
        
        # Metni segmentlere ayır (her segment ~30 saniye = ~50 kelime)
        words = transcription.split()
        segment_size = 50
        segments = [words[i:i+segment_size] for i in range(0, len(words), segment_size)]
        
        heatmap = []
        
        for i, segment in enumerate(segments):
            segment_text = ' '.join(segment).lower()
            
            # Bu segmentteki anahtar kavram yoğunluğu
            concept_scores = {}
            for concept in key_concepts:
                count = segment_text.count(concept)
                density = count / len(segment) if segment else 0
                concept_scores[concept] = density
            
            # Segment bilgisi
            segment_info = {
                'segment_id': i,
                'start_word': i * segment_size,
                'end_word': min((i + 1) * segment_size, len(words)),
                'concept_scores': concept_scores,
                'dominant_concept': max(concept_scores.items(), key=lambda x: x[1])[0] if concept_scores else None,
                'density_score': sum(concept_scores.values())
            }
            
            heatmap.append(segment_info)
        
        return heatmap
    
    def _calculate_overall_content_score(self, completeness: float, flow: float, 
                                       structure: float, interaction_count: int, 
                                       concept_count: int) -> float:
        """Genel içerik skoru hesapla"""
        
        # Etkileşim skoru (0-100 arası normalize et)
        interaction_score = min(100, interaction_count * 10)
        
        # Kavram zenginliği skoru
        concept_score = min(100, concept_count * 8)
        
        # Ağırlıklı ortalama
        overall_score = (
            completeness * 0.3 +
            flow * 0.25 +
            structure * 0.25 +
            interaction_score * 0.1 +
            concept_score * 0.1
        )
        
        return overall_score
    
    def generate_recommendations(self, analysis_result: ContentAnalysisResult, 
                               transcription: str) -> List[str]:
        """İyileştirme önerileri oluştur"""
        
        prompt = f"""
        Bu eğitim analiz sonuçlarına göre iyileştirme önerileri oluştur:
        
        İçerik Bütünlüğü: {analysis_result.content_completeness_score}/100
        Konu Akışı: {analysis_result.topic_flow_score}/100
        Eğitimsel Yapı: {analysis_result.educational_structure_score}/100
        Etkileşim Sayısı: {analysis_result.interaction_examples_count}
        Eksik Konular: {', '.join(analysis_result.missing_topics)}
        
        Orijinal içerik: "{transcription[:500]}..."
        
        Lütfen 5-7 pratik iyileştirme önerisi ver. Her öneriyi yeni satırda "- " ile başlat.
        """
        
        try:
            response = self.model.generate_content(prompt)
            recommendations_text = response.text
            
            # Önerileri liste olarak parse et
            recommendations = []
            for line in recommendations_text.split('\n'):
                if line.strip().startswith('-') or line.strip().startswith('•'):
                    recommendation = line.strip()[1:].strip()
                    if recommendation:
                        recommendations.append(recommendation)
            
            return recommendations[:7]  # Max 7 öneri
            
        except Exception as e:
            print(f"Öneri oluşturma hatası: {e}")
            return [
                "İçeriğe daha fazla örnek ve analoji ekleyin",
                "Konular arası geçişleri güçlendirin",
                "Öğrenci etkileşimi artıran sorular sorun",
                "Ana kavramları özetleyen bölümler ekleyin"
            ] 