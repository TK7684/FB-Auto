"""
Thai Language Helpers.

Provides Thai-specific linguistic considerations for natural,
culturally appropriate responses.
"""

import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class PolitenessLevel(Enum):
    """Thai politeness levels."""
    FORMAL = "formal"           # ค่ะ/ครับ, กรุณา
    CASUAL = "casual"           # ค่ะ/ครับ, นะ
    VERY_CASUAL = "very_casual"  # จ้า, ค้า, นะ


@dataclass
class ThaiLinguisticProfile:
    """Profile of Thai language characteristics in text."""
    politeness_level: PolitenessLevel
    gender_hint: str  # 'female', 'male', 'unknown'
    particles_used: List[str]
    formality_score: float  # 0.0 to 1.0


class ThaiLanguageHelper:
    """
    Helper for Thai-specific linguistic considerations.
    
    Features:
    - Politeness particle detection and matching
    - Gender hint detection
    - Formality level analysis
    - Skincare terminology
    """
    
    # Politeness particles by gender
    PARTICLES = {
        "female_formal": ["ค่ะ", "เจ้าค่ะ"],
        "female_casual": ["นะคะ", "ค่ะ"],
        "female_very_casual": ["นะ", "จ้า", "ค้า", "เจ้า"],
        "male_formal": ["ครับ", "เจ้าคะ"],
        "male_casual": ["นะครับ", "ครับ"],
        "male_very_casual": ["นะ", "จ้า", "ค้า"],
        "neutral": ["นะ", "จ้ะ", "จ้า"],
    }
    
    # Formal markers
    FORMAL_MARKERS = [
        "กรุณา", "ขอความกรุณา", "รบกวน", "ขออนุญาต",
        "ดิฉัน", "หนู", "ผม", "ดีครับ", "ดีค่ะ"
    ]
    
    # Casual markers
    CASUAL_MARKERS = [
        "555", "ฮา", "ช่วย", "หน่อย", "สิ", "เถอะ",
        "เธอ", "มึง", "กู", "เรา"
    ]
    
    # Gender indicators
    GENDER_INDICATORS = {
        "female": ["ค่ะ", "หนู", "ดิฉัน", "เธอ", "นาง"],
        "male": ["ครับ", "ผม", "พี่", "นาย", "ชาย"],
    }
    
    # Common skincare terms
    SKINCARE_TERMS = {
        "melasma": {
            "terms": ["ฝ้า", "ฝ้ากระ", "กระ", "จุดด่างดำ", "ผิวคล้ำ"],
            "treatments": ["ห้ามแดด", "กันแดด", "วิตามินซี", "ไนอาซินาไมด์", "ทรานซ์ซีแนมิค"],
        },
        "acne": {
            "terms": ["สิว", "สิวอักเสบ", "สิวหัวดำ", "สิวหัวขาว", "สิวเสี้ยน", "ผด"],
            "treatments": ["ซาลิไซลิก", "ทีทรี", "ไนอาซินาไมด์", "ห้ามบีบ"],
        },
        "dry_skin": {
            "terms": ["ผิวแห้ง", "แห้งกร้าน", "ลอก", "แตก", "ขาดน้ำ", "หยาบ"],
            "treatments": ["ไฮยาลูรอน", "มอยส์เจอไรเซอร์", "เซราไมด์"],
        },
        "wrinkles": {
            "terms": ["ริ้วรอย", "เหี่ยวย่น", "ตีนกา", "ผิวหย่อนคล้อย", "หย่อน"],
            "treatments": ["เรตินอล", "คอลลาเจน", "เปปไทด์", "วิตามินอี"],
        },
        "sunscreen": {
            "terms": ["กันแดด", "ครีมกันแดด", "แดด", "แสงแดด", "UV", "SPF"],
            "treatments": ["SPF50+", "PA+++", "ทาซ้ำ", "กันน้ำ"],
        },
    }
    
    @classmethod
    def detect_formality(cls, text: str) -> PolitenessLevel:
        """
        Detect formality level from user message.
        
        Args:
            text: User message text
            
        Returns:
            Detected politeness level
        """
        text_lower = text.lower()
        
        formal_score = 0
        casual_score = 0
        
        # Check formal markers
        for marker in cls.FORMAL_MARKERS:
            if marker in text_lower:
                formal_score += 1
        
        # Check casual markers
        for marker in cls.CASUAL_MARKERS:
            if marker in text_lower:
                casual_score += 1
        
        # Check particles
        for particle in ["ค่ะ", "ครับ"]:
            if particle in text:
                formal_score += 0.5
        
        for particle in ["จ้า", "ค้า", "นะ"]:
            if particle in text:
                casual_score += 1
        
        # Determine level
        if formal_score > casual_score:
            return PolitenessLevel.FORMAL
        elif casual_score > formal_score + 1:
            return PolitenessLevel.VERY_CASUAL
        else:
            return PolitenessLevel.CASUAL
    
    @classmethod
    def detect_gender_hint(cls, text: str) -> str:
        """
        Detect likely gender from message.
        
        Args:
            text: User message text
            
        Returns:
            'female', 'male', or 'unknown'
        """
        female_score = 0
        male_score = 0
        
        for indicator in cls.GENDER_INDICATORS["female"]:
            if indicator in text:
                female_score += 1
        
        for indicator in cls.GENDER_INDICATORS["male"]:
            if indicator in text:
                male_score += 1
        
        if female_score > male_score:
            return "female"
        elif male_score > female_score:
            return "male"
        return "unknown"
    
    @classmethod
    def get_linguistic_profile(cls, text: str) -> ThaiLinguisticProfile:
        """
        Get complete linguistic profile of text.
        
        Args:
            text: Text to analyze
            
        Returns:
            ThaiLinguisticProfile with analysis results
        """
        politeness = cls.detect_formality(text)
        gender = cls.detect_gender_hint(text)
        
        # Detect particles used
        all_particles = []
        for category, particles in cls.PARTICLES.items():
            for particle in particles:
                if particle in text:
                    all_particles.append(particle)
        
        # Calculate formality score
        formality_score = 0.5  # Default middle
        if politeness == PolitenessLevel.FORMAL:
            formality_score = 0.8
        elif politeness == PolitenessLevel.VERY_CASUAL:
            formality_score = 0.2
        
        return ThaiLinguisticProfile(
            politeness_level=politeness,
            gender_hint=gender,
            particles_used=list(set(all_particles)),
            formality_score=formality_score
        )
    
    @classmethod
    def add_appropriate_particle(
        cls,
        response: str,
        profile: ThaiLinguisticProfile,
        force_gender: Optional[str] = None
    ) -> str:
        """
        Add appropriate Thai politeness particle to response.
        
        Args:
            response: Response text (may or may not have particle)
            profile: Linguistic profile to match
            force_gender: Override detected gender
            
        Returns:
            Response with appropriate particle
        """
        gender = force_gender or profile.gender_hint
        
        # Default to female if unknown
        if gender == "unknown":
            gender = "female"
        
        # Check if already has particle
        has_particle = any(
            particle in response[-10:]  # Check end of response
            for particle_list in cls.PARTICLES.values()
            for particle in particle_list
        )
        
        if has_particle:
            return response
        
        # Select appropriate particle
        if profile.politeness_level == PolitenessLevel.FORMAL:
            particle = "ค่ะ" if gender == "female" else "ครับ"
        elif profile.politeness_level == PolitenessLevel.VERY_CASUAL:
            particle = "จ้า" if gender == "female" else "จ้า"
        else:
            particle = "นะคะ" if gender == "female" else "นะครับ"
        
        # Add particle to response
        return f"{response}{particle}"
    
    @classmethod
    def normalize_thai_text(cls, text: str) -> str:
        """
        Normalize Thai text for consistent processing.
        
        Args:
            text: Thai text to normalize
            
        Returns:
            Normalized text
        """
        # Remove excessive spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Normalize certain characters
        text = text.replace('ๅ', '์')  # Common typo
        
        # Standardize particle variations
        text = text.replace('คับ', 'ครับ')
        text = text.replace('ค่า', 'ค่ะ')
        
        return text.strip()
    
    @classmethod
    def detect_skin_concern(cls, text: str) -> List[Tuple[str, float]]:
        """
        Detect skin concerns mentioned in text with confidence scores.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of (concern_type, confidence) tuples
        """
        text_lower = text.lower()
        concerns = []
        
        for concern_type, data in cls.SKINCARE_TERMS.items():
            terms = data["terms"]
            matches = sum(1 for term in terms if term in text_lower)
            if matches > 0:
                confidence = min(1.0, matches / len(terms) + 0.3)
                concerns.append((concern_type, confidence))
        
        # Sort by confidence
        concerns.sort(key=lambda x: x[1], reverse=True)
        return concerns
    
    @classmethod
    def suggest_treatment_terms(cls, concern: str) -> List[str]:
        """
        Get treatment terms for a skin concern.
        
        Args:
            concern: Skin concern type
            
        Returns:
            List of treatment terms in Thai
        """
        data = cls.SKINCARE_TERMS.get(concern, {})
        return data.get("treatments", [])
    
    @classmethod
    def count_thai_characters(cls, text: str) -> int:
        """
        Count Thai characters in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Number of Thai characters
        """
        return len(re.findall(r'[\u0E00-\u0E7F]', text))
    
    @classmethod
    def contains_thai(cls, text: str) -> bool:
        """Check if text contains Thai characters."""
        return cls.count_thai_characters(text) > 0
    
    @classmethod
    def estimate_reading_time(cls, text: str) -> int:
        """
        Estimate reading time in seconds.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated seconds to read
        """
        # Thai reading speed ~ 200 chars/minute
        thai_chars = cls.count_thai_characters(text)
        other_chars = len(text) - thai_chars
        
        # Thai chars take longer to read
        total_time = (thai_chars / 200 + other_chars / 300) * 60
        return max(1, int(total_time))


class ThaiResponseFormatter:
    """
    Formatter for Thai responses with consistent styling.
    """
    
    # CTA templates
    CTA_TEMPLATES = {
        "line": "ทักไลน์มาได้เลยค่ะ 👉 @dplusskin 💕",
        "shop": "สนใจสั่งซื้อทักมาได้เลยค่ะ 💕",
        "consult": "มีคำถามเพิ่มเติมสอบถามได้นะคะ 😊",
        "try": "ลองใช้ดูนะคะ รับรองว่าชอบ 💕",
    }
    
    # Emoji sets by mood
    EMOJI_SETS = {
        "friendly": ["💕", "✨", "🌸", "😊"],
        "professional": ["📌", "✅", "💧", "🌿"],
        "urgent": ["⚠️", "❗", "💡", "🔥"],
        "celebration": ["🎉", "🎁", "✨", "💫"],
    }
    
    @classmethod
    def format_with_cta(
        cls,
        content: str,
        cta_type: str = "line",
        add_emoji: bool = True,
        emoji_mood: str = "friendly"
    ) -> str:
        """
        Format response with CTA.
        
        Args:
            content: Main response content
            cta_type: Type of CTA (line, shop, consult, try)
            add_emoji: Whether to add emoji
            emoji_mood: Mood for emoji selection
            
        Returns:
            Formatted response
        """
        parts = [content]
        
        # Add CTA
        cta = cls.CTA_TEMPLATES.get(cta_type, cls.CTA_TEMPLATES["line"])
        parts.append(f"\n\n{cta}")
        
        # Add emoji if requested
        if add_emoji and emoji_mood in cls.EMOJI_SETS:
            emojis = cls.EMOJI_SETS[emoji_mood]
            # Ensure at least one emoji from set is present
            if not any(e in content for e in emojis):
                parts.append(f" {emojis[0]}")
        
        return "".join(parts)
    
    @classmethod
    def format_bullet_points(
        cls,
        items: List[str],
        bullet: str = "•",
        header: Optional[str] = None
    ) -> str:
        """
        Format items as bullet points.
        
        Args:
            items: List of items
            bullet: Bullet character
            header: Optional header text
            
        Returns:
            Formatted bullet list
        """
        lines = []
        
        if header:
            lines.append(header)
        
        for item in items:
            lines.append(f"{bullet} {item}")
        
        return "\n".join(lines)
