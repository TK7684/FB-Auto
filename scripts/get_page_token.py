"""
Script to fetch Page Access Token from User Access Token.
"""
import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

USER_TOKEN = os.getenv('FACEBOOK_PAGE_ACCESS_TOKEN')  # Currently holds user token
PAGE_ID = os.getenv('FACEBOOK_PAGE_ID')

def get_page_token():
    print(f"Fetching accounts for User Token...")
    url = f"https://graph.facebook.com/v19.0/me/accounts"
    params = {
        "access_token": USER_TOKEN,
        "limit": 100
    }
    
    try:
        r = httpx.get(url, params=params)
        data = r.json()
        
        if "error" in data:
            print(f"❌ Error: {data['error']['message']}")
            return None
            
        accounts = data.get("data", [])
        print(f"Found {len(accounts)} pages.")
        
        for page in accounts:
            print(f"- {page.get('name')} (ID: {page.get('id')})")
            if page.get("id") == PAGE_ID:
                print(f"   ✓ MATCH! Found token for {page.get('name')}")
                return page.get("access_token")
                
        print(f"❌ Page ID {PAGE_ID} not found in user's accounts.")
        return None
        
    except Exception as e:
        print(f"❌ Exception: {e}")
        return None

if __name__ == "__main__":
    page_token = get_page_token()
    if page_token:
        print("\n👇 FOUND PAGE TOKEN 👇")
        print(f"{page_token[:20]}...{page_token[-20:]}")
        
        # Update .env file
        env_path = Path(".env")
        if env_path.exists():
            content = env_path.read_text(encoding="utf-8")
            lines = content.splitlines()
            new_lines = []
            updated = False
            for line in lines:
                if line.startswith("FACEBOOK_PAGE_ACCESS_TOKEN="):
                    new_lines.append(f"FACEBOOK_PAGE_ACCESS_TOKEN={page_token}")
                    updated = True
                else:
                    new_lines.append(line)
            
            if updated:
                env_path.write_text("\n".join(new_lines), encoding="utf-8")
                print("✅ Updated .env file with new Page Access Token!")
            else:
                print("❌ Could not find FACEBOOK_PAGE_ACCESS_TOKEN in .env to update.")
        else:
             print("❌ .env file not found.")
