from services.google_sheet_service import get_google_sheet_service
from loguru import logger
import sys

# Configure logger
logger.remove()
logger.add(sys.stdout, level="INFO")

def test_sheet_connection():
    print("Testing Google Sheets Connection...")
    try:
        service = get_google_sheet_service()
        if service.connected:
            print("✅ Connection Successful!")
            print(f"File Path: {service.key_file_path}")
            print(f"Sheet ID: {service.SHEET_ID}")
            
            print("\nAvailable Worksheets (with repr):")
            for ws in service.sheet.worksheets():
                print(f" - {repr(ws.title)}")
            
            inbox_name = "Inbox" # Default guess
            print(f"\nAttempting to access {repr(inbox_name)}...")
            try:
                inbox = service.sheet.worksheet(inbox_name)
                print(f"✅ Success! Headers: {inbox.row_values(1)}")
            except Exception as e:
                print(f"❌ Failed: {e}")
        else:
            print("❌ Connection Failed (Check logs above)")
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_sheet_connection()
