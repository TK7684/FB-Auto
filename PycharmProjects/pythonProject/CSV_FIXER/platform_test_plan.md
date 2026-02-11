# Test Plan: Platform Integration

## 1. Fast Header Fix Tests
- **TikTok Streaming:** Verify header replacement without reading rows.
- **TikTok Repair:** Verify header replacement and column count padding/truncation for broken rows.
- **Shopee Streaming:** Verify header replacement (Thai -> English).
- **Shopee Repair:** Verify row repair for Shopee data.

## 2. General Fix Platform Integration
- **TikTok + Timestamps:** Verify headers are replaced AND timestamps are converted in one pass.
- **Shopee + Column Sanitization:** Verify headers are replaced AND standard sanitization is applied.

## 3. Performance & Integrity
- **Encoding:** Ensure UTF-8 with BOM and other common encodings are handled.
- **Data Preservation:** Verify leading zeros (order IDs) and special characters (product names) are preserved.
