"""
Unit tests for Prompt Manager.
"""

import pytest
from services.prompts import (
    get_prompt_manager,
    ConversationType,
    FewShotExample,
)


class TestPromptManager:
    """Test prompt manager functionality."""
    
    @pytest.fixture
    def manager(self):
        return get_prompt_manager()
    
    def test_detect_conversation_type_melasma(self, manager):
        """Should detect melasma conversation."""
        text = "ฝ้าบนใบหน้าหนักมาก"
        conv_type = manager.detect_conversation_type(text)
        
        assert conv_type == ConversationType.MELASMA_SPECIFIC
    
    def test_detect_conversation_type_purchase(self, manager):
        """Should detect purchase intent."""
        text = "สนใจค่ะ ราคาเท่าไหร่"
        conv_type = manager.detect_conversation_type(text)
        
        assert conv_type == ConversationType.PURCHASE_INTENT
    
    def test_detect_conversation_type_social(self, manager):
        """Should detect social chitchat."""
        text = "แอดน่ารักจัง"
        conv_type = manager.detect_conversation_type(text)
        
        assert conv_type == ConversationType.SOCIAL_CHITCHAT
    
    def test_build_prompt_includes_examples(self, manager):
        """Built prompt should include few-shot examples."""
        prompt = manager.build_prompt(
            user_message="ฝ้าหนักมาก ใช้อะไรดี",
            context="Product info...",
            conversation_type=ConversationType.MELASMA_SPECIFIC,
            num_examples=2
        )
        
        assert "ตัวอย่างการตอบ" in prompt
        assert "ลูกค้า:" in prompt
        assert "แอดมิน:" in prompt
    
    def test_build_prompt_includes_context(self, manager):
        """Built prompt should include context."""
        context = "เซรั่ม Vitamin C ราคา 590"
        prompt = manager.build_prompt(
            user_message="สนใจสินค้า",
            context=context,
            conversation_type=ConversationType.PRODUCT_INQUIRY
        )
        
        assert context in prompt
    
    def test_select_examples_returns_relevant(self, manager):
        """Should return relevant examples."""
        examples = manager._select_examples(
            ConversationType.MELASMA_SPECIFIC,
            "ฝ้าหนักมาก",
            num_examples=2
        )
        
        assert len(examples) > 0
        assert all(isinstance(ex, FewShotExample) for ex in examples)
    
    def test_get_conversation_type_name(self, manager):
        """Should return Thai name for type."""
        name = manager.get_conversation_type_name(ConversationType.MELASMA_SPECIFIC)
        
        assert "ฝ้า" in name


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
