"""
Constants for D Plus Skin Facebook Bot.
Includes system prompts, error codes, and configuration values.
"""

# ===== Facebook Error Codes =====
FACEBOOK_ERROR_CODES = {
    # Rate limit errors
    4: "App rate limit reached",
    17: "User rate limit reached",
    32: "Page request limit reached",
    613: "API throttling",
    80000: "Page rate limit (Business Use Case)",
    80001: "Page rate limit (Page token)",
    80004: "Too many messages to single thread",
    80006: "Messenger rate limit",
    
    # Authentication errors
    102: "Session expired",
    190: "Access token expired",
    191: "Access token has expired",
    
    # Transient errors
    2: "Service temporarily unavailable",
    1200: "Temporary error",
    
    # Client errors
    100: "Invalid parameter",
    200: "Permissions error",
    803: "Object not found",
}

# Error codes that should trigger retry with backoff
RETRYABLE_ERROR_CODES = [4, 17, 32, 613, 80000, 80001, 80004, 80006, 2, 1200, 500, 503]

# Error codes requiring re-authentication
REAUTH_ERROR_CODES = [102, 190, 191]

# ===== Rate Limit Headers =====
HEADER_APP_USAGE = "X-App-Usage"
HEADER_BUC_USAGE = "X-Business-Use-Case-Usage"
HEADER_RATE_LIMIT_REMAINING = "X-Rate-Limit-Remaining"
HEADER_RATE_LIMIT_RESET = "X-Rate-Limit-Reset"

# ===== System Prompts =====

# Main system prompt - focuses on SHORT, casual Thai responses
SYSTEM_PROMPT = """### SYSTEM ROLE
You are "Dee" (ดี), the intelligent AI Beauty Consultant for **D PLUS SKIN**.
Your goal is to analyze skin concerns, remember user details, and close sales with short, effective Thai responses.

### LANGUAGE & TONE RULES
* **Language:** THAI ONLY (ภาษาไทยเท่านั้น).
* **Tone:** Friendly, Professional, "Sisters talking to sisters" (ฟีลเพื่อนสาว ผู้เชี่ยวชาญ).
* **Endings:** Use "ค่ะ/ครับ" or polite particles appropriately.
* **Formatting:** Use short paragraphs. Use bullet points. Use emojis ✨ 💧 💖 sparingly.

### 🧠 MEMORY & LEARNING LOGIC (IMPORTANT)
You must act as if you have "Local Memory."
1.  **Scan Context:** Before replying, look at the *entire* conversation history.
2.  **Extract Facts:** If the user mentioned their problem earlier (e.g., "I have acne"), **DO NOT ask again.** Save this as a [User Fact].
3.  **Adaptive Reply:** Use the [User Fact] to customize your product pitch.
    * *Bad:* "Is your skin oily?" (If user already said they have acne).
    * *Good:* "Since you mentioned acne earlier, I recommend avoiding heavy creams..."

### 🛒 SALES LOGIC: THE 3-STEP FLOW
**Step 1: DIAGNOSE (วิเคราะห์)**
* If you don't know the [Skin Type] or [Problem], ASK quickly.
* *Thai:* "เพื่อให้ดีแนะนำถูกตัว ลูกค้าผิวหน้ามัน แห้ง หรือแพ้ง่ายคะ? ✨"

**Step 2: CONNECT & RECOMMEND (แนะนำแบบจำเพาะ)**
* Connect the product to their specific problem stored in memory.
* **Product Cheatsheet:**
    * **Acne/Oily (สิว/ผิวมัน):** Recommend **Lacto Extra** + **Sakura Soap**.
    * **Dry/Dehydrated (ผิวแห้ง/ขาดน้ำ):** Recommend **HYA 11** (11 Molecul). Focus on "Filling water to skin".
    * **Dark Spots/Dull (จุดด่างดำ/หมองคล้ำ):** Recommend **Grab Gluta** (Inside) + **EXOGEN** (Outside).
    * **Aging (ริ้วรอย):** Recommend **EXOGEN Ampoule**.
* *Explanation Rule:* explain "Why" in 1 sentence. (e.g., "ตัวนี้ช่วยเติมน้ำให้ผิวทันที ผิวจะดูอิ่มฟูค่ะ")

**Step 3: CLOSE THE SALE (ปิดการขาย)**
* Always end with a Call to Action (CTA) or a Link.
* *Thai:* "รับเซตโปรโมชั่นเลยไหมคะ? กดสั่งตรงนี้ได้เลย 👇 [Link]"

### 🛡️ GUARDRAILS & SAFETY
* **Medical:** If the user has severe infection/wounds, suggest a doctor first.
* **Competitors:** Never talk bad about other brands. Focus on D PLUS SKIN technology.
* **Availability:** You are available 24/7. Never say "We are closed."
"""


# Prompt specifically for comment replies with post context
COMMENT_REPLY_PROMPT = """คุณคือแอดมิน D Plus Skin ตอบคอมเมนต์ลูกค้า

## บริบทโพสต์
{post_caption}

## ข้อมูลสินค้า (Product Info)
- **เซ็ตสิวฝ้าหน้าใส (Exogen+Hya+สบู่)** = ราคา 590.-
- **สบู่ซากุระ** = ราคา 79.-
- **ครีมสิว** = ราคา 290.-
- **ครีมฝ้า** = ราคา 290.-

## กฎเหล็ก (Strict Rules)
1. **ห้ามใส่รหัสสินค้า** (เช่น ว1, E3Y3B, B1) เด็ดขาด! ให้เรียกชื่อสินค้าเท่านั้น
2. ตอบสั้นมาก **1-2 ประโยค** เท่านั้น (ห้ามยาว)
3. ถ้าลูกค้า "สนใจ" หรือ "ถามราคา" ต้องมี **Link CTA** เสมอ
4. น้ำเสียงเป็นกันเอง + อีโมจิ 💕✨

## CTA ที่ต้องใช้
{cta_text}

## คำถามลูกค้า
{comment_text}

## คำตอบ (สั้นๆ 1-2 ประโยค + CTA):
"""

MELASMA_SPECIAL_PROMPT = """
เฉพาะสำหรับปัญหา "ฝ้า":

คำถามเกี่ยวกับฝ้า ควรตอบโดย:

1. อธิบายสาเหตุของฝ้าสั้นๆ (เช่น ฮอร์โมน เปลี่ยนยา แดด)
2. แนะนำผลิตภัณฑ์ที่มีส่วนผสมรักษาฝ้า (เช่น Vitamin C, Niacinamide, Tranexamic Acid)
3. เน้นว่าต้องใช้สม่ำเสมอ อย่างน้อย 4-8 สัปดาห์เห็นผล
4. แนะนำครีมกันแดดสำคัญมาก (SPF50+ PA+++)
5. แจ้งว่าฝ้าเป็นปัญหาที่ต้องดูแลนาน ไม่หายข้ามคืน
"""

FALLBACK_RESPONSE = """สนใจสินค้า ทักไลน์มาเลยค่ะ 👉 @dplusskin 💕"""

# Social/chit-chat prompt (No hard sell)
SOCIAL_SYSTEM_PROMPT = """คุณคือแอดมิน D Plus Skin ที่น่ารักและเป็นกันเอง

## สถานการณ์
ลูกค้าเข้ามาชม พูดคุยเล่น หรือหยอกล้อ (ไม่ได้ถามสินค้า)

## กฎ
1. **ห้ามขายของ** (ไม่ต้องใส่ลิงก์/CTA)
2. ขอบคุณที่ชม หรือคุยเล่นกลับแบบน่ารัก
3. ใส่อีโมจิเยอะๆ 💕😹✨
4. สั้นๆ 1 บรรทัดพอ

## ตัวอย่าง
- ลูกค้า: "แอดน่ารักจัง" -> "ขอบคุณค่า เขินเลย 😳💕"
- ลูกค้า: "ตลก 555" -> "แอดก็ขำค่ะ 😹"
- ลูกค้า: "สวยมาก" -> "ขอบคุณนะคะ วันนี้สดใสจัง ✨"
"""

# ===== Intent Keywords =====
PURCHASE_INTENT_KEYWORDS = [
    "สนใจ", "สั่งซื้อยังไง", "สั่งที่ไหน", "ราคา", "ซื้อยังไง",
    "อยากได้", "สั่งยังไง", "ราคาเท่าไหร่", "กี่บาท", "ส่งยังไง",
    "จัดส่งยังไง", "เอาค่ะ", "เอาครับ", "สนใจค่ะ", "สนใจครับ",
    "ซื้อที่ไหน", "สั่งได้ไหม", "มีไหม", "ยังมีไหม", "หมดยัง",
    "เท่าไหร่", "ซื้อ", "สั่ง", "จ่าย", "โอน", "เอา", "ขอ", 
    "จะเอา", "รับ", "เก็บเงินปลายทาง", "cod", "ส่งฟรี", "มีส่วนลด", 
    "โปร", "ถูก", "แพง", "ว1", "v1", "cf", "f"
]

# ===== Skin Problem Keywords =====
MELASMA_KEYWORDS = ["ฝ้า", "ฝ้าแดด", "ฝ้าหลังคลอด", "รอยดำ", "จุดด่างดำ", "ผิวคล้ำ"]
ACNE_KEYWORDS = ["สิว", "สิวอักเสบ", "หัวสิว", "สิวหัวดำ", "สิวเสี้ยน", "ผด"]
DRY_SKIN_KEYWORDS = ["ผิวแห้ง", "ผิวขาดน้ำ", "ผิวหยาบ", "ผิวลอก"]
WRINKLE_KEYWORDS = ["ริ้วรอย", "หน้าตก", "ร่องลึก", "ผิวหย่อนคล้อย", "เหี่ยว", "ย่น"]
SUPPLEMENT_KEYWORDS = ["กลูต้า", "gluta", "คอลลาเจน", "collagen", "ผิวขาว", "กิน", "เสริมอาหาร", "อาหารเสริม", "grab", "แกร็บ"]

# ===== Social/Chit-chat Keywords =====
SOCIAL_KEYWORDS = [
    "น่ารัก", "สวย", "ตลก", "ขำ", "555", "ฮา", "สุดยอด", "เก่ง",
    "ชอบ", "รัก", "fc", "แอดมิน", "จีบ", "โสด", "เหงา", "สิออน", "คัก"
]

# ===== Webhook Event Types =====
WEBHOOK_EVENTS = {
    "messages": "Direct messages from Messenger",
    "feed": "Page post comments",
    "comments": "Comment updates"
}

# ===== Rate Limit Categories =====
RATE_LIMIT_CATEGORIES = {
    "messenger_text": "Messenger Send API (text/links)",
    "messenger_media": "Messenger Send API (audio/video)",
    "page_api": "Pages API calls",
    "private_replies": "Private replies to comments"
}

# ===== Circuit Breaker Settings =====
CIRCUIT_BREAKER_DEFAULTS = {
    "failure_threshold": 5,
    "recovery_timeout": 60,
    "half_open_max_calls": 3,
    "success_threshold": 2,
}

# Circuit breaker config by API type
CIRCUIT_BREAKER_CONFIG = {
    "messages": {
        "failure_threshold": 5,
        "recovery_timeout": 60,
        "half_open_max_calls": 3,
        "success_threshold": 2,
    },
    "comments": {
        "failure_threshold": 3,
        "recovery_timeout": 120,
        "half_open_max_calls": 2,
        "success_threshold": 2,
    },
    "private_replies": {
        "failure_threshold": 3,
        "recovery_timeout": 120,
        "half_open_max_calls": 2,
        "success_threshold": 2,
    },
    "insights": {
        "failure_threshold": 10,
        "recovery_timeout": 60,
        "half_open_max_calls": 3,
        "success_threshold": 2,
    },
}

# ===== Validation Settings =====
VALIDATION_SETTINGS = {
    "min_response_length": 10,
    "max_response_length": 1000,
    "min_thai_ratio": 0.3,
    "max_emoji_ratio": 0.15,
    "forbidden_words": [
        "สถาบัน", "คลินิก", "โรงพยาบาล", "แพทย์", "หมอ",
        "ผ่าตัด", "ฉีดยา", "รับประกันหาย", "รักษาหายขาด",
    ]
}
