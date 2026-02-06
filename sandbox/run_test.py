
import asyncio
import csv
import random
import os
import sys

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sandbox.content_gen import SandboxContentGenerator
from sandbox.image_gen import SandboxImageGenerator
from sandbox.fb_draft import SandboxFacebookPoster

PRODUCTS_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'products.csv')

async def main():
    print("--- Starting Sandbox Auto-Poster Test ---")
    
    # 1. Load Products
    print(f"Loading products from {PRODUCTS_FILE}...")
    products = []
    try:
        with open(PRODUCTS_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            products = list(reader)
    except Exception as e:
        print(f"Error loading products: {e}")
        return

    if not products:
        print("No products found.")
        return

    # 2. Select Product
    product = random.choice(products)
    print(f"Selected Product: {product.get('product_name', 'Unknown')}")
    print(f"Link: {product.get('Link', 'No Link')}")

    # 3. Generate Content
    print("\n--- Generating Content (Enriched Gen-Z Mode) ---")
    content_gen = SandboxContentGenerator()
    image_gen = SandboxImageGenerator()
    
    # Enrichment: Find and read text file
    enriched_context = ""
    text_ref = image_gen.find_reference_text(product.get('product_name', ''))
    if text_ref:
        print(f"Found enriched context file: {text_ref.name}")
        try:
            with open(text_ref, 'r', encoding='utf-8') as f:
                enriched_context = f.read()
        except Exception as e:
            print(f"Warning: Could not read text file: {e}")

    caption = await content_gen.generate_post(product, enriched_context=enriched_context)
    print(f"Generated Caption:\n{caption}")
    
    if not caption:
        print("Failed to generate caption.")
        return

    # 4. Generate/Find Image
    print("\n--- Handling Image ---")
    image_gen = SandboxImageGenerator()
    product_name = product.get('product_name', '')
    
    # Find reference
    ref_image = image_gen.find_reference_image(product_name)
    final_image_path = None
    
    if ref_image:
        print(f"Found reference image: {ref_image}")
        # Try to generate stylized version using Nanobanana
        # For now, we reuse the prompt logic or simple description
        prompt = f"A high quality commercial photography of {product_name}, aesthetic, soft lighting, 8k resolution."
        
        # generate_image returns a path to the generated file
        # generated_image_path = await image_gen.generate_image(prompt, reference_image_path=ref_image)
        
        # Since currently generate_image implementation is Text-to-Image and might not support ref image well without proper API
        # We will try to run it. If it fails or returns None, we fallback to uploading the Reference Image directly for this test.
        # Ideally, we want the generated one.
        
        print("Attempting to generate AI image...")
        generated_image_path = await image_gen.generate_image(prompt)
        
        if generated_image_path:
            print(f"Generated AI Image: {generated_image_path}")
            final_image_path = generated_image_path
        else:
            print("AI Generation failed. Using Reference Image as fallback.")
            final_image_path = ref_image
            
    else:
        print("No reference image found. Attempting Text-to-Image generation...")
        prompt = f"A high quality commercial photography of skincare product {product_name}, aesthetic, soft lighting."
        final_image_path = await image_gen.generate_image(prompt)

    # 5. Upload Draft
    print("\n--- Uploading Draft to Facebook ---")
    poster = SandboxFacebookPoster()
    
    post_id = await poster.create_draft_post(
        message=caption,
        link=product.get('Link'),
        image_path=str(final_image_path) if final_image_path else None
    )
    
    if post_id:
        print(f"\nSUCCESS! Draft created. ID: {post_id}")
        print("Please check Facebook Business Suite to review and publish.")
    else:
        print("\nFailed to create draft.")

if __name__ == "__main__":
    asyncio.run(main())
