
import sys
import os
import httpx
from dotenv import load_dotenv

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config.settings import settings

load_dotenv()

class SandboxFacebookPoster:
    def __init__(self):
        self.page_access_token = settings.facebook_page_access_token
        self.page_id = settings.facebook_page_id
        self.api_version = settings.facebook_api_version
        self.base_url = f"https://graph.facebook.com/{self.api_version}"

    async def create_draft_post(self, message: str, link: str = None, image_path: str = None):
        """
        Creates a DRAFT post on the Facebook Page.
        If image_path is provided, uses /photos endpoint.
        Else uses /feed endpoint.
        """
        if not self.page_access_token or not self.page_id:
            print("Error: Facebook credentials missing.")
            return None

        async with httpx.AsyncClient() as client:
            try:
                # Option 1: Photo Post (if image exists)
                if image_path and os.path.exists(image_path):
                    url = f"{self.base_url}/{self.page_id}/photos"
                    
                    data = {
                        "access_token": self.page_access_token,
                        "message": message,
                        "published": "false",  # DRAFT MODE
                        # "unpublished_content_type": "DRAFT", # Standard Draft
                    }
                    
                    # Read image
                    files = {'source': open(image_path, 'rb')}
                    
                    print(f"Uploading draft photo to {url}...")
                    response = await client.post(url, data=data, files=files, timeout=60.0)
                
                # Option 2: Link/Text Post
                else:
                    url = f"{self.base_url}/{self.page_id}/feed"
                    data = {
                        "access_token": self.page_access_token,
                        "message": message,
                        "link": link,
                        "published": "false", # DRAFT MODE
                    }
                    print(f"Uploading draft text/link to {url}...")
                    response = await client.post(url, data=data, timeout=30.0)

                response.raise_for_status()
                result = response.json()
                
                post_id = result.get("id") or result.get("post_id")
                print(f"Draft created successfully! ID: {post_id}")
                return post_id

            except httpx.HTTPStatusError as e:
                print(f"HTTP Error: {e.response.text}")
            except Exception as e:
                print(f"Error creating draft: {e}")
            return None

# Test Block
if __name__ == "__main__":
    import asyncio
    poster = SandboxFacebookPoster()
    asyncio.run(poster.create_draft_post("Test Draft Message", link="https://google.com"))
