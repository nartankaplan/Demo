from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.piecharts import Pie
import io
import base64
from datetime import datetime
from typing import Dict, List, Any

from .analysis_orchestrator import OverallAnalysisResult

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.custom_styles = self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Özel stiller oluştur"""
        styles = {}
        
        # Başlık stilleri
        styles['CustomTitle'] = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Title'],
            fontSize=24,
            spaceAfter=30,
            textColor=colors.darkblue,
            alignment=1  # center
        )
        
        styles['SectionHeader'] = ParagraphStyle(
            'SectionHeader',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceBefore=20,
            spaceAfter=10,
            textColor=colors.darkblue,
            borderWidth=1,
            borderColor=colors.lightgrey,
            borderPadding=5
        )
        
        styles['SubsectionHeader'] = ParagraphStyle(
            'SubsectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=15,
            spaceAfter=8,
            textColor=colors.darkgreen
        )
        
        styles['HighlightBox'] = ParagraphStyle(
            'HighlightBox',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=10,
            borderWidth=1,
            borderColor=colors.lightblue,
            borderPadding=10,
            backColor=colors.lightcyan
        )
        
        return styles
    
    def generate_report(self, analysis_result: OverallAnalysisResult, 
                       output_path: str = None) -> bytes:
        """PDF raporu oluştur"""
        
        # PDF buffer
        buffer = io.BytesIO()
        
        # PDF dokümanı oluştur
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=18
        )
        
        # İçerik listesi
        story = []
        
        # Başlık
        story.append(Paragraph("🎓 EduView Analiz Raporu", self.custom_styles['CustomTitle']))
        story.append(Spacer(1, 20))
        
        # Genel bilgiler
        story.extend(self._create_overview_section(analysis_result))
        
        # Performans skoru
        story.extend(self._create_score_section(analysis_result))
        
        # Beden dili analizi
        story.extend(self._create_body_language_section(analysis_result))
        
        # Ses analizi
        story.extend(self._create_voice_analysis_section(analysis_result))
        
        # İçerik analizi
        story.extend(self._create_content_analysis_section(analysis_result))
        
        # Öneriler
        story.extend(self._create_recommendations_section(analysis_result))
        
        # Transkript
        story.extend(self._create_transcript_section(analysis_result))
        
        # PDF'i oluştur
        doc.build(story)
        
        # Buffer'dan byte'ları al
        pdf_bytes = buffer.getvalue()
        buffer.close()
        
        # Dosyaya kaydet (eğer path verilmişse)
        if output_path:
            with open(output_path, 'wb') as f:
                f.write(pdf_bytes)
        
        return pdf_bytes
    
    def _create_overview_section(self, result: OverallAnalysisResult) -> List:
        """Genel bilgiler bölümü"""
        content = []
        
        content.append(Paragraph("📊 Genel Bilgiler", self.custom_styles['SectionHeader']))
        
        # Analiz tarihi ve video bilgileri
        duration_str = f"{int(result.video_duration // 60)}:{int(result.video_duration % 60):02d}"
        
        info_data = [
            ['Analiz Tarihi:', result.analysis_timestamp.strftime('%d.%m.%Y %H:%M')],
            ['Video Süresi:', duration_str],
            ['Toplam Performans Skoru:', f"{result.total_score:.1f}/100"],
        ]
        
        info_table = Table(info_data, colWidths=[2*inch, 3*inch])
        info_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.darkblue),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(info_table)
        content.append(Spacer(1, 20))
        
        return content
    
    def _create_score_section(self, result: OverallAnalysisResult) -> List:
        """Performans skoru bölümü"""
        content = []
        
        content.append(Paragraph("🎯 Performans Skorları", self.custom_styles['SectionHeader']))
        
        # Performans seviyesi belirleme
        if result.total_score >= 85:
            level = "🏆 Mükemmel"
            level_color = colors.green
        elif result.total_score >= 75:
            level = "⭐ İyi"
            level_color = colors.orange
        elif result.total_score >= 65:
            level = "👍 Orta"
            level_color = colors.yellow
        else:
            level = "📈 Geliştirilmeli"
            level_color = colors.red
        
        # Genel performans kutusu
        performance_text = f"""
        <b>Genel Performans Seviyeniz: {level}</b><br/>
        <font size="18"><b>{result.total_score:.1f}/100</b></font>
        """
        
        content.append(Paragraph(performance_text, self.custom_styles['HighlightBox']))
        content.append(Spacer(1, 15))
        
        # Kategori skorları tablosu
        score_data = [
            ['Kategori', 'Puan', 'Yüzde', 'Değerlendirme'],
            ['Beden Dili', f"{result.body_language_score:.1f}/25", f"%{result.body_language_score*4:.0f}", self._get_score_rating(result.body_language_score, 25)],
            ['Ses Kalitesi', f"{result.voice_score:.1f}/25", f"%{result.voice_score*4:.0f}", self._get_score_rating(result.voice_score, 25)],
            ['İçerik Akışı', f"{result.content_flow_score:.1f}/25", f"%{result.content_flow_score*4:.0f}", self._get_score_rating(result.content_flow_score, 25)],
            ['Etkileşim', f"{result.interaction_score:.1f}/25", f"%{result.interaction_score*4:.0f}", self._get_score_rating(result.interaction_score, 25)],
        ]
        
        score_table = Table(score_data, colWidths=[2*inch, 1*inch, 1*inch, 1.5*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('ALTERNATEROWCOLOR', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(score_table)
        content.append(Spacer(1, 20))
        
        return content
    
    def _create_body_language_section(self, result: OverallAnalysisResult) -> List:
        """Beden dili analizi bölümü"""
        content = []
        
        content.append(Paragraph("👁️ Beden Dili Analizi", self.custom_styles['SectionHeader']))
        
        vision = result.vision_analysis
        
        body_data = [
            ['Metrik', 'Değer', 'Durum'],
            ['Göz Teması', f"%{vision.eye_contact_percentage:.1f}", self._get_eye_contact_status(vision.eye_contact_percentage)],
            ['Duruş Kalitesi', f"{vision.posture_score:.2f}/1.0", self._get_posture_status(vision.posture_score)],
            ['Jest Aktivitesi', f"{vision.gesture_activity:.2f}/1.0", self._get_gesture_status(vision.gesture_activity)],
            ['Gereksiz Hareketler', f"{vision.fidgeting_count} adet", self._get_fidgeting_status(vision.fidgeting_count)],
            ['Yüz Yönü Değişimi', f"{vision.face_direction_changes} kez", "Normal" if vision.face_direction_changes < 20 else "Fazla"],
        ]
        
        body_table = Table(body_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
        body_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(body_table)
        content.append(Spacer(1, 20))
        
        return content
    
    def _create_voice_analysis_section(self, result: OverallAnalysisResult) -> List:
        """Ses analizi bölümü"""
        content = []
        
        content.append(Paragraph("🎤 Ses Analizi", self.custom_styles['SectionHeader']))
        
        audio = result.audio_analysis
        
        voice_data = [
            ['Metrik', 'Değer', 'İdeal Aralık', 'Durum'],
            ['Konuşma Hızı', f"{audio.speech_rate:.0f} kelime/dk", "120-180 kelime/dk", self._get_speech_rate_status(audio.speech_rate)],
            ['Dolgu Kelimeleri', f"%{audio.filler_words_percentage:.1f} ({audio.filler_words_count} adet)", "<%5", self._get_filler_status(audio.filler_words_percentage)],
            ['Duraklamalar', f"{audio.pause_count} adet (ort. {audio.average_pause_duration:.1f}s)", "Doğal", "Normal"],
            ['Monotonluk', f"{audio.monotony_score:.2f}/1.0", "<0.7", self._get_monotony_status(audio.monotony_score)],
            ['Ses Tutarlılığı', f"{audio.volume_consistency:.2f}/1.0", ">0.7", "İyi" if audio.volume_consistency > 0.7 else "Geliştirilmeli"],
        ]
        
        voice_table = Table(voice_data, colWidths=[2*inch, 1.8*inch, 1.2*inch, 1*inch])
        voice_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightpink),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(voice_table)
        content.append(Spacer(1, 20))
        
        return content
    
    def _create_content_analysis_section(self, result: OverallAnalysisResult) -> List:
        """İçerik analizi bölümü"""
        content = []
        
        content.append(Paragraph("📚 İçerik Analizi", self.custom_styles['SectionHeader']))
        
        cont = result.content_analysis
        
        content_data = [
            ['Metrik', 'Puan', 'Durum'],
            ['İçerik Bütünlüğü', f"%{cont.content_completeness_score:.1f}", self._get_content_status(cont.content_completeness_score)],
            ['Konu Akışı', f"%{cont.topic_flow_score:.1f}", self._get_flow_status(cont.topic_flow_score)],
            ['Eğitimsel Yapı', f"%{cont.educational_structure_score:.1f}", self._get_structure_status(cont.educational_structure_score)],
            ['Etkileşim Örnekleri', f"{cont.interaction_examples_count} adet", "İyi" if cont.interaction_examples_count >= 5 else "Az"],
            ['Anahtar Kavramlar', f"{len(cont.key_concepts)} kavram", "Yeterli" if len(cont.key_concepts) >= 5 else "Az"],
        ]
        
        content_table = Table(content_data, colWidths=[2.5*inch, 1.5*inch, 2*inch])
        content_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkorange),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightyellow),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        content.append(content_table)
        
        # Anahtar kavramlar listesi
        if cont.key_concepts:
            content.append(Spacer(1, 10))
            content.append(Paragraph("🔑 Tespit Edilen Anahtar Kavramlar:", self.custom_styles['SubsectionHeader']))
            
            concepts_text = ", ".join(cont.key_concepts[:10])  # İlk 10 kavram
            content.append(Paragraph(concepts_text, self.styles['Normal']))
        
        # Eksik konular
        if cont.missing_topics:
            content.append(Spacer(1, 10))
            content.append(Paragraph("⚠️ Eksik Olabilecek Konular:", self.custom_styles['SubsectionHeader']))
            
            for topic in cont.missing_topics[:5]:  # İlk 5 eksik konu
                content.append(Paragraph(f"• {topic}", self.styles['Normal']))
        
        content.append(Spacer(1, 20))
        
        return content
    
    def _create_recommendations_section(self, result: OverallAnalysisResult) -> List:
        """Öneriler bölümü"""
        content = []
        
        content.append(Paragraph("💡 İyileştirme Önerileri", self.custom_styles['SectionHeader']))
        
        if result.recommendations:
            for i, rec in enumerate(result.recommendations, 1):
                content.append(Paragraph(f"{i}. {rec}", self.styles['Normal']))
                content.append(Spacer(1, 5))
        else:
            content.append(Paragraph("Performansınız genel olarak iyidir. Mevcut seviyenizi korumaya devam edin.", self.styles['Normal']))
        
        content.append(Spacer(1, 20))
        
        return content
    
    def _create_transcript_section(self, result: OverallAnalysisResult) -> List:
        """Transkript bölümü"""
        content = []
        
        content.append(PageBreak())
        content.append(Paragraph("📝 Video Transkripti", self.custom_styles['SectionHeader']))
        
        # Transkripti paragraflar halinde böl
        transcript = result.audio_analysis.transcription
        if len(transcript) > 1000:
            transcript = transcript[:1000] + "... (devamı için tam raporu inceleyiniz)"
        
        content.append(Paragraph(transcript, self.styles['Normal']))
        
        return content
    
    # Yardımcı metodlar
    def _get_score_rating(self, score: float, max_score: float) -> str:
        percentage = (score / max_score) * 100
        if percentage >= 80:
            return "Mükemmel"
        elif percentage >= 70:
            return "İyi"
        elif percentage >= 60:
            return "Orta"
        else:
            return "Geliştirilmeli"
    
    def _get_eye_contact_status(self, percentage: float) -> str:
        if percentage >= 70:
            return "Mükemmel"
        elif percentage >= 50:
            return "İyi"
        elif percentage >= 30:
            return "Orta"
        else:
            return "Zayıf"
    
    def _get_posture_status(self, score: float) -> str:
        if score >= 0.8:
            return "Mükemmel"
        elif score >= 0.6:
            return "İyi"
        else:
            return "Geliştirilmeli"
    
    def _get_gesture_status(self, score: float) -> str:
        if 0.3 <= score <= 0.8:
            return "Dengeli"
        elif score < 0.3:
            return "Az"
        else:
            return "Fazla"
    
    def _get_fidgeting_status(self, count: int) -> str:
        if count <= 5:
            return "İyi"
        elif count <= 15:
            return "Orta"
        else:
            return "Fazla"
    
    def _get_speech_rate_status(self, rate: float) -> str:
        if 120 <= rate <= 180:
            return "İdeal"
        elif 100 <= rate < 120 or 180 < rate <= 200:
            return "Kabul Edilebilir"
        else:
            return "Ayarlanmalı"
    
    def _get_filler_status(self, percentage: float) -> str:
        if percentage <= 3:
            return "Mükemmel"
        elif percentage <= 5:
            return "İyi"
        elif percentage <= 8:
            return "Orta"
        else:
            return "Fazla"
    
    def _get_monotony_status(self, score: float) -> str:
        if score <= 0.5:
            return "İyi"
        elif score <= 0.7:
            return "Orta"
        else:
            return "Monoton"
    
    def _get_content_status(self, score: float) -> str:
        if score >= 85:
            return "Mükemmel"
        elif score >= 75:
            return "İyi"
        elif score >= 65:
            return "Orta"
        else:
            return "Eksik"
    
    def _get_flow_status(self, score: float) -> str:
        return self._get_content_status(score)
    
    def _get_structure_status(self, score: float) -> str:
        return self._get_content_status(score) 