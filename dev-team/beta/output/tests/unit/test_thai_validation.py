"""
Unit tests for Thai Language Helpers.
"""

import pytest
from services.prompts.thai_language import (
    ThaiLanguageHelper,
    ThaiResponseFormatter,
    PolitenessLevel,
)


class TestThaiLanguageHelper:
    """Test Thai language helper functions."""
    
    def test_detect_formality_formal(self):
        """Should detect formal speech."""
        text = "กรุณาช่วยแนะนำสินค้าด้วยค่ะ"
        level = ThaiLanguageHelper.detect_formality(text)
        assert level == PolitenessLevel.FORMAL
    
    def test_detect_formality_casual(self):
        """Should detect casual speech."""
        text = "ช่วยแนะนำหน่อยนะคะ"
        level = ThaiLanguageHelper.detect_formality(text)
        assert level == PolitenessLevel.CASUAL
    
    def test_detect_formality_very_casual(self):
        """Should detect very casual speech."""
        text = "ช่วยแนะนำหน่อยจ้า"
        level = ThaiLanguageHelper.detect_formality(text)
        assert level == PolitenessLevel.VERY_CASUAL
    
    def test_detect_gender_hint_female(self):
        """Should detect female indicators."""
        text = "สนใจค่ะ อยากได้"
        gender = ThaiLanguageHelper.detect_gender_hint(text)
        assert gender == "female"
    
    def test_detect_gender_hint_male(self):
        """Should detect male indicators."""
        text = "สนใจครับ อยากได้"
        gender = ThaiLanguageHelper.detect_gender_hint(text)
        assert gender == "male"
    
    def test_detect_skin_concern_melasma(self):
        """Should detect melasma concerns."""
        text = "มีฝ้าที่แก้ม รักษายังไงดี"
        concerns = ThaiLanguageHelper.detect_skin_concern(text)
        
        assert len(concerns) > 0
        assert concerns[0][0] == "melasma"
    
    def test_detect_skin_concern_acne(self):
        """Should detect acne concerns."""
        text = "เป็นสิวอักเสบเยอะมาก"
        concerns = ThaiLanguageHelper.detect_skin_concern(text)
        
        assert any(c[0] == "acne" for c in concerns)
    
    def test_count_thai_characters(self):
        """Should count Thai characters correctly."""
        text = "สวัสดี hello 123"
        count = ThaiLanguageHelper.count_thai_characters(text)
        
        assert count == 8  # สวัสดี = 8 chars
    
    def test_contains_thai(self):
        """Should detect Thai content."""
        assert ThaiLanguageHelper.contains_thai("สวัสดี") is True
        assert ThaiLanguageHelper.contains_thai("Hello") is False
    
    def test_normalize_thai_text(self):
        """Should normalize Thai text."""
        text = "สวัสดี  ค่ะ   ที่   นี่"
        normalized = ThaiLanguageHelper.normalize_thai_text(text)
        
        assert "  " not in normalized


class TestThaiResponseFormatter:
    """Test Thai response formatter."""
    
    def test_format_with_cta_line(self):
        """Should format response with LINE CTA."""
        content = "สนใจสินค้าทักมาได้เลย"
        result = ThaiResponseFormatter.format_with_cta(content, cta_type="line")
        
        assert "@dplusskin" in result
        assert content in result
    
    def test_format_bullet_points(self):
        """Should format bullet points."""
        items = ["ข้อ 1", "ข้อ 2", "ข้อ 3"]
        result = ThaiResponseFormatter.format_bullet_points(items, header="รายการ:")
        
        assert "รายการ:" in result
        assert "• ข้อ 1" in result
        assert "• ข้อ 2" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
