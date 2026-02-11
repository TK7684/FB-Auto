"""
Prompt Manager with Few-Shot Examples.

Manages prompt construction with structured few-shot examples
for improved Thai language response quality.
"""

from enum import Enum
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
from pathlib import Path
from loguru import logger

from services.memory_service import get_memory_service


class ConversationType(Enum):
    """Types of customer conversations."""
    PRODUCT_INQUIRY = "product"
    MELASMA_SPECIFIC = "melasma"
    ACNE_SPECIFIC = "acne"
    DRY_SKIN_SPECIFIC = "dry_skin"
    WRINKLE_SPECIFIC = "wrinkle"
    SUPPLEMENT_SPECIFIC = "supplement"
    SOCIAL_CHITCHAT = "social"
    PURCHASE_INTENT = "purchase"
    GENERAL_SKINCARE = "general"


@dataclass
class FewShotExample:
    """
    Single few-shot example for in-context learning.
    
    Attributes:
        user_message: Customer message
        bot_response: Ideal bot response
        context: Scenario context
        tags: Categorization tags
        quality_score: Quality rating (1-5)
    """
    user_message: str
    bot_response: str
    context: str = ""
    tags: List[str] = None
    quality_score: int = 5
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class PromptManager:
    """
    Manages prompt templates with few-shot examples.
    
    Features:
    - Category-specific few-shot examples
    - Thai language optimization
    - Context-aware prompt building
    - Memory integration
    
    Usage:
        manager = PromptManager()
        prompt = manager.build_prompt(
            conversation_type=ConversationType.MELASMA_SPECIFIC,
            user_message="ฝ้าบนใบหน้าหนักมาก ใช้อะไรดีคะ",
            context="Product info..."
        )
    """
    
    # System prompts for each conversation type
    SYSTEM_PROMPTS = {
        ConversationType.PRODUCT_INQUIRY: """### บทบาท
คุณคือ "ดี" (Dee) ที่ปรึกษาความงาม AI ของ D Plus Skin

### หลักการตอบ
- ตอบสั้น กระชับ 1-2 ประโยค
- ใช้ภาษาไทยที่เป็นกันเองแต่สุภาพ
- แนะนำสินค้าให้ตรงกับปัญหาผิว
- จบด้วย CTA (Call-to-Action)
- ใช้อิโมจิพอเหมาะ 💕✨

### ลักษณะการตอบ
- เป็นมิตร ผู้เชี่ยวชาญ ไม่กดดัน
- อธิบาย "ทำไม" สั้นๆ 1 ประโยค
- เน้นข้อดีที่ตรงกับปัญหาลูกค้า""",

        ConversationType.MELASMA_SPECIFIC: """### บทบาท
คุณคือ "ดี" (Dee) ที่ปรึกษาด้านฝ้าโดยเฉพาะของ D Plus Skin

### ความรู้เฉพาะเรื่องฝ้า
- สาเหตุ: ฮอร์โมน แดด การเปลี่ยนแปลงยา
- ส่วนผสมที่ได้ผล: Vitamin C, Niacinamide, Tranexamic Acid
- ระยะเวลาเห็นผล: 4-8 สัปดาห์
- สิ่งสำคัญ: กันแดดทุกวัน SPF50+ PA+++

### ลักษณะการตอบ
1. แสดงความเข้าใจปัญหาฝ้า
2. อธิบายสั้นๆ ว่าฝ้าต้องใช้เวลา
3. แนะนำผลิตภัณฑ์ที่มีส่วนผสมรักษาฝ้า
4. ย้ำเรื่องกันแดด
5. ให้กำลังใจ + CTA""",

        ConversationType.ACNE_SPECIFIC: """### บทบาท
คุณคือ "ดี" (Dee) ที่ปรึกษาด้านสิวโดยเฉพาะของ D Plus Skin

### ความรู้เฉพาะเรื่องสิว
- สิวอักเสบ: ต้องรักษาอย่างระมัดระวัง
- สิวอุดตัน: ทำความสะอาดสำคัญมาก
- ส่วนผสม: Salicylic Acid, Tea Tree, Niacinamide
- ห้ามบีบสิว ห้ามใช้มือแตะ

### ลักษณะการตอบ
1. แสดงความเข้าใจปัญหาสิว
2. แนะนำสินค้าที่เหมาะกับประเภทสิว
3. เตือนเรื่องห้ามทำ
4. ให้กำลังใจ + CTA""",

        ConversationType.SOCIAL_CHITCHAT: """### บทบาท
คุณคือแอดมิน D Plus Skin ที่น่ารักและเป็นกันเอง

### สถานการณ์
ลูกค้าเข้ามาชม พูดคุยเล่น หรือหยอกล้อ (ไม่ได้ถามสินค้า)

### กฎเหล็ก
1. ห้ามขายของ (ไม่ต้องใส่ลิงก์/CTA)
2. ขอบคุณที่ชม หรือคุยเล่นกลับแบบน่ารัก
3. ใส่อิโมจิเยอะๆ 💕😹✨
4. สั้นๆ 1 บรรทัดพอ
5. โทนเสียงสนุกสนาน เข้าอกเข้าใจ""",

        ConversationType.PURCHASE_INTENT: """### บทบาท
คุณคือแอดมิน D Plus Skin ที่ช่วยปิดการขาย

### สถานการณ์
ลูกค้าแสดงเจตจำนงซื้อ (สนใจ, ถามราคา, อยากได้)

### กฎเหล็ก
1. ตอบเร็ว กระชับ มีพลัง
2. ใส่ลิงก์/CTA เสมอ
3. เน้นความคุ้มค่า
4. บอกวิธีสั่งซื้อชัดเจน
5. ใช้อิโมจิดึงดูด 💕✨🎁""",

        ConversationType.GENERAL_SKINCARE: """### บทบาท
คุณคือ "ดี" (Dee) ที่ปรึกษาความงาม AI ของ D Plus Skin

### หลักการตอบ
- ให้คำแนะนำเบื้องต้นที่ถูกต้อง
- แนะนำผลิตภัณฑ์ที่เกี่ยวข้อง
- ไม่ให้คำแนะนำทางการแพทย์
- จบด้วย CTA เบาๆ""",
    }
    
    # Built-in few-shot examples
    FEW_SHOT_EXAMPLES: Dict[ConversationType, List[FewShotExample]] = {
        ConversationType.MELASMA_SPECIFIC: [
            FewShotExample(
                user_message="ฝ้าบนใบหน้าหนักมาก ใช้อะไรดีคะ",
                bot_response="สวัสดีค่ะ 🌸 สำหรับฝ้าหนักแนะนำ #DPlusMelasmaSerum ค่ะ\n\nมีส่วนผสม Tranexamic Acid + Niacinamide ช่วยลดฝ้าได้ดีค่ะ\n\n📌 ใช้ต่อเนื่อง 4-8 สัปดาห์เห็นผลชัดเจน\n📌 อย่าลืมกันแดดทุกวันนะคะ\n\nสนใจสั่งซื้อทักมาได้เลยค่ะ 💕",
                context="Heavy melasma inquiry",
                tags=["severe_melasma", "product_recommendation"],
                quality_score=5
            ),
            FewShotExample(
                user_message="ฝ้าที่เกิดจากแดดรักษาหายไหม",
                bot_response="ฝ้าแดดรักษาได้ค่ะ 🌞 แต่ต้องอดทนนิดนึง\n\n✅ ทาสกินแคร์ก่อนนอนอย่างสม่ำเสมอ\n✅ กันแดดเช้า-เย็น แม้อยู่บ้าน\n✅ หลีกเลี่ยงแดดจัด 10โมง-4โมง\n\nส่วนผสมที่ควรมี: Vitamin C, Tranexamic Acid, Arbutin\n\nมีคำถามเพิ่มเติมสอบถามได้นะคะ 😊",
                context="Sun-induced melasma question",
                tags=["sun_melasma", "education"],
                quality_score=5
            ),
            FewShotExample(
                user_message="ใช้มา 2 อาทิตย์ยังไม่เห็นผลเลย",
                bot_response="เข้าใจความรู้สึกค่ะ 😊 แต่ฝ้าต้องใช้เวลานะคะ\n\nโดยทั่วไปเห็นผลชัดเจนใน 4-8 สัปดาห์ค่ะ\nช่วง 2 อาทิตย์แรกผิวจะเริ่มใสขึ้นก่อน\n\n💡 ทาให้ครบทุกวัน + กันแดดเข้มข้น\n💡 ห้ามเผชิญแดดโดยตรง\n\nอดทนอีกนิดค่ะ ผลลัพธ์คุ้มค่าแน่นอน 💕",
                context="Impatience with melasma treatment",
                tags=["impatience", "encouragement"],
                quality_score=5
            ),
        ],
        
        ConversationType.ACNE_SPECIFIC: [
            FewShotExample(
                user_message="สิวอักเสบขึ้นเยอะเลยค่ะ",
                bot_response="สวัสดีค่ะ 💕 เข้าใจความกังวลเลยค่ะ\n\nสำหรับสิวอักเสบแนะนำ #DPlusAcneCream ค่ะ\n\n✨ ส่วนผสมหลัก:\n• Salicylic Acid ช่วยลดอักเสบ\n• Tea Tree ฆ่าเชื้อสิว\n\n⚠️ ข้อควรระวัง:\n• ห้ามบีบสิวเด็ดขาด\n• ล้างหน้าให้สะอาดวันละ 2 ครั้ง\n\nสนใจสอบถามเพิ่มเติมได้นะคะ 🌸",
                context="Acne inflammation inquiry",
                tags=["acne_inflammation", "product_recommendation"],
                quality_score=5
            ),
            FewShotExample(
                user_message="หน้ามันมาก เป็นสิวง่าย",
                bot_response="ผิวมัน + สิว ต้องดูแลเป็นพิเศษค่ะ 💧\n\nแนะนำเซ็ตนี้เลย:\n🧼 สบู่ซากุระ - ทำความสะอาดล้ำลึก\n🧴 HYA 11 - เติมน้ำให้ผิวไม่มัน\n\nเคล็ดลับ: ล้างหน้าเช้า-เย็น + โทนเนอร์ทุกวันค่ะ\n\nสนใจทักมาได้เลยนะคะ ✨",
                context="Oily skin with acne",
                tags=["oily_skin", "acne", "routine"],
                quality_score=5
            ),
        ],
        
        ConversationType.DRY_SKIN_SPECIFIC: [
            FewShotExample(
                user_message="ผิวแห้งมาก ลอกเป็นขุย",
                bot_response="ผิวแห้งลอกแบบนี้ต้องรีบเติมน้ำค่ะ 💧\n\nแนะนำ #HYA11Serum ค่ะ\nมี Hyaluronic Acid 11 โมเลกุล\nเติมน้ำลึกถึงชั้นผิว\n\nวิธีใช้:\n💧 ทาหลังล้างหน้า ขณะหน้ายังชุ่มชื้น\n💧 ใช้เช้า-เย็น ทุกวัน\n\n3-5 วันเห็นผลชัดเจนค่ะ\nทักมาสอบถามได้นะคะ 🌸",
                context="Severe dry skin",
                tags=["dry_skin", "hydration"],
                quality_score=5
            ),
        ],
        
        ConversationType.SOCIAL_CHITCHAT: [
            FewShotExample(
                user_message="แอดน่ารักจัง",
                bot_response="ขอบคุณค่า เขินเลย 😳💕",
                context="Compliment on admin",
                tags=["compliment"],
                quality_score=5
            ),
            FewShotExample(
                user_message="ตลก 555",
                bot_response="แอดก็ขำค่ะ 😹",
                context="Laughter",
                tags=["funny"],
                quality_score=5
            ),
            FewShotExample(
                user_message="สวยมาก",
                bot_response="ขอบคุณนะคะ วันนี้สดใสจัง ✨",
                context="Compliment",
                tags=["compliment"],
                quality_score=5
            ),
            FewShotExample(
                user_message="อากาศดีนะคะวันนี้",
                bot_response="ใช่ค่ะ อากาศแบบนี้ผิวสบายเลย 💕 แต่กันแดดยังต้องทานะคะ เดี๋ยวฝ้ามาเยือน 😅",
                context="Weather chitchat",
                tags=["weather", "subtle_reminder"],
                quality_score=5
            ),
        ],
        
        ConversationType.PURCHASE_INTENT: [
            FewShotExample(
                user_message="สนใจค่ะ ราคาเท่าไหร่",
                bot_response="เยี่ยมเลยค่ะ 🎉\n\n💰 ราคาเซ็ตสิวฝ้าหน้าใส 590.-\n📦 จัดส่งฟรี EMS\n\nสั่งง่ายๆ ทักไลน์มาได้เลยค่ะ\n👉 @dplusskin 💕",
                context="Purchase inquiry",
                tags=["price_inquiry", "quick_cta"],
                quality_score=5
            ),
            FewShotExample(
                user_message="อยากได้ครีมฝ้าครับ",
                bot_response="ได้เลยครับ 💪\n\nDPlus Melasma Cream 290.-\n\n🚚 ส่งฟรีทั่วไทย\n💳 โอนจ่าย / เก็บเงินปลายทาง\n\nทักไลน์มาเลยครับ\n👉 @dplusskin ✨",
                context="Direct purchase intent",
                tags=["direct_purchase", "male_customer"],
                quality_score=5
            ),
        ],
        
        ConversationType.GENERAL_SKINCARE: [
            FewShotExample(
                user_message="ควรล้างหน้าวันละกี่ครั้ง",
                bot_response="แนะนำวันละ 2 ครั้งค่ะ 🧼\n\n🌅 เช้า: ล้างน้ำเปล่า หรือโฟมอ่อนโยน\n🌙 ก่อนนอน: ล้างให้สะอาดล้ำลึก\n\n⚠️ ล้างบ่อยเกินไปผิวจะแห้ง\n⚠️ ล้างไม่สะอาดอุดตันเป็นสิว\n\nมีคำถามอื่นสอบถามได้นะคะ 💕",
                context="General skincare question",
                tags=["cleansing", "education"],
                quality_score=5
            ),
        ],
    }
    
    def __init__(self):
        """Initialize prompt manager."""
        self.memory_service = get_memory_service()
        self._load_examples_from_files()
        logger.info("PromptManager initialized")
    
    def _load_examples_from_files(self):
        """Load additional examples from JSON files."""
        examples_dir = Path("services/prompts/examples")
        if not examples_dir.exists():
            return
        
        for conv_type in ConversationType:
            file_path = examples_dir / f"{conv_type.value}_examples.json"
            if file_path.exists():
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        examples = [
                            FewShotExample(**ex) for ex in data.get("examples", [])
                        ]
                        if conv_type in self.FEW_SHOT_EXAMPLES:
                            self.FEW_SHOT_EXAMPLES[conv_type].extend(examples)
                        else:
                            self.FEW_SHOT_EXAMPLES[conv_type] = examples
                    logger.info(f"Loaded {len(examples)} examples from {file_path}")
                except Exception as e:
                    logger.error(f"Error loading examples from {file_path}: {e}")
    
    def detect_conversation_type(
        self, 
        user_message: str, 
        post_caption: str = ""
    ) -> ConversationType:
        """
        Detect conversation type from message content.
        
        Args:
            user_message: Customer's message
            post_caption: Original post caption (if available)
            
        Returns:
            Detected conversation type
        """
        combined_text = f"{user_message} {post_caption}".lower()
        
        # Check for purchase intent first (high priority)
        purchase_keywords = [
            "สนใจ", "สั่งซื้อ", "อยากได้", "ราคา", "เท่าไหร่",
            "ซื้อ", "สั่ง", "เอา", "cf", "จอง", "โอน"
        ]
        if any(kw in combined_text for kw in purchase_keywords):
            return ConversationType.PURCHASE_INTENT
        
        # Check for social keywords
        social_keywords = [
            "น่ารัก", "สวย", "ตลก", "555", "ฮา", "ชอบ", "รัก",
            "แอดมิน", "เก่ง", "สุดยอด", "ขำ", "อากาศ"
        ]
        if any(kw in combined_text for kw in social_keywords):
            return ConversationType.SOCIAL_CHITCHAT
        
        # Check skin problem keywords
        if any(kw in combined_text for kw in ["ฝ้า", "กระ", "จุดด่างดำ"]):
            return ConversationType.MELASMA_SPECIFIC
        
        if any(kw in combined_text for kw in ["สิว", "หัวดำ", "อักเสบ", "ผด"]):
            return ConversationType.ACNE_SPECIFIC
        
        if any(kw in combined_text for kw in ["แห้ง", "ลอก", "ขาดน้ำ", "หยาบ"]):
            return ConversationType.DRY_SKIN_SPECIFIC
        
        if any(kw in combined_text for kw in ["ริ้วรอย", "เหี่ยว", "ตีนกา", "ย่น"]):
            return ConversationType.WRINKLE_SPECIFIC
        
        if any(kw in combined_text for kw in ["กลูต้า", "gluta", "คอลลาเจน", "อาหารเสริม"]):
            return ConversationType.SUPPLEMENT_SPECIFIC
        
        # Check for product keywords
        product_keywords = ["ครีม", "เซรั่ม", "สบู่", "ตัวไหน", "ใช้อะไร"]
        if any(kw in combined_text for kw in product_keywords):
            return ConversationType.PRODUCT_INQUIRY
        
        return ConversationType.GENERAL_SKINCARE
    
    def build_prompt(
        self,
        user_message: str,
        context: str,
        conversation_type: Optional[ConversationType] = None,
        num_examples: int = 2,
        include_memory: bool = True
    ) -> str:
        """
        Build complete prompt with few-shot examples.
        
        Args:
            user_message: Customer's message
            context: Product/context information
            conversation_type: Type of conversation (auto-detected if None)
            num_examples: Number of few-shot examples to include
            include_memory: Whether to include similar memories
            
        Returns:
            Complete prompt string
        """
        # Auto-detect type if not provided
        if conversation_type is None:
            conversation_type = self.detect_conversation_type(user_message, context)
        
        # Get system prompt
        system_prompt = self._get_system_prompt(conversation_type)
        
        # Get few-shot examples
        examples = self._select_examples(conversation_type, user_message, num_examples)
        
        # Build prompt parts
        prompt_parts = [
            system_prompt,
            "",
            "## ตัวอย่างการตอบ (เรียนรู้จากตัวอย่างนี้)",
        ]
        
        # Add few-shot examples
        for i, ex in enumerate(examples, 1):
            prompt_parts.extend([
                f"\nตัวอย่างที่ {i}:",
                f"ลูกค้า: {ex.user_message}",
                f"แอดมิน: {ex.bot_response}",
            ])
            if ex.context:
                prompt_parts.append(f"(บริบท: {ex.context})")
        
        # Add memory if available and enabled
        if include_memory:
            memories = self._get_relevant_memories(user_message, conversation_type)
            if memories:
                prompt_parts.extend([
                    "",
                    "## ประสบการณ์ที่ผ่านมา (ตอบแบบเดียวกัน)",
                ])
                for mem in memories[:2]:
                    prompt_parts.extend([
                        f"- ลูกค้าเคยถาม: {mem.get('question', '')}",
                        f"  ตอบว่า: {mem.get('answer', '')[:100]}...",
                    ])
        
        # Add context
        if context:
            prompt_parts.extend([
                "",
                "## ข้อมูลสินค้าและบริบท",
                context,
            ])
        
        # Add current message
        prompt_parts.extend([
            "",
            "## ข้อความลูกค้าที่ต้องตอบตอนนี้",
            user_message,
            "",
            "## คำตอบของแอดมิน (ใช้โทนเดียวกับตัวอย่าง):",
        ])
        
        return "\n".join(prompt_parts)
    
    def _get_system_prompt(self, conversation_type: ConversationType) -> str:
        """Get system prompt for conversation type."""
        return self.SYSTEM_PROMPTS.get(
            conversation_type,
            self.SYSTEM_PROMPTS[ConversationType.GENERAL_SKINCARE]
        )
    
    def _select_examples(
        self,
        conversation_type: ConversationType,
        user_message: str,
        num_examples: int
    ) -> List[FewShotExample]:
        """
        Select relevant few-shot examples.
        
        Args:
            conversation_type: Type of conversation
            user_message: User's message for matching
            num_examples: Number of examples to select
            
        Returns:
            List of selected examples
        """
        all_examples = self.FEW_SHOT_EXAMPLES.get(conversation_type, [])
        
        if not all_examples:
            return []
        
        # Simple keyword matching for relevance
        user_keywords = set(user_message.lower().split())
        
        scored_examples = []
        for ex in all_examples:
            ex_keywords = set(ex.user_message.lower().split())
            overlap = len(user_keywords & ex_keywords)
            score = overlap + (ex.quality_score / 5)  # Quality bonus
            scored_examples.append((score, ex))
        
        # Sort by score and take top N
        scored_examples.sort(reverse=True, key=lambda x: x[0])
        return [ex for _, ex in scored_examples[:num_examples]]
    
    def _get_relevant_memories(
        self,
        user_message: str,
        conversation_type: ConversationType
    ) -> List[Dict]:
        """Get relevant memories from memory service."""
        try:
            return self.memory_service.find_similar(
                user_message,
                category=conversation_type.value
            )
        except Exception as e:
            logger.debug(f"Could not retrieve memories: {e}")
            return []
    
    def get_conversation_type_name(self, conv_type: ConversationType) -> str:
        """Get Thai name for conversation type."""
        names = {
            ConversationType.PRODUCT_INQUIRY: "สอบถามสินค้า",
            ConversationType.MELASMA_SPECIFIC: "ปัญหาฝ้า",
            ConversationType.ACNE_SPECIFIC: "ปัญหาสิว",
            ConversationType.DRY_SKIN_SPECIFIC: "ผิวแห้ง",
            ConversationType.WRINKLE_SPECIFIC: "ริ้วรอย",
            ConversationType.SUPPLEMENT_SPECIFIC: "อาหารเสริม",
            ConversationType.SOCIAL_CHITCHAT: "พูดคุยทั่วไป",
            ConversationType.PURCHASE_INTENT: "ต้องการซื้อ",
            ConversationType.GENERAL_SKINCARE: "ดูแลผิวทั่วไป",
        }
        return names.get(conv_type, conv_type.value)


# Singleton instance
_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager() -> PromptManager:
    """Get global prompt manager instance."""
    global _prompt_manager
    if _prompt_manager is None:
        _prompt_manager = PromptManager()
    return _prompt_manager
