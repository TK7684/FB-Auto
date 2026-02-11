import pytest
from unittest.mock import MagicMock, patch
from services.gemini_service import GeminiService
from config.constants import COMMENT_REPLY_PROMPT, SYSTEM_PROMPT

@pytest.fixture
def mock_gemini_service():
    with patch("services.gemini_service.settings") as mock_settings:
        mock_settings.gemini_api_key = "test_key"
        mock_settings.gemini_model = "gemini-test"
        mock_settings.openrouter_api_key = None
        
        with patch("services.gemini_service.genai"):
            service = GeminiService(api_key="test_key")
            service.memory_service = MagicMock()
            service.model = MagicMock()
            return service

def test_detect_skin_category(mock_gemini_service):
    service = mock_gemini_service
    
    # Test Acne
    assert service._detect_skin_category("เป็นสิวเยอะมาก") == "สิว"
    assert service._detect_skin_category("หน้ามัน รูขุมขนกว้าง") == "สิว"
    
    # Test Melasma
    assert service._detect_skin_category("มีฝ้ากระ จุดด่างดำ") == "ฝ้า"
    
    # Test Supplement
    assert service._detect_skin_category("อยากผิวขาว กินตัวไหนดี") == "อาหารเสริม"
    assert service._detect_skin_category("สนใจกลูต้า") == "อาหารเสริม"
    
    # Test Aging
    assert service._detect_skin_category("ริ้วรอยเยอะ ตีนกาขึ้น") == "ริ้วรอย"
    
    # Test General
    assert service._detect_skin_category("สวัสดีค่ะ") == "ทั่วไป"

def test_is_purchase_intent(mock_gemini_service):
    service = mock_gemini_service
    
    # Strong intent
    assert service._is_purchase_intent("สนใจค่ะ") is True
    assert service._is_purchase_intent("ราคาเท่าไหร่") is True
    assert service._is_purchase_intent("ขอรายละเอียดสั่งซื้อ") is True
    assert service._is_purchase_intent("รับโปรนี้") is True
    
    # No intent
    assert service._is_purchase_intent("ใช้ดีไหมคะ") is False
    assert service._is_purchase_intent("คนท้องใช้ได้ไหม") is False

def test_get_cta_for_category(mock_gemini_service):
    service = mock_gemini_service
    
    # Test default CTAs
    cta = service._get_cta_for_category("สิว")
    # Expect specific product recommendation for Acne
    assert "Exogen" in cta or "แนะนำ" in cta
    assert "shopee" in cta or "line.me" in cta
    
    # Test specific product context (if configured in CTA_CONFIG, otherwise default)
    # Assuming default config behavior here as we mock file load or rely on default dict

def test_build_prompt_social(mock_gemini_service):
    service = mock_gemini_service
    prompt = service._build_prompt("น่ารักจังเลยแอด", "", [])
    assert "## ตอบกลับ (สั้นๆ น่ารัก):" in prompt
    assert "ห้ามขายของ" in prompt # Correct, SOCIAL_PROMPT logic is used

def test_build_prompt_buying_intent(mock_gemini_service):
    service = mock_gemini_service
    
    # Buying intent shoud trigger short prompt + CTA
    prompt = service._build_prompt("ราคาเท่าไหร่คะ", "", [])
    assert "## กฎเหล็ก (Strict Rules)" in prompt
    assert "ต้องมี **Link CTA** เสมอ" in prompt
    assert "ตอบสั้นมาก **1-2 ประโยค** เท่านั้น" in prompt

def test_build_prompt_with_post_context(mock_gemini_service):
    service = mock_gemini_service
    
    context = "บริบทโพสต์: โปรโมชั่นลด 50% เซ็ตสิว\n\nข้อมูลสินค้า..."
    prompt = service._build_prompt("สนใจค่ะ", context, [])
    
    assert "โปรโมชั่นลด 50% เซ็ตสิว" in prompt
    assert "## กฎเหล็ก (Strict Rules)" in prompt # Short prompt due to intent/context

@pytest.mark.asyncio
async def test_generate_reply_flow(mock_gemini_service):
    service = mock_gemini_service
    
    # Mock Gemini response
    service.model.generate_content.return_value.text = "เซ็ตสิวราคา 590.- ค่า สนใจทักแชทเลย 👇"
    
    reply = await service.generate_reply("ราคาเท่าไหร่คะ", reply_mode="public_link")
    
    assert "เซ็ตสิวราคา 590.-" in reply
    service.model.generate_content.assert_called_once()
    
    # Check prompt passed to model
    args, _ = service.model.generate_content.call_args
    prompt_sent = args[0]
    assert "ราคาเท่าไหร่คะ" in prompt_sent
    assert "## CTA ที่ต้องใช้" in prompt_sent
