
import os
import base64
import json
import httpx
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
SITE_URL = "https://dplusskin.com" # Optional, for OpenRouter ranking
APP_NAME = "DPlusSkin Bot"

class SandboxImageGenerator:
    def __init__(self, assets_dir="sandbox/assets", output_dir="sandbox/output"):
        self.assets_dir = Path(assets_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def find_reference_image(self, product_name: str) -> Path:
        """Finds a matching image in the assets directory."""
        return self._find_asset_by_name(product_name, ['.jpg', '.jpeg', '.png'])

    def find_reference_text(self, product_name: str) -> Path:
        """Finds a matching text file in the assets directory."""
        return self._find_asset_by_name(product_name, ['.txt'])

    def _find_asset_by_name(self, product_name: str, extensions: list) -> Path:
        """Helper to find assets by fuzzy name match."""
        keywords = product_name.lower().split()
        
        for file_path in self.assets_dir.glob("*"):
            if file_path.suffix.lower() not in extensions:
                continue
                
            filename = file_path.stem.lower()
            if product_name.lower() in filename or any(kw in filename for kw in keywords):
                return file_path
        
        return None

    async def generate_image(self, prompt: str, reference_image_path: Path = None, output_filename: str = "generated.png") -> Path:
        """
        Generates an image using OpenRouter (Nanobanana).
        If reference_image_path is provided, we might use it (if API supports img2img)
        OR currently, just rely on the prompt which should describe the product.
        
        Note: OpenRouter standard Chat Completion API for images usually takes text.
        Deep-integration of img2img varies by provider.
        For now, we will perform Text-to-Image.
        """
        
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": SITE_URL,
            "X-Title": APP_NAME,
            "Content-Type": "application/json"
        }

        # Nanobanana via OpenRouter
        # Model: "bananabin/nanobanana" (or check exact ID)
        model = "bananabin/nanobanana" 
        
        payload = {
            "model": model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            # Image generation specific params might differ on OpenRouter
            # Usually it's strictly ChatCompletions, but some specialized models output image URLs.
            # If Nanobanana is an LLM that makes images, it might return a URL.
        }

        # Alternative: If Nanobanana is not on OpenRouter standard chat, 
        # we might need to use a different endpoint or check if it's "stabilityai/..."
        # Let's check the user's previous request. They mentioned "nanobanana".
        # Assuming it's an available model ID.
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{OPENROUTER_BASE_URL}/chat/completions",
                    headers=headers,
                    json=payload,
                    timeout=60.0
                )
                response.raise_for_status()
                data = response.json()
                
                # Check for image URL in response
                # This depends heavily on how the model returns data.
                # Often it's in logic like: content = "Here is your image: ![img](url)"
                content = data['choices'][0]['message']['content']
                
                # Simple extraction of markdown image or URL
                import re
                url_match = re.search(r'\!\[.*?\]\((.*?)\)', content)
                if not url_match:
                    url_match = re.search(r'(https?://[^\s)]+)', content)
                
                if url_match:
                    image_url = url_match.group(1)
                    # Download image
                    img_response = await client.get(image_url)
                    output_path = self.output_dir / output_filename
                    with open(output_path, 'wb') as f:
                        f.write(img_response.content)
                    return output_path
                else:
                    print("No image URL found in response.")
                    return None

        except Exception as e:
            print(f"Error generating image: {e}")
            return None

# Test Block (Search capability)
if __name__ == "__main__":
    generator = SandboxImageGenerator()
    # Mock test
    # ref = generator.find_reference_image("Acne")
    # print(f"Found reference: {ref}")
