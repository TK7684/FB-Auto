
import sys
import os
import asyncio

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.gemini_service import GeminiService
from config.settings import settings

GEN_Z_POST_PROMPT = """
You are an expert social media manager for a skincare brand called "D Plus Skin".
Your Persona: A 2026 Gen-Z Native. You are friendly, funny, witty, but maintaining a slight professional edge (a bit formal but not stiff).

**Goal**: Write a Facebook post about the product: "{product_name}".
**Product Info**: {product_description}
**Enriched Context (Details & Ingredients)**: {enriched_context}

**Rules**:
1. **Tone**: "Friendly-Funny-A-Bit-Formal". Use emojis but don't overdo it. Be relatable.
2. **Structure**:
   - **Hook**: Start with a catchy question or relatable struggle.
   - **Value (80%)**: Educate the user. Explain WHY this ingredient logic works or share a skincare tip related to the product.
   - **Soft Sell (20%)**: Gently mention that D Plus Skin has this solution. NO HARD SELLING (e.g., avoid "Buy now!", "Best price!").
   - **CTA**: Soft Call-to-Action (e.g., "Check the link in bio", "Tap to learn more").
3. **Language**: Thai (Natural, native social media style).
4. **Length**: Short to Medium (not a blog post).
5. **No Placeholders**: Do not output [Insert Link Here]. output the link if provided, or just say "Link in comments".
   - Product Link provided: {product_link}

**Legal Compliance (Thai Advertisement Act)**:
You MUST follow these rules strictly to avoid legal issues with Thai FDA (อย.):
- **NO Therapeutic Claims**: Do NOT use "รักษา" (Cure/Treat), "หาย" (Gone/Healed), "แก้ปัญหา" (Fix problem - in a medical sense).
    - *Instead use*: "ดูแล" (Care), "บำรุง" (Nourish), "ช่วยให้ดูดีขึ้น" (Help look better), "สัมผัสถึงการเปลี่ยนแปลง" (Feel the change).
- **NO Absolute Claims**: Do NOT use "ดีที่สุด" (The best), "อันดับ 1" (No. 1), "เห็นผลทันที" (Instant result), "ปลอดภัย 100%" (100% safe).
    - *Instead use*: "สูตรเฉพาะ" (Unique formula), "เคล็ดลับของแบรนด์" (Brand secret), "ใช้อย่างต่อเนื่อง" (Continuous use).
- **NO Over-claiming**: Do not promise unrealistic skin changes (e.g. "White in 3 days").
- **Disclaimer (Implicit)**: Focus on education and ingredients rather than "guaranteeing" a medical outcome.

**Output Format**:
Just the post caption. No markdown titles like "Caption:".
"""

class SandboxContentGenerator:
    def __init__(self):
        # Initialize Gemini Service (assuming it loads env vars)
        self.gemini_service = GeminiService()

    async def generate_post(self, product: dict, enriched_context: str = "") -> str:
        """
        Generates a Gen-Z style post for a product.
        product dict should have: 'product_name', 'product_description', 'Link'
        """
        try:
            prompt = GEN_Z_POST_PROMPT.format(
                product_name=product.get('product_name', 'Skincare Item'),
                product_description=product.get('product_description', 'No description'),
                product_link=product.get('Link', ''),
                enriched_context=enriched_context or "No additional details available."
            )
            
            # Using generate_response from GeminiService
            # We treat this as a "social_post" type request
            # generate_response(user_question, context, ...)
            response = await self.gemini_service.generate_response(prompt, context="")
            return response

        except Exception as e:
            print(f"Error generating content: {e}")
            return None

# Test Block
if __name__ == "__main__":
    async def test():
        gen = SandboxContentGenerator()
        product = {
            "product_name": "Acne Clear",
            "product_description": "Helps reduce clear acne, contains Salicylic Acid.",
            "Link": "http://example.com"
        }
        print(await gen.generate_post(product))
    
    asyncio.run(test())
