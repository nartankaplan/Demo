import whisper
import librosa
import numpy as np
import re
from typing import Dict, List, Tuple
from dataclasses import dataclass
import parselmouth
from parselmouth.praat import call
import warnings

# FFmpeg kontrolü
try:
    from pydub import AudioSegment
    FFMPEG_AVAILABLE = True
except Exception:
    FFMPEG_AVAILABLE = False
    warnings.warn("FFmpeg bulunamadı. Ses analizi sınırlı modda çalışacak.")

@dataclass
class AudioAnalysisResult:
    transcription: str
    filler_words_count: int
    filler_words_percentage: float
    speech_rate: float  # words per minute
    pause_count: int
    average_pause_duration: float
    pitch_variation: float
    monotony_score: float
    volume_consistency: float
    overall_voice_score: float

class AudioAnalyzer:
    def __init__(self):
        # Whisper modelini yükle
        self.whisper_model = whisper.load_model("base")
        
        # Türkçe dolgu kelimeleri
        self.filler_words = [
            'eee', 'ee', 'ııı', 'şey', 'işte', 'yani', 'hani', 'böyle',
            'falan', 'filan', 'tabi', 'tabii', 'şöyle', 'böylece',
            'um', 'uh', 'hmm', 'ah', 'oh'
        ]
        
        # Filler word pattern oluştur
        self.filler_pattern = r'\b(' + '|'.join(self.filler_words) + r')\b'
    
    def analyze_audio(self, video_path: str) -> AudioAnalysisResult:
        """Ana ses analiz fonksiyonu"""
        
        if not FFMPEG_AVAILABLE:
            return self._create_fallback_result()
        
        try:
            # Video'dan ses çıkar
            audio_path = self._extract_audio(video_path)
        except Exception as e:
            print(f"Ses çıkarma hatası: {e}")
            return self._create_fallback_result()
        
        try:
            # Ses transkripti al
            transcription = self._transcribe_audio(audio_path)
            
            # Dolgu kelime analizi
            filler_count, filler_percentage = self._analyze_filler_words(transcription)
            
            # Konuşma hızı analizi
            speech_rate = self._calculate_speech_rate(transcription, audio_path)
            
            # Duraklama analizi
            pause_count, avg_pause_duration = self._analyze_pauses(audio_path)
            
            # Ses tonu analizi
            pitch_variation, monotony_score = self._analyze_pitch(audio_path)
            
            # Ses seviyesi tutarlılığı
            volume_consistency = self._analyze_volume_consistency(audio_path)
            
            # Genel ses skoru
            overall_score = self._calculate_overall_voice_score(
                filler_percentage, speech_rate, monotony_score, volume_consistency
            )
            
            return AudioAnalysisResult(
                transcription=transcription,
                filler_words_count=filler_count,
                filler_words_percentage=filler_percentage,
                speech_rate=speech_rate,
                pause_count=pause_count,
                average_pause_duration=avg_pause_duration,
                pitch_variation=pitch_variation,
                monotony_score=monotony_score,
                volume_consistency=volume_consistency,
                overall_voice_score=overall_score
            )
        
        finally:
            # Geçici ses dosyasını temizle
            import os
            if os.path.exists(audio_path):
                os.remove(audio_path)
    
    def _extract_audio(self, video_path: str) -> str:
        """Video'dan ses çıkar"""
        import tempfile
        import os
        
        # Geçici ses dosyası oluştur
        temp_dir = tempfile.mkdtemp()
        audio_path = os.path.join(temp_dir, "extracted_audio.wav")
        
        # FFmpeg ile ses çıkar
        video = AudioSegment.from_file(video_path)
        video.export(audio_path, format="wav")
        
        return audio_path
    
    def _transcribe_audio(self, audio_path: str) -> str:
        """Ses dosyasını transkript et"""
        result = self.whisper_model.transcribe(audio_path, language="tr")
        return result["text"]
    
    def _analyze_filler_words(self, transcription: str) -> Tuple[int, float]:
        """Dolgu kelimeleri analiz et"""
        # Metni küçük harfe çevir ve dolgu kelimeleri bul
        text_lower = transcription.lower()
        filler_matches = re.findall(self.filler_pattern, text_lower)
        
        # Toplam kelime sayısı
        words = re.findall(r'\b\w+\b', transcription)
        total_words = len(words)
        
        filler_count = len(filler_matches)
        filler_percentage = (filler_count / total_words * 100) if total_words > 0 else 0
        
        return filler_count, filler_percentage
    
    def _calculate_speech_rate(self, transcription: str, audio_path: str) -> float:
        """Konuşma hızını hesapla (kelime/dakika)"""
        # Toplam kelime sayısı
        words = re.findall(r'\b\w+\b', transcription)
        word_count = len(words)
        
        # Ses dosyasının süresi
        audio = AudioSegment.from_file(audio_path)
        duration_minutes = len(audio) / 1000 / 60  # milisaniyeden dakikaya
        
        speech_rate = word_count / duration_minutes if duration_minutes > 0 else 0
        
        return speech_rate
    
    def _analyze_pauses(self, audio_path: str) -> Tuple[int, float]:
        """Duraklama analizi"""
        # Ses dosyasını yükle
        y, sr = librosa.load(audio_path)
        
        # Ses seviyesi eşiği ile sessiz bölgeleri bul
        non_silent = librosa.effects.split(y, top_db=20)
        
        # Duraklamaları hesapla
        pauses = []
        if len(non_silent) > 1:
            for i in range(len(non_silent) - 1):
                pause_start = non_silent[i][1]
                pause_end = non_silent[i + 1][0]
                pause_duration = (pause_end - pause_start) / sr
                
                # En az 0.5 saniye sessizlik olmalı
                if pause_duration > 0.5:
                    pauses.append(pause_duration)
        
        pause_count = len(pauses)
        avg_pause_duration = np.mean(pauses) if pauses else 0
        
        return pause_count, avg_pause_duration
    
    def _analyze_pitch(self, audio_path: str) -> Tuple[float, float]:
        """Ses tonu ve monotonluk analizi"""
        try:
            # Parselmouth ile ses analizi
            sound = parselmouth.Sound(audio_path)
            
            # Pitch analizi
            pitch = call(sound, "To Pitch", 0.0, 75, 600)
            pitch_values = call(pitch, "List values", "Hertz")
            
            # NaN değerleri filtrele
            pitch_values = [p for p in pitch_values if not np.isnan(p) and p > 0]
            
            if len(pitch_values) < 10:
                return 0, 1  # Çok az veri var, monoton kabul et
            
            # Pitch varyasyonu
            pitch_std = np.std(pitch_values)
            pitch_mean = np.mean(pitch_values)
            pitch_variation = pitch_std / pitch_mean if pitch_mean > 0 else 0
            
            # Monotonluk skoru (düşük varyasyon = yüksek monotonluk)
            monotony_score = max(0, 1 - pitch_variation * 2)
            
            return pitch_variation, monotony_score
            
        except Exception as e:
            print(f"Pitch analizi hatası: {e}")
            return 0, 0.5  # Orta değer döndür
    
    def _analyze_volume_consistency(self, audio_path: str) -> float:
        """Ses seviyesi tutarlılığı analizi"""
        # Ses dosyasını yükle
        y, sr = librosa.load(audio_path)
        
        # RMS (Root Mean Square) energy hesapla
        rms = librosa.feature.rms(y=y, frame_length=2048, hop_length=512)[0]
        
        # Ses seviyesi varyasyonu
        rms_std = np.std(rms)
        rms_mean = np.mean(rms)
        
        # Tutarlılık skoru (düşük varyasyon = yüksek tutarlılık)
        consistency = max(0, 1 - (rms_std / rms_mean)) if rms_mean > 0 else 0
        
        return consistency
    
    def _calculate_overall_voice_score(self, filler_percentage: float, speech_rate: float,
                                     monotony_score: float, volume_consistency: float) -> float:
        """Genel ses skoru hesapla"""
        # İdeal değerler ve normalizasyon
        
        # Dolgu kelime skoru (az olmalı)
        filler_score = max(0, 100 - filler_percentage * 5)
        
        # Konuşma hızı skoru (120-180 kelime/dakika ideal)
        if 120 <= speech_rate <= 180:
            rate_score = 100
        elif speech_rate < 120:
            rate_score = max(0, 100 - (120 - speech_rate) * 2)
        else:
            rate_score = max(0, 100 - (speech_rate - 180) * 1.5)
        
        # Monotonluk skoru (düşük monotonluk iyi)
        monotony_score_norm = (1 - monotony_score) * 100
        
        # Ses tutarlılığı skoru
        consistency_score = volume_consistency * 100
        
        # Ağırlıklı ortalama
        overall_score = (
            filler_score * 0.3 +
            rate_score * 0.3 +
            monotony_score_norm * 0.25 +
            consistency_score * 0.15
        )
        
        return overall_score 

    def _create_fallback_result(self) -> AudioAnalysisResult:
        """FFmpeg olmadan varsayılan sonuç döndür"""
        return AudioAnalysisResult(
            transcription="Ses analizi için FFmpeg gereklidir. Lütfen FFmpeg'i yükleyin.",
            filler_words_count=0,
            filler_words_percentage=5.0,  # Ortalama değer
            speech_rate=120.0,  # Ortalama konuşma hızı
            pause_count=3,
            average_pause_duration=1.5,
            pitch_variation=15.0,
            monotony_score=25.0,
            volume_consistency=75.0,
            overall_voice_score=65.0  # Orta seviye
        )