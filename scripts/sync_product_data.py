import csv
import json
import os
import re

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_PATH = os.path.join(BASE_DIR, 'data', 'products.csv')
CTA_PATH = os.path.join(BASE_DIR, 'data', 'products_cta.json')
MEMORY_PATH = os.path.join(BASE_DIR, 'data', 'memory.json')
CONSTANTS_PATH = os.path.join(BASE_DIR, 'config', 'constants.py')

def load_csv_products():
    products = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)
        # Skip header lines until we find the real header "ชื่อสินค้า"
        start_idx = 0
        for i, row in enumerate(rows):
            if row and "ชื่อสินค้า" in row[0]:
                start_idx = i + 1
                break
        
        for row in rows[start_idx:]:
            if len(row) >= 2:
                name = row[0].strip()
                desc = row[1].strip()
                link = row[2].strip() if len(row) > 2 else ""
                if name:
                    products.append({
                        "name": name,
                        "description": desc,
                        "link": link
                    })
    return products

def generate_constants_update(products):
    # This generates the "ข้อมูลสินค้าละเอียด" section
    lines = []
    for i, p in enumerate(products, 1):
        # Clean description to be concise (first sentence or first 100 chars?)
        # User wants "Description" applied.
        # Format: 1. **Name**: Description
        clean_desc = p['description'].replace('\n', ' ').strip()
        line = f"{i}. **{p['name']}**: {clean_desc}"
        lines.append(line)
    return "\n".join(lines)

def update_cta_json(products):
    try:
        with open(CTA_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except:
        data = {"categories": {}}

    # We'll add a "products_catalog" category or similar, or just try to categorize
    # For now, let's create a "All Products" category if strict matching fails
    # But user wants "products_cta.json" updated. 
    # The current structure has 'categories'.
    # We can add a specialized "Catalog" category or append to "General".
    
    # Actually, a better way is to update the 'products' list in existing categories if keywords match,
    # or just add them to the 'purchase_intent_keywords' or similar? No.
    
    # Let's add them to a new structure "catalog" inside json if it allows, or just ignore for now as 
    # strict categorization is hard without AI.
    # However, I can create a simple 'catalog' mapping in the JSON for direct name lookups.
    
    catalog = {}
    for p in products:
        catalog[p['name']] = {
            "description": p['description'],
            "link": p['link']
        }
    
    data['product_catalog'] = catalog
    return data

def update_memory_json(products):
    try:
        with open(MEMORY_PATH, 'r', encoding='utf-8') as f:
            memory = json.load(f)
    except:
        memory = []

    # Create a set of existing questions to avoid dups
    existing_qs = set(m['question'] for m in memory)
    
    new_memory = memory.copy()
    from datetime import datetime
    
    for p in products:
        # Q: สนใจ [Item]
        q1 = f"สนใจ {p['name']}"
        if q1 not in existing_qs:
            new_memory.append({
                "question": q1,
                "answer": f"ได้เลยค่ะ {p['name']} {p['description'][:50]}... 👉 {p['link']} 💕",
                "category": "product_interest",
                "timestamp": datetime.now().isoformat()
            })
            existing_qs.add(q1)
            
        # Q: [Item] คืออะไร
        q2 = f"{p['name']} คืออะไร"
        if q2 not in existing_qs:
            new_memory.append({
                "question": q2,
                "answer": f"{p['name']} คือ {p['description']} 👉 {p['link']} ✨",
                "category": "product_info",
                "timestamp": datetime.now().isoformat()
            })
            existing_qs.add(q2)

    return new_memory

def main():
    products = load_csv_products()
    print(f"Loaded {len(products)} products.")
    
    # 1. Constants Snippet
    constants_text = generate_constants_update(products)
    with open('constants_update.txt', 'w', encoding='utf-8') as f:
        f.write(constants_text)
    print("Saved constants_update.txt")
    
    # 2. CTA JSON
    cta_data = update_cta_json(products)
    with open(CTA_PATH, 'w', encoding='utf-8') as f:
        json.dump(cta_data, f, ensure_ascii=False, indent=4)
    print(f"\nUpdated {CTA_PATH}")
    
    # 3. Memory JSON
    memory_data = update_memory_json(products)
    with open(MEMORY_PATH, 'w', encoding='utf-8') as f:
        json.dump(memory_data, f, ensure_ascii=False, indent=2)
    print(f"Updated {MEMORY_PATH}")

if __name__ == "__main__":
    main()
