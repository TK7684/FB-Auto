
import sys
import os
import pandas as pd
from pathlib import Path

# Add current directory to path
sys.path.append(os.getcwd())

from shopee_order_fixer import ShopeeOrderFixer
from csv_fixer_core.fixers import process_csv_pandas

# Define inputs
shopee_input = r"C:\Users\ttapk\Downloads\Shopee-Order.toship.FebOnly12.xlsx"
tiktok_input = r"C:\Users\ttapk\Downloads\TikTok-Feb-only12.csv"
output_dir = r"C:\Users\ttapk\Downloads\processed_output"

os.makedirs(output_dir, exist_ok=True)

def process_shopee():
    print(f"Processing Shopee file: {shopee_input}")
    if not os.path.exists(shopee_input):
        print(f"Error: File not found: {shopee_input}")
        return None

    try:
        # Load excel directly
        print("  - Reading Excel file...")
        df = pd.read_excel(shopee_input)
        print(f"  - Loaded {len(df)} rows")
        
        # Use cleaner from ShopeeOrderFixer
        fixer = ShopeeOrderFixer(output_dir=output_dir)
        print("  - Cleaning data...")
        df_clean = fixer.clean_data(df)
        
        # Save CSV
        output_name = Path(shopee_input).stem + ".clean.csv"
        output_path = os.path.join(output_dir, output_name)
        
        print(f"  - Saving to {output_path}...")
        # Use to_csv directly as fixer.save_csv might force a specific filename
        df_clean.to_csv(
            output_path,
            index=False,
            encoding='utf-8-sig',
            quoting=1  # QUOTE_ALL
        )
        print(f"  - Saved to: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error processing Shopee file: {e}")
        import traceback
        traceback.print_exc()
        return None

def process_tiktok():
    print(f"Processing TikTok file: {tiktok_input}")
    if not os.path.exists(tiktok_input):
        print(f"Error: File not found: {tiktok_input}")
        return None
        
    output_name = Path(tiktok_input).stem + ".clean.csv"
    output_path = os.path.join(output_dir, output_name)
    
    options = {
        "column_names": True,
        "timestamps": True,
        "quotes": True,
        "newlines": True
    }
    
    try:
        print("  - Validating CSV structure and processing...")
        fixes, count = process_csv_pandas(
            input_file=tiktok_input,
            output_file=output_path,
            options=options,
            platform="tiktok"
        )
        print(f"  - Processed {count} rows")
        print(f"  - Fixes applied: {len(fixes)}")
        print(f"  - Saved to: {output_path}")
        return output_path
    except Exception as e:
        print(f"Error processing TikTok file: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    print("Starting processing...")
    shopee_out = process_shopee()
    print("-" * 50)
    tiktok_out = process_tiktok()
    
    print("\n" + "=" * 50)
    print("Summary:")
    if shopee_out:
        print(f"Shopee: {shopee_out}")
    else:
        print("Shopee: FAILED")
        
    if tiktok_out:
        print(f"TikTok: {tiktok_out}")
    else:
        print("TikTok: FAILED")
