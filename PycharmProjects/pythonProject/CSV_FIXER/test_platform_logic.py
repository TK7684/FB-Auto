import unittest
import os
import csv
import sys
from typing import List

# Setup path
sys.path.insert(0, os.getcwd())

from csv_fixer_core.fixers import (
    fix_header_only, 
    process_csv_file, 
    process_csv_pandas,
    TIKTOK_HEADERS,
    SHOPEE_HEADERS
)

class TestPlatformIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = "test_files"
        os.makedirs(self.test_dir, exist_ok=True)
        self.input_file = os.path.join(self.test_dir, "input.csv")
        self.output_file = os.path.join(self.test_dir, "output.csv")

    def tearDown(self):
        if os.path.exists(self.test_dir):
            for f in os.listdir(self.test_dir):
                os.remove(os.path.join(self.test_dir, f))
            os.rmdir(self.test_dir)

    def create_mock_csv(self, headers: List[str], rows: List[List[str]], encoding='utf-8', sep=','):
        with open(self.input_file, 'w', encoding=encoding, newline='') as f:
            writer = csv.writer(f, delimiter=sep)
            writer.writerow(headers)
            writer.writerows(rows)

    def test_fast_fix_tiktok_streaming(self):
        # 55 columns for TikTok
        mock_headers = ["Old Col " + str(i) for i in range(55)]
        mock_rows = [["Data " + str(i) for i in range(55)] for _ in range(5)]
        self.create_mock_csv(mock_headers, mock_rows)
        
        fixes, count = fix_header_only(self.input_file, self.output_file, "tiktok", repair_rows=False)
        
        with open(self.output_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            # Normalize TIKTOK_HEADERS for comparison (remove spaces after commas)
            expected_headers = [h.strip() for h in TIKTOK_HEADERS.split(',')]
            self.assertEqual(headers, expected_headers)
            self.assertEqual(count, -1) # Streaming mode returns -1

    def test_fast_fix_tiktok_repair(self):
        # Create broken rows (too few and too many columns)
        mock_headers = ["h1", "h2"]
        mock_rows = [
            ["v1"], # Too few
            ["v1", "v2", "v3"] # Too many
        ]
        self.create_mock_csv(mock_headers, mock_rows)
        
        # TikTok expects 55
        fixes, count = fix_header_only(self.input_file, self.output_file, "tiktok", repair_rows=True)
        
        with open(self.output_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            self.assertEqual(len(headers), 55)
            row1 = next(reader)
            self.assertEqual(len(row1), 55)
            self.assertEqual(row1[0], "v1")
            self.assertEqual(row1[1], "")
            row2 = next(reader)
            self.assertEqual(len(row2), 55)
            self.assertEqual(row2[2], "v3") # v3 should be preserved if expected_cols > 3
            self.assertEqual(count, 2)

    def test_pandas_shopee_integration(self):
        # Shopee expects 59
        mock_headers = ["Thai Header " + str(i) for i in range(59)]
        mock_rows = [["00123", "Other Data"] + [""] * 57]
        self.create_mock_csv(mock_headers, mock_rows)
        
        options = {"column_names": True, "timestamps": False}
        fixes, count = process_csv_pandas(self.input_file, self.output_file, options, platform="shopee")
        
        # Verify result with pandas (strict)
        import pandas as pd
        df = pd.read_csv(self.output_file, dtype=str)
        self.assertEqual(list(df.columns), SHOPEE_HEADERS.split(", ")) # Note the spacer in constant
        self.assertEqual(df.iloc[0, 0], "00123") # Preservation of leading zeros
        self.assertIn("Applied shopee header template", fixes)

    def test_shopee_thai_to_english_standard(self):
        # Test standard processing with platform override
        mock_headers = ["หมายเลขคำสั่งซื้อ", "สถานะการสั่งซื้อ"] + ["Extra"] * 57
        mock_rows = [["ID123", "Success"] + ["Data"] * 57]
        self.create_mock_csv(mock_headers, mock_rows)
        
        options = {"column_names": True, "timestamps": False}
        fixes, count = process_csv_file(self.input_file, self.output_file, options, platform="shopee")
        
        with open(self.output_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            self.assertEqual(headers[0], "order_id")
            self.assertEqual(headers[1], "order_status")

if __name__ == '__main__':
    unittest.main()
