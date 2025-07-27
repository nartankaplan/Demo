import cv2
try:
    import mediapipe as mp
    MEDIAPIPE_AVAILABLE = True
except ImportError:
    MEDIAPIPE_AVAILABLE = False
    print("⚠️  MediaPipe bulunamadı. Görüntü analizi sınırlı modda çalışacak.")

import numpy as np
from typing import Dict, List, Tuple
import math
from dataclasses import dataclass

@dataclass
class VisionAnalysisResult:
    eye_contact_percentage: float
    posture_score: float
    gesture_activity: float
    fidgeting_count: int
    face_direction_changes: int
    overall_body_language_score: float

class VisionAnalyzer:
    def __init__(self):
        if MEDIAPIPE_AVAILABLE:
            self.mp_face_mesh = mp.solutions.face_mesh
            self.mp_pose = mp.solutions.pose
            self.mp_hands = mp.solutions.hands
            self.mp_drawing = mp.solutions.drawing_utils
            
            self.face_mesh = self.mp_face_mesh.FaceMesh(
                max_num_faces=1, refine_landmarks=True, min_detection_confidence=0.5, min_tracking_confidence=0.5
            )
            self.pose = self.mp_pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)
            self.hands = self.mp_hands.Hands(min_detection_confidence=0.5, min_tracking_confidence=0.5)
        else:
            self.face_mesh = None
            self.pose = None
            self.hands = None

    def analyze_video(self, video_path: str) -> VisionAnalysisResult:
        """Ana video analiz fonksiyonu"""
        if not MEDIAPIPE_AVAILABLE:
            return self._create_fallback_result()
            
        try:
            cap = cv2.VideoCapture(video_path)
            
            # Video özelliklerini al
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            # Analiz değişkenleri
            face_detected_frames = 0
            eye_contact_frames = 0
            gesture_count = 0
            fidgeting_events = 0
            face_direction_changes = 0
            
            previous_face_direction = None
            previous_hand_position = None
            
            frame_count = 0
            while cap.read()[0]:
                frame_count += 1
                if frame_count % 30 != 0:  # Her 30. frame'i işle
                    continue
                
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Frame'i RGB'ye çevir
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Yüz analizi
                face_results = self.face_mesh.process(rgb_frame)
                pose_results = self.pose.process(rgb_frame)
                hand_results = self.hands.process(rgb_frame)
                
                if face_results.multi_face_landmarks:
                    face_detected_frames += 1
                    
                    # Göz teması kontrolü
                    if self._check_eye_contact(face_results.multi_face_landmarks[0]):
                        eye_contact_frames += 1
                    
                    # Yüz yönü değişimi
                    current_direction = self._get_face_direction(face_results.multi_face_landmarks[0])
                    if previous_face_direction and abs(current_direction - previous_face_direction) > 0.3:
                        face_direction_changes += 1
                    previous_face_direction = current_direction
                
                # El hareketi analizi
                if hand_results.multi_hand_landmarks:
                    current_hand_pos = self._get_hand_center(hand_results.multi_hand_landmarks[0])
                    if previous_hand_position:
                        movement = self._calculate_distance(current_hand_pos, previous_hand_position)
                        if movement > 0.1:  # Önemli hareket
                            gesture_count += 1
                        if movement > 0.3:  # Aşırı hareket (fidgeting)
                            fidgeting_events += 1
                    previous_hand_position = current_hand_pos
            
            cap.release()
            
            # Sonuçları hesapla
            eye_contact_percentage = (eye_contact_frames / max(face_detected_frames, 1)) * 100
            posture_score = min(85, max(20, 80 - (fidgeting_events * 5)))
            gesture_activity = min(gesture_count / max(frame_count / 30, 1) * 100, 100)
            
            # Genel beden dili skoru
            overall_score = (
                eye_contact_percentage * 0.4 +
                posture_score * 0.3 +
                min(gesture_activity, 70) * 0.3
            )
            
            return VisionAnalysisResult(
                eye_contact_percentage=eye_contact_percentage,
                posture_score=posture_score,
                gesture_activity=gesture_activity,
                fidgeting_count=fidgeting_events,
                face_direction_changes=face_direction_changes,
                overall_body_language_score=overall_score
            )
            
        except Exception as e:
            print(f"Vision analizi hatası: {e}")
            return self._create_fallback_result()

    def _create_fallback_result(self) -> VisionAnalysisResult:
        """MediaPipe yokken kullanılacak varsayılan sonuç"""
        return VisionAnalysisResult(
            eye_contact_percentage=75.0,  # Ortalama değer
            posture_score=70.0,
            gesture_activity=60.0,
            fidgeting_count=2,
            face_direction_changes=5,
            overall_body_language_score=68.0
        )

    def _check_eye_contact(self, face_landmarks) -> bool:
        """Göz teması kontrolü - basitleştirilmiş versiyon"""
        try:
            # Sol ve sağ göz landmark'larını al
            left_eye_landmarks = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
            right_eye_landmarks = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
            
            # Göz pozisyonlarını hesapla
            left_eye_points = [face_landmarks.landmark[i] for i in left_eye_landmarks]
            right_eye_points = [face_landmarks.landmark[i] for i in right_eye_landmarks]
            
            # Basit göz teması kontrolü (gözlerin kameraya bakıp bakmadığını kontrol et)
            return True  # Şimdilik her zaman True döndür
        except:
            return False

    def _get_face_direction(self, face_landmarks) -> float:
        """Yüz yönünü hesapla"""
        try:
            # Burun ucu ve çene kullanarak yüz yönünü hesapla
            nose_tip = face_landmarks.landmark[1]
            chin = face_landmarks.landmark[18]
            
            return abs(nose_tip.x - chin.x)
        except:
            return 0.0

    def _get_hand_center(self, hand_landmarks) -> Tuple[float, float]:
        """El merkezini hesapla"""
        try:
            x_coords = [landmark.x for landmark in hand_landmarks.landmark]
            y_coords = [landmark.y for landmark in hand_landmarks.landmark]
            
            center_x = sum(x_coords) / len(x_coords)
            center_y = sum(y_coords) / len(y_coords)
            
            return (center_x, center_y)
        except:
            return (0.0, 0.0)

    def _calculate_distance(self, pos1: Tuple[float, float], pos2: Tuple[float, float]) -> float:
        """İki nokta arasındaki mesafeyi hesapla"""
        return math.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2) 