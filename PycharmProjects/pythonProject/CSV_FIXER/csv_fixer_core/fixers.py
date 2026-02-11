"""
CSV Fixing Functions

This module contains all the core CSV fixing functions.
"""

import csv
import os
import re
import shutil
import time
from datetime import datetime
from typing import List, Tuple, Dict, Any, Optional

try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

from .constants import TIMESTAMP_FORMATS, BIGQUERY_TIMESTAMP_FORMAT, BIGQUERY_DATE_FORMAT
from .utils import detect_file_encoding, detect_separator
from .logging_utils import get_logger


# Header Constants for Fast Process
TIKTOK_HEADERS = "order_id, order_status, order_substatus, cancel_return_type, order_type, sku_id, seller_sku, product_name, variation, quantity, return_quantity, unit_original_price, subtotal_gross, discount_platform, discount_seller, subtotal_net, shipping_fee_net, shipping_fee_original, shipping_fee_discount_seller, shipping_fee_discount_platform, payment_platform_discount, taxes, small_order_fee, order_total_amount, refund_amount, created_at, paid_at, rts_at, shipped_at, delivered_at, cancelled_at, cancelled_by, cancel_reason, fulfillment_type, warehouse_name, tracking_id, delivery_option, shipping_provider, buyer_message, buyer_username, recipient_name, phone_number, zipcode, country, province, district, address_detail, address_additional, payment_method, weight_kg, category, package_id, seller_note, checked_status, checked_marked_by"

SHOPEE_HEADERS = "order_id, order_status, hot_listing, cancel_reason, return_refund_status, buyer_username, created_at, paid_at, payment_method, payment_method_detail, installment_plan, fee_percentage, delivery_option, shipping_provider, tracking_id, estimated_ship_date, shipped_at, parent_sku_ref, product_name, seller_sku, variation, unit_original_price, unit_deal_price, quantity, return_quantity, subtotal_net, discount_platform, discount_seller, seller_coin_cashback, shopee_voucher_rebate, voucher_code, is_bundle_deal, bundle_discount_seller, bundle_discount_platform, coin_discount, payment_promotion_discount, trade_in_discount, trade_in_bonus, commission_fee, transaction_fee, order_total_amount, shipping_fee_net, shipping_fee_discount_platform, return_shipping_fee, service_fee, total_settlement_amount, estimated_shipping_fee, trade_in_seller_bonus, recipient_name, phone_number, buyer_message, address_detail, country, province, district, zipcode, order_type, completed_at, seller_note"


def fix_header_only(input_file: str, output_file: str, platform: str, repair_rows: bool = False) -> Tuple[List[str], int]:
    """
    Fast-path header replacement for TikTok and Shopee.
    Only replaces the first line and streams the rest.
    If repair_rows is True, it ensures every row matches the header's column count.
    """
    logger = get_logger()
    fixes_applied = [f"Replaced header for {platform}"]
    if repair_rows:
        fixes_applied.append("Repaired row column counts")
    
    start_time = time.time()
    
    if platform.lower() == 'tiktok':
        header_text = TIKTOK_HEADERS
    elif platform.lower() == 'shopee':
        header_text = SHOPEE_HEADERS
    else:
        return [f"Error: Unknown platform {platform}"], 0

    try:
        # Detect encoding
        detected_encoding = detect_file_encoding(input_file)
        
        # Prepare header
        header_list = [h.strip() for h in header_text.split(',')]
        expected_cols = len(header_list)
        
        if not repair_rows:
            # STREAMING MODE (Fastest)
            with open(input_file, 'r', encoding=detected_encoding, errors='replace', newline='') as infile:
                # Read first line to skip (header)
                first_line = infile.readline()
                
                # Detect separator from first line if possible, otherwise use comma
                separator = detect_separator(first_line) if first_line else ','
                
                # Prepare new header with correct separator
                final_header = separator.join(header_list) + '\n'
                
                os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
                with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                    outfile.write(final_header)
                    # Stream the rest of the file
                    shutil.copyfileobj(infile, outfile)
            row_count = -1
        else:
            # REPAIR MODE (Safe for BigQuery)
            row_count = 0
            with open(input_file, 'r', encoding=detected_encoding, errors='replace', newline='') as infile:
                # Detect separator from first few lines
                sample = "".join([infile.readline() for _ in range(5)])
                infile.seek(0)
                separator = detect_separator(sample)
                
                reader = csv.reader(infile, delimiter=separator)
                next(reader) # Skip original header
                
                os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
                with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                    writer = csv.writer(outfile, delimiter=separator, quoting=csv.QUOTE_MINIMAL)
                    writer.writerow(header_list)
                    
                    for row in reader:
                        row_count += 1
                        # Pad or truncate
                        if len(row) < expected_cols:
                            row.extend([''] * (expected_cols - len(row)))
                        elif len(row) > expected_cols:
                            row = row[:expected_cols]
                        writer.writerow(row)
                        
        processing_time = time.time() - start_time
        logger.info(f"Header fix for {platform} completed in {processing_time:.2f}s (repair_rows={repair_rows})")
        return fixes_applied, row_count
        
    except Exception as e:
        logger.error(f"Failed fast header fix: {e}")
        return [f"Error: {e}"], 0


def get_platform_headers(platform: Optional[str]) -> Optional[List[str]]:
    """Get header list for a platform."""
    if not platform:
        return None
    
    if platform.lower() == 'tiktok':
        return [h.strip() for h in TIKTOK_HEADERS.split(',')]
    elif platform.lower() == 'shopee':
        return [h.strip() for h in SHOPEE_HEADERS.split(',')]
    return None


def sanitize_column_name(col_name: str) -> str:
    """
    Sanitize column name for BigQuery compatibility.
    """
    # Remove accents and convert to lowercase
    # This is a basic implementation, can be enhanced with unidecode if available
    sanitized = col_name.strip().lower()
    
    # Replace common special characters with underscore explicitly
    # This handles /, -, space, (, ), ., etc.
    sanitized = re.sub(r'[\/\s\-\(\)\.]+', '_', sanitized)
    
    # Remove any remaining non-word characters (except underscore)
    sanitized = re.sub(r'[^\w]+', '', sanitized)
    # Remove multiple consecutive underscores
    sanitized = re.sub(r'_+', '_', sanitized)
    # Remove leading/trailing underscores
    sanitized = sanitized.strip('_')
    
    # Ensure it starts with a letter or underscore
    if sanitized and sanitized[0].isdigit():
        sanitized = f'col_{sanitized}'
        
    # Handle reserved words
    reserved_words = ["date", "time", "timestamp", "group", "order", "table", "select", "where", "from"]
    if sanitized in reserved_words:
        sanitized = f"{sanitized}_field"
        
    # Ensure it's not empty
    if not sanitized:
        sanitized = "column"
        
    return sanitized


def fix_timestamp_for_bigquery(timestamp_str: str) -> str:
    """
    Convert timestamp from various formats to BigQuery compatible format.
    If timestamp has time component, add UTC suffix.
    """
    if not timestamp_str or timestamp_str.strip() == '':
        return timestamp_str

    timestamp_str = timestamp_str.strip()

    # Try to parse with various formats
    for fmt in TIMESTAMP_FORMATS:
        try:
            dt = datetime.strptime(timestamp_str, fmt)
            # Check if it has time component
            if any(char in fmt for char in ['%H', '%M', '%S']):
                return dt.strftime(BIGQUERY_TIMESTAMP_FORMAT)
            else:
                return dt.strftime(BIGQUERY_DATE_FORMAT)
        except ValueError:
            continue

    # If all parsing attempts fail, return the original string
    return timestamp_str


def fix_encoding_issues(content: str, from_encoding: str = 'utf-8') -> str:
    """
    Fix encoding issues by ensuring proper UTF-8 encoding.
    """
    try:
        # Try to decode with the specified encoding
        decoded = content.encode('latin1').decode(from_encoding)
        # Return as UTF-8
        return decoded
    except (UnicodeDecodeError, UnicodeEncodeError):
        # Fall back to replacing problematic characters
        return content.encode('utf-8', errors='replace').decode('utf-8')


def fix_newline_characters(content: str) -> str:
    """
    Normalize newline characters to \n.
    """
    # Replace Windows newlines (\r\n) and old Mac newlines (\r) with \n
    return re.sub(r'\r\n|\r', '\n', content)


def fix_quote_escaping(content: str) -> str:
    """
    Fix improperly escaped quotes in CSV content.
    """
    # Fix double quotes that should be escaped
    # This is a simplified implementation
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        # Skip empty lines
        if not line.strip():
            fixed_lines.append(line)
            continue

        # Count quotes in the line
        quote_count = line.count('"')

        # If odd number of quotes, there's likely an issue
        if quote_count % 2 != 0:
            # Try to fix by escaping unescaped quotes
            in_field = False
            fixed_line = []

            for char in line:
                if char == '"':
                    if not in_field:
                        fixed_line.append(char)
                        in_field = True
                    else:
                        # Look ahead to see if this is the end of a field
                        next_chars = line[line.index(char) + 1:line.index(char) + 3] if line.index(char) + 3 <= len(line) else ''
                        if next_chars in [',', '\n', ''] or len(next_chars) < 2:
                            fixed_line.append(char)
                            in_field = False
                        else:
                            fixed_line.append('""')
                else:
                    fixed_line.append(char)

            fixed_lines.append(''.join(fixed_line))
        else:
            fixed_lines.append(line)

    return '\n'.join(fixed_lines)


def fix_separator_issues(content: str, separator: str = ',') -> str:
    """
    Fix issues with separator characters in data fields.
    """
    lines = content.split('\n')
    fixed_lines = []

    for line in lines:
        if not line.strip():
            fixed_lines.append(line)
            continue

        # Parse the line with CSV reader to handle quoted fields
        reader = csv.reader([line], delimiter=separator)
        fields = next(reader, [])

        # Write back with proper quoting
        writer = csv.writer(fixed_lines, delimiter=separator, quoting=csv.QUOTE_MINIMAL)
        writer.writerow(fields)

    return '\n'.join(fixed_lines)


def process_csv_file(
    input_file: str,
    output_file: str,
    options: Dict[str, bool],
    separator: Optional[str] = None,
    platform: Optional[str] = None
) -> Tuple[List[str], int]:
    """
    Process a CSV file with the specified options and optional platform header override.

    Args:
        input_file: Path to input CSV file
        output_file: Path to output CSV file
        options: Dictionary of fixing options
        separator: CSV separator (auto-detect if None)

    Returns:
        Tuple of (list of fixes applied, number of rows processed)
    """
    logger = get_logger()
    fixes_applied = []
    start_time = time.time()

    try:
        # Log processing start
        logger.log_processing_start(input_file, options)
        logger.log_file_operation("Reading", input_file)

        # Check if input file exists
        if not os.path.exists(input_file):
            logger.error(f"Input file does not exist: {input_file}")
            return [f"Error: File not found - {input_file}"], 0

        # Detect file encoding first
        try:
            detected_encoding = detect_file_encoding(input_file)
            logger.info(f"Detected file encoding: {detected_encoding}")
        except Exception as e:
            logger.warning(f"Failed to detect encoding: {str(e)}")
            detected_encoding = 'utf-8'

        # Detect separator if not provided
        if separator is None:
            try:
                with open(input_file, 'r', encoding=detected_encoding, newline='') as f:
                    sample = f.read(1024)
                    separator = detect_separator(sample)
                    logger.info(f"Detected separator: '{separator}'")
            except Exception as e:
                logger.error(f"Failed to detect separator: {str(e)}")
                separator = ','
                logger.warning(f"Using default separator: '{separator}'")

        # Read the file with proper encoding
        try:
            with open(input_file, 'r', encoding=detected_encoding, newline='') as infile:
                reader = csv.reader(infile, delimiter=separator)

                # Read headers
                try:
                    headers = next(reader)
                    logger.info(f"Found {len(headers)} columns: {headers}")
                except StopIteration:
                    logger.error("Empty file - no headers found")
                    return ["Empty file"], 0

                # Apply platform header override if requested
                platform_headers = get_platform_headers(platform)
                if platform_headers:
                    logger.info(f"Overriding headers for platform: {platform}")
                    headers = platform_headers
                    fixes_applied.append(f"Applied {platform} header template")

                original_headers = headers.copy()

                # Process headers if requested
                if options.get('column_names', False):
                    logger.debug("Processing column names...")
                    for i, header in enumerate(headers):
                        sanitized = sanitize_column_name(str(header))
                        if sanitized != str(header):
                            logger.debug(f"Column {i+1} renamed: '{header}' -> '{sanitized}'")
                            fixes_applied.append(f"Column {i+1}: '{header}' -> '{sanitized}'")
                            headers[i] = sanitized

                # Process data rows
                processed_rows = []
                row_count = 0
                timestamp_fixes = {}

                for row_num, row in enumerate(reader, start=2):
                    processed_row = []
                    row_count += 1

                    # Log progress every 1000 rows
                    if row_count % 1000 == 0:
                        logger.debug(f"Processed {row_count} rows...")

                    for col_idx, cell in enumerate(row):
                        # Apply timestamp fixes
                        if options.get('timestamps', False) and cell:
                            fixed = fix_timestamp_for_bigquery(str(cell))
                            if fixed != str(cell):
                                if col_idx not in timestamp_fixes:
                                    timestamp_fixes[col_idx] = 0
                                    fixes_applied.append(f"Timestamp fix col {col_idx+1}")
                                timestamp_fixes[col_idx] += 1
                                cell = fixed

                        processed_row.append(cell)

                    # Fix column count if requested
                    if options.get('column_count', False):
                        expected_count = len(headers)
                        current_count = len(processed_row)
                        if current_count < expected_count:
                            # Pad with empty strings
                            processed_row.extend([''] * (expected_count - current_count))
                            if "Row count padded" not in fixes_applied:
                                fixes_applied.append("Row count padded")
                        elif current_count > expected_count:
                            # Truncate to match header
                            processed_row = processed_row[:expected_count]
                            if "Row count truncated" not in fixes_applied:
                                fixes_applied.append("Row count truncated")

                    processed_rows.append(processed_row)

                # Log timestamp fix statistics
                if timestamp_fixes:
                    for col_idx, count in timestamp_fixes.items():
                        logger.info(f"Fixed {count} timestamps in column {col_idx+1}")

                logger.info(f"Total rows processed: {row_count}")

        except UnicodeDecodeError as e:
            logger.error(f"Encoding error: {str(e)}")
            logger.info("Attempting to read with UTF-8 with error replacement...")
            try:
                with open(input_file, 'r', encoding='utf-8', errors='replace', newline='') as infile:
                    reader = csv.reader(infile, delimiter=separator)
                    headers = next(reader)
                    logger.warning(f"File contains encoding issues, using UTF-8 with replacement characters")
                    # Continue processing with error handling...
            except Exception as e2:
                logger.error(f"Failed to read file even with error handling: {str(e2)}")
                return [f"Encoding error: {str(e)}"], 0

        # Write the fixed CSV
        logger.log_file_operation("Writing", output_file)
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

        try:
            with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
                writer = csv.writer(outfile, delimiter=separator)
                writer.writerow(headers)
                writer.writerows(processed_rows)
            logger.info(f"Successfully wrote fixed file: {output_file}")
        except Exception as e:
            logger.error(f"Failed to write output file: {str(e)}")
            return [f"Write error: {str(e)}"], row_count

        # Calculate processing time
        processing_time = time.time() - start_time
        logger.log_processing_end(input_file, output_file, fixes_applied, row_count, processing_time)

        return fixes_applied, row_count

    except Exception as e:
        processing_time = time.time() - start_time
        logger.exception(f"Unexpected error processing file {input_file}: {str(e)}")
        logger.error(f"Processing failed after {processing_time:.2f} seconds")
        return [f"Error: {str(e)}"], 0


def process_creator_order_csv(input_file: str, output_file: str) -> Tuple[List[str], int]:
    """
    Process creator order CSV file specifically for BigQuery compatibility.
    """
    issues_fixed = []

    with open(input_file, 'r', encoding='utf-8') as infile:
        reader = csv.reader(infile)

        # Read and process headers
        headers = next(reader)
        original_headers = headers.copy()

        # Sanitize column names
        for i, header in enumerate(headers):
            sanitized = sanitize_column_name(header)
            if sanitized != header:
                issues_fixed.append(f"Column {i+1}: '{header}' -> '{sanitized}'")
                headers[i] = sanitized

        # Process data rows
        processed_rows = []
        for row_num, row in enumerate(reader, start=2):
            processed_row = row.copy()

            # Check timestamp columns (based on typical creator order structure)
            # These are the columns that typically contain timestamps in DD/MM/YYYY format
            timestamp_columns = [24, 25, 26, 27, 28]  # Indexes of timestamp columns

            for col_idx in timestamp_columns:
                if col_idx < len(processed_row):
                    original = processed_row[col_idx]
                    fixed = fix_timestamp_for_bigquery(original)
                    if fixed != original:
                        issues_fixed.append(f"Row {row_num}, Col {col_idx+1}: Fixed timestamp")
                        processed_row[col_idx] = fixed

            processed_rows.append(processed_row)

    # Write the fixed CSV
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
    with open(output_file, 'w', encoding='utf-8', newline='') as outfile:
        writer = csv.writer(outfile)
        writer.writerow(headers)
        writer.writerows(processed_rows)


    return issues_fixed, len(processed_rows)


def process_csv_pandas(
    input_file: str,
    output_file: str,
    options: Dict[str, bool],
    separator: Optional[str] = None,
    platform: Optional[str] = None
) -> Tuple[List[str], int]:
    """
    Process CSV using Pandas for high performance.
    Strictly preserves data types by forcing dtype=str.
    Supports platform-specific header override.
    """
    if not PANDAS_AVAILABLE:
        return ["Error: Pandas not installed"], 0
        
    logger = get_logger()
    fixes_applied = []
    start_time = time.time()
    
    try:
        logger.log_processing_start(input_file, options)
        logger.info("Using Pandas optimized processing")
        
        # Check if input file exists
        if not os.path.exists(input_file):
            logger.error(f"Input file does not exist: {input_file}")
            return [f"Error: File not found - {input_file}"], 0
            
        # Detect encoding first
        try:
            detected_encoding = detect_file_encoding(input_file)
            logger.info(f"Detected file encoding: {detected_encoding}")
        except Exception as e:
            logger.warning(f"Failed to detect encoding: {str(e)}")
            detected_encoding = 'utf-8'

        # Detect separator if not provided
        if separator is None:
            try:
                with open(input_file, 'r', encoding=detected_encoding, errors='replace') as f:
                    sample = f.read(1024)
                    separator = detect_separator(sample)
                    logger.info(f"Detected separator: '{separator}'")
            except Exception as e:
                logger.error(f"Failed to detect separator: {str(e)}")
                separator = ','
        
        # 1. READ
        # dtype=str and keep_default_na=False are CRITICAL for data integrity
        # strict preservation of "001" as "001" and "null" as "null"
        try:
            df = pd.read_csv(
                input_file, 
                sep=separator, 
                dtype=str, 
                keep_default_na=False,
                encoding=detected_encoding,
                encoding_errors='replace'
            )
        except Exception as e:
             logger.error(f"Pandas read failed: {e}")
             return [f"Pandas Read Error: {e}"], 0
        
        row_count = len(df)
        logger.info(f"Loaded {row_count} rows into DataFrame")
        
        # 1.5 PLATFORM HEADER OVERRIDE
        platform_headers = get_platform_headers(platform)
        if platform_headers:
            if len(platform_headers) == len(df.columns):
                df.columns = platform_headers
                fixes_applied.append(f"Applied {platform} header template")
                logger.info(f"Overridden {len(platform_headers)} columns for {platform}")
            else:
                logger.warning(f"Platform header mismatch: expected {len(platform_headers)}, found {len(df.columns)}")
                # Force replace by padding/truncating if necessary or just fail?
                # For safety in general fix, let's keep it strict or use fix_column_names if needed
                # But if they chose the platform, they probably want these headers.
                # Let's use a safe rename that matches column count.
                new_cols = platform_headers[:len(df.columns)]
                if len(new_cols) < len(df.columns):
                    new_cols += [f"extra_col_{i}" for i in range(len(df.columns) - len(new_cols))]
                df.columns = new_cols
                fixes_applied.append(f"Applied partial {platform} headers")

        # 2. SANITIZE HEADERS
        if options.get('column_names', False):
            original_cols = df.columns.tolist()
            new_cols = [sanitize_column_name(str(c)) for c in original_cols]
            
            # Check if any changed
            changed_count = sum(1 for a, b in zip(original_cols, new_cols) if a != b)
            if changed_count > 0:
                df.columns = new_cols
                fixes_applied.append(f"Sanitized {changed_count} column names")
                logger.info(f"Sanitized {changed_count} column names")

        # 3. FIX TIMESTAMPS
        if options.get('timestamps', False):
            fix_count = 0
            # iterate over columns, check if they look like dates
            for col in df.columns:
                # heuristic: check first non-empty value
                # or just try applying fix_timestamp_for_bigquery to all unique values
                # Vectorized map is faster than apply
                
                # Get unique values to reduce processing
                unique_vals = df[col].unique()
                
                # Create a mapping dictionary for optimization
                val_map = {}
                col_fix_count = 0
                
                for val in unique_vals:
                    if not val: 
                        continue
                    fixed = fix_timestamp_for_bigquery(val)
                    if fixed != val:
                        val_map[val] = fixed
                        col_fix_count += 1
                        
                if val_map:
                    # Apply map
                    df[col] = df[col].replace(val_map)
                    fix_count += col_fix_count
                    fixes_applied.append(f"Fixed timestamps in column '{col}'")
            
            if fix_count > 0:
                logger.info(f"Fixed timestamps across {fix_count} values")

        # 4. WRITE
        logger.log_file_operation("Writing", output_file)
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        
        try:
            df.to_csv(
                output_file, 
                index=False, 
                sep=separator, 
                encoding='utf-8',
                quoting=csv.QUOTE_MINIMAL
            )
            logger.info(f"Successfully wrote fixed file: {output_file}")
        except Exception as e:
            logger.error(f"Failed to write output file: {str(e)}")
            return [f"Write error: {str(e)}"], row_count
        
        processing_time = time.time() - start_time
        logger.log_processing_end(input_file, output_file, fixes_applied, row_count, processing_time)
        return fixes_applied, row_count

    except Exception as e:
        logger.exception(f"Pandas processing failed: {e}")
        return [f"Error: {e}"], 0





