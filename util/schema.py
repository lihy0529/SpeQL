# Copyright (c) 2025 Haoyu Li
# Released under the MIT License.
# See LICENSE file in the project root for details.

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Schema management module for database schema extraction and caching.
"""

import sys
from pathlib import Path
from typing import Dict
from threading import Lock

# -----------------------------------------------------------------------------
# Path Configuration
# -----------------------------------------------------------------------------

root_dir = str(Path(__file__).parent.parent)
sys.path.extend([
    root_dir,
    str(Path(root_dir) / "src"),
    str(Path(root_dir) / "util"),
])

# -----------------------------------------------------------------------------
# Local Imports
# -----------------------------------------------------------------------------

from db_api import get_cursor
from log import log, append_test_info
from concurrency import get_execute_cursor_lock
from param import get_test_param

# -----------------------------------------------------------------------------
# Global State
# -----------------------------------------------------------------------------


# schema = {'CALL_CENTER': {'CC_CALL_CENTER_SK': 'integer', 'CC_CALL_CENTER_ID': 'character(16)', 'CC_REC_START_DATE': 'date', 'CC_REC_END_DATE': 'date', 'CC_CLOSED_DATE_SK': 'integer', 'CC_OPEN_DATE_SK': 'integer', 'CC_NAME': 'character varying(50)', 'CC_CLASS': 'character varying(50)', 'CC_EMPLOYEES': 'integer', 'CC_SQ_FT': 'integer', 'CC_HOURS': 'character(20)', 'CC_MANAGER': 'character varying(40)', 'CC_MKT_ID': 'integer', 'CC_MKT_CLASS': 'character(50)', 'CC_MKT_DESC': 'character varying(100)', 'CC_MARKET_MANAGER': 'character varying(40)', 'CC_DIVISION': 'integer', 'CC_DIVISION_NAME': 'character varying(50)', 'CC_COMPANY': 'integer', 'CC_COMPANY_NAME': 'character(50)', 'CC_STREET_NUMBER': 'character(10)', 'CC_STREET_NAME': 'character varying(60)', 'CC_STREET_TYPE': 'character(15)', 'CC_SUITE_NUMBER': 'character(10)', 'CC_CITY': 'character varying(60)', 'CC_COUNTY': 'character varying(30)', 'CC_STATE': 'character(2)', 'CC_ZIP': 'character(10)', 'CC_COUNTRY': 'character varying(20)', 'CC_GMT_OFFSET': 'numeric(5,2)', 'CC_TAX_PERCENTAGE': 'numeric(5,2)'}, 'CATALOG_PAGE': {'CP_CATALOG_PAGE_SK': 'integer', 'CP_CATALOG_PAGE_ID': 'character(16)', 'CP_START_DATE_SK': 'integer', 'CP_END_DATE_SK': 'integer', 'CP_DEPARTMENT': 'character varying(50)', 'CP_CATALOG_NUMBER': 'integer', 'CP_CATALOG_PAGE_NUMBER': 'integer', 'CP_DESCRIPTION': 'character varying(100)', 'CP_TYPE': 'character varying(100)'}, 'CATALOG_RETURNS': {'CR_RETURNED_DATE_SK': 'integer', 'CR_RETURNED_TIME_SK': 'integer', 'CR_ITEM_SK': 'integer', 'CR_REFUNDED_CUSTOMER_SK': 'integer', 'CR_REFUNDED_CDEMO_SK': 'integer', 'CR_REFUNDED_HDEMO_SK': 'integer', 'CR_REFUNDED_ADDR_SK': 'integer', 'CR_RETURNING_CUSTOMER_SK': 'integer', 'CR_RETURNING_CDEMO_SK': 'integer', 'CR_RETURNING_HDEMO_SK': 'integer', 'CR_RETURNING_ADDR_SK': 'integer', 'CR_CALL_CENTER_SK': 'integer', 'CR_CATALOG_PAGE_SK': 'integer', 'CR_SHIP_MODE_SK': 'integer', 'CR_WAREHOUSE_SK': 'integer', 'CR_REASON_SK': 'integer', 'CR_ORDER_NUMBER': 'bigint', 'CR_RETURN_QUANTITY': 'integer', 'CR_RETURN_AMOUNT': 'numeric(7,2)', 'CR_RETURN_TAX': 'numeric(7,2)', 'CR_RETURN_AMT_INC_TAX': 'numeric(7,2)', 'CR_FEE': 'numeric(7,2)', 'CR_RETURN_SHIP_COST': 'numeric(7,2)', 'CR_REFUNDED_CASH': 'numeric(7,2)', 'CR_REVERSED_CHARGE': 'numeric(7,2)', 'CR_STORE_CREDIT': 'numeric(7,2)', 'CR_NET_LOSS': 'numeric(7,2)'}, 'CATALOG_SALES': {'CS_SOLD_DATE_SK': 'integer', 'CS_SOLD_TIME_SK': 'integer', 'CS_SHIP_DATE_SK': 'integer', 'CS_BILL_CUSTOMER_SK': 'integer', 'CS_BILL_CDEMO_SK': 'integer', 'CS_BILL_HDEMO_SK': 'integer', 'CS_BILL_ADDR_SK': 'integer', 'CS_SHIP_CUSTOMER_SK': 'integer', 'CS_SHIP_CDEMO_SK': 'integer', 'CS_SHIP_HDEMO_SK': 'integer', 'CS_SHIP_ADDR_SK': 'integer', 'CS_CALL_CENTER_SK': 'integer', 'CS_CATALOG_PAGE_SK': 'integer', 'CS_SHIP_MODE_SK': 'integer', 'CS_WAREHOUSE_SK': 'integer', 'CS_ITEM_SK': 'integer', 'CS_PROMO_SK': 'integer', 'CS_ORDER_NUMBER': 'bigint', 'CS_QUANTITY': 'integer', 'CS_WHOLESALE_COST': 'numeric(7,2)', 'CS_LIST_PRICE': 'numeric(7,2)', 'CS_SALES_PRICE': 'numeric(7,2)', 'CS_EXT_DISCOUNT_AMT': 'numeric(7,2)', 'CS_EXT_SALES_PRICE': 'numeric(7,2)', 'CS_EXT_WHOLESALE_COST': 'numeric(7,2)', 'CS_EXT_LIST_PRICE': 'numeric(7,2)', 'CS_EXT_TAX': 'numeric(7,2)', 'CS_COUPON_AMT': 'numeric(7,2)', 'CS_EXT_SHIP_COST': 'numeric(7,2)', 'CS_NET_PAID': 'numeric(7,2)', 'CS_NET_PAID_INC_TAX': 'numeric(7,2)', 'CS_NET_PAID_INC_SHIP': 'numeric(7,2)', 'CS_NET_PAID_INC_SHIP_TAX': 'numeric(7,2)', 'CS_NET_PROFIT': 'numeric(7,2)'}, 'CUSTOMER': {'C_CUSTOMER_SK': 'integer', 'C_CUSTOMER_ID': 'character(16)', 'C_CURRENT_CDEMO_SK': 'integer', 'C_CURRENT_HDEMO_SK': 'integer', 'C_CURRENT_ADDR_SK': 'integer', 'C_FIRST_SHIPTO_DATE_SK': 'integer', 'C_FIRST_SALES_DATE_SK': 'integer', 'C_SALUTATION': 'character(10)', 'C_FIRST_NAME': 'character(20)', 'C_LAST_NAME': 'character(30)', 'C_PREFERRED_CUST_FLAG': 'character(1)', 'C_BIRTH_DAY': 'integer', 'C_BIRTH_MONTH': 'integer', 'C_BIRTH_YEAR': 'integer', 'C_BIRTH_COUNTRY': 'character varying(20)', 'C_LOGIN': 'character(13)', 'C_EMAIL_ADDRESS': 'character(50)', 'C_LAST_REVIEW_DATE_SK': 'integer'}, 'CUSTOMER_ADDRESS': {'CA_ADDRESS_SK': 'integer', 'CA_ADDRESS_ID': 'character(16)', 'CA_STREET_NUMBER': 'character(10)', 'CA_STREET_NAME': 'character varying(60)', 'CA_STREET_TYPE': 'character(15)', 'CA_SUITE_NUMBER': 'character(10)', 'CA_CITY': 'character varying(60)', 'CA_COUNTY': 'character varying(30)', 'CA_STATE': 'character(2)', 'CA_ZIP': 'character(10)', 'CA_COUNTRY': 'character varying(20)', 'CA_GMT_OFFSET': 'numeric(5,2)', 'CA_LOCATION_TYPE': 'character(20)'}, 'CUSTOMER_DEMOGRAPHICS': {'CD_DEMO_SK': 'integer', 'CD_GENDER': 'character(1)', 'CD_MARITAL_STATUS': 'character(1)', 'CD_EDUCATION_STATUS': 'character(20)', 'CD_PURCHASE_ESTIMATE': 'integer', 'CD_CREDIT_RATING': 'character(10)', 'CD_DEP_COUNT': 'integer', 'CD_DEP_EMPLOYED_COUNT': 'integer', 'CD_DEP_COLLEGE_COUNT': 'integer'}, 'DATE_DIM': {'D_DATE_SK': 'integer', 'D_DATE_ID': 'character(16)', 'D_DATE': 'date', 'D_MONTH_SEQ': 'integer', 'D_WEEK_SEQ': 'integer', 'D_QUARTER_SEQ': 'integer', 'D_YEAR': 'integer', 'D_DOW': 'integer', 'D_MOY': 'integer', 'D_DOM': 'integer', 'D_QOY': 'integer', 'D_FY_YEAR': 'integer', 'D_FY_QUARTER_SEQ': 'integer', 'D_FY_WEEK_SEQ': 'integer', 'D_DAY_NAME': 'character(9)', 'D_QUARTER_NAME': 'character(6)', 'D_HOLIDAY': 'character(1)', 'D_WEEKEND': 'character(1)', 'D_FOLLOWING_HOLIDAY': 'character(1)', 'D_FIRST_DOM': 'integer', 'D_LAST_DOM': 'integer', 'D_SAME_DAY_LY': 'integer', 'D_SAME_DAY_LQ': 'integer', 'D_CURRENT_DAY': 'character(1)', 'D_CURRENT_WEEK': 'character(1)', 'D_CURRENT_MONTH': 'character(1)', 'D_CURRENT_QUARTER': 'character(1)', 'D_CURRENT_YEAR': 'character(1)'}, 'DBGEN_VERSION': {'DV_VERSION': 'character varying(32)', 'DV_CREATE_DATE': 'date', 'DV_CREATE_TIME': 'timestamp without time zone', 'DV_CMDLINE_ARGS': 'character varying(200)'}, 'HOUSEHOLD_DEMOGRAPHICS': {'HD_DEMO_SK': 'integer', 'HD_INCOME_BAND_SK': 'integer', 'HD_BUY_POTENTIAL': 'character(15)', 'HD_DEP_COUNT': 'integer', 'HD_VEHICLE_COUNT': 'integer'}, 'INCOME_BAND': {'IB_INCOME_BAND_SK': 'integer', 'IB_LOWER_BOUND': 'integer', 'IB_UPPER_BOUND': 'integer'}, 'INVENTORY': {'INV_DATE_SK': 'integer', 'INV_ITEM_SK': 'integer', 'INV_WAREHOUSE_SK': 'integer', 'INV_QUANTITY_ON_HAND': 'integer'}, 'ITEM': {'I_ITEM_SK': 'integer', 'I_ITEM_ID': 'character(16)', 'I_REC_START_DATE': 'date', 'I_REC_END_DATE': 'date', 'I_ITEM_DESC': 'character varying(200)', 'I_CURRENT_PRICE': 'numeric(7,2)', 'I_WHOLESALE_COST': 'numeric(7,2)', 'I_BRAND_ID': 'integer', 'I_BRAND': 'character(50)', 'I_CLASS_ID': 'integer', 'I_CLASS': 'character(50)', 'I_CATEGORY_ID': 'integer', 'I_CATEGORY': 'character(50)', 'I_MANUFACT_ID': 'integer', 'I_MANUFACT': 'character(50)', 'I_SIZE': 'character(20)', 'I_FORMULATION': 'character(20)', 'I_COLOR': 'character(20)', 'I_UNITS': 'character(10)', 'I_CONTAINER': 'character(10)', 'I_MANAGER_ID': 'integer', 'I_PRODUCT_NAME': 'character(50)'}, 'PROMOTION': {'P_PROMO_SK': 'integer', 'P_PROMO_ID': 'character(16)', 'P_START_DATE_SK': 'integer', 'P_END_DATE_SK': 'integer', 'P_ITEM_SK': 'integer', 'P_COST': 'numeric(15,2)', 'P_RESPONSE_TARGET': 'integer', 'P_PROMO_NAME': 'character(50)', 'P_CHANNEL_DMAIL': 'character(1)', 'P_CHANNEL_EMAIL': 'character(1)', 'P_CHANNEL_CATALOG': 'character(1)', 'P_CHANNEL_TV': 'character(1)', 'P_CHANNEL_RADIO': 'character(1)', 'P_CHANNEL_PRESS': 'character(1)', 'P_CHANNEL_EVENT': 'character(1)', 'P_CHANNEL_DEMO': 'character(1)', 'P_CHANNEL_DETAILS': 'character varying(100)', 'P_PURPOSE': 'character(15)', 'P_DISCOUNT_ACTIVE': 'character(1)'}, 'REASON': {'R_REASON_SK': 'integer', 'R_REASON_ID': 'character(16)', 'R_REASON_DESC': 'character(100)'}, 'SHIP_MODE': {'SM_SHIP_MODE_SK': 'integer', 'SM_SHIP_MODE_ID': 'character(16)', 'SM_TYPE': 'character(30)', 'SM_CODE': 'character(10)', 'SM_CARRIER': 'character(20)', 'SM_CONTRACT': 'character(20)'}, 'STORE': {'S_STORE_SK': 'integer', 'S_STORE_ID': 'character(16)', 'S_REC_START_DATE': 'date', 'S_REC_END_DATE': 'date', 'S_CLOSED_DATE_SK': 'integer', 'S_STORE_NAME': 'character varying(50)', 'S_NUMBER_EMPLOYEES': 'integer', 'S_FLOOR_SPACE': 'integer', 'S_HOURS': 'character(20)', 'S_MANAGER': 'character varying(40)', 'S_MARKET_ID': 'integer', 'S_GEOGRAPHY_CLASS': 'character varying(100)', 'S_MARKET_DESC': 'character varying(100)', 'S_MARKET_MANAGER': 'character varying(40)', 'S_DIVISION_ID': 'integer', 'S_DIVISION_NAME': 'character varying(50)', 'S_COMPANY_ID': 'integer', 'S_COMPANY_NAME': 'character varying(50)', 'S_STREET_NUMBER': 'character varying(10)', 'S_STREET_NAME': 'character varying(60)', 'S_STREET_TYPE': 'character(15)', 'S_SUITE_NUMBER': 'character(10)', 'S_CITY': 'character varying(60)', 'S_COUNTY': 'character varying(30)', 'S_STATE': 'character(2)', 'S_ZIP': 'character(10)', 'S_COUNTRY': 'character varying(20)', 'S_GMT_OFFSET': 'numeric(5,2)', 'S_TAX_PRECENTAGE': 'numeric(5,2)'}, 'STORE_RETURNS': {'SR_RETURNED_DATE_SK': 'integer', 'SR_RETURN_TIME_SK': 'integer', 'SR_ITEM_SK': 'integer', 'SR_CUSTOMER_SK': 'integer', 'SR_CDEMO_SK': 'integer', 'SR_HDEMO_SK': 'integer', 'SR_ADDR_SK': 'integer', 'SR_STORE_SK': 'integer', 'SR_REASON_SK': 'integer', 'SR_TICKET_NUMBER': 'bigint', 'SR_RETURN_QUANTITY': 'integer', 'SR_RETURN_AMT': 'numeric(7,2)', 'SR_RETURN_TAX': 'numeric(7,2)', 'SR_RETURN_AMT_INC_TAX': 'numeric(7,2)', 'SR_FEE': 'numeric(7,2)', 'SR_RETURN_SHIP_COST': 'numeric(7,2)', 'SR_REFUNDED_CASH': 'numeric(7,2)', 'SR_REVERSED_CHARGE': 'numeric(7,2)', 'SR_STORE_CREDIT': 'numeric(7,2)', 'SR_NET_LOSS': 'numeric(7,2)'}, 'STORE_SALES': {'SS_SOLD_DATE_SK': 'integer', 'SS_SOLD_TIME_SK': 'integer', 'SS_ITEM_SK': 'integer', 'SS_CUSTOMER_SK': 'integer', 'SS_CDEMO_SK': 'integer', 'SS_HDEMO_SK': 'integer', 'SS_ADDR_SK': 'integer', 'SS_STORE_SK': 'integer', 'SS_PROMO_SK': 'integer', 'SS_TICKET_NUMBER': 'bigint', 'SS_QUANTITY': 'integer', 'SS_WHOLESALE_COST': 'numeric(7,2)', 'SS_LIST_PRICE': 'numeric(7,2)', 'SS_SALES_PRICE': 'numeric(7,2)', 'SS_EXT_DISCOUNT_AMT': 'numeric(7,2)', 'SS_EXT_SALES_PRICE': 'numeric(7,2)', 'SS_EXT_WHOLESALE_COST': 'numeric(7,2)', 'SS_EXT_LIST_PRICE': 'numeric(7,2)', 'SS_EXT_TAX': 'numeric(7,2)', 'SS_COUPON_AMT': 'numeric(7,2)', 'SS_NET_PAID': 'numeric(7,2)', 'SS_NET_PAID_INC_TAX': 'numeric(7,2)', 'SS_NET_PROFIT': 'numeric(7,2)'}, 'TIME_DIM': {'T_TIME_SK': 'integer', 'T_TIME_ID': 'character(16)', 'T_TIME': 'integer', 'T_HOUR': 'integer', 'T_MINUTE': 'integer', 'T_SECOND': 'integer', 'T_AM_PM': 'character(2)', 'T_SHIFT': 'character(20)', 'T_SUB_SHIFT': 'character(20)', 'T_MEAL_TIME': 'character(20)'}, 'WAREHOUSE': {'W_WAREHOUSE_SK': 'integer', 'W_WAREHOUSE_ID': 'character(16)', 'W_WAREHOUSE_NAME': 'character varying(20)', 'W_WAREHOUSE_SQ_FT': 'integer', 'W_STREET_NUMBER': 'character(10)', 'W_STREET_NAME': 'character varying(60)', 'W_STREET_TYPE': 'character(15)', 'W_SUITE_NUMBER': 'character(10)', 'W_CITY': 'character varying(60)', 'W_COUNTY': 'character varying(30)', 'W_STATE': 'character(2)', 'W_ZIP': 'character(10)', 'W_COUNTRY': 'character varying(20)', 'W_GMT_OFFSET': 'numeric(5,2)'}, 'WEB_PAGE': {'WP_WEB_PAGE_SK': 'integer', 'WP_WEB_PAGE_ID': 'character(16)', 'WP_REC_START_DATE': 'date', 'WP_REC_END_DATE': 'date', 'WP_CREATION_DATE_SK': 'integer', 'WP_ACCESS_DATE_SK': 'integer', 'WP_AUTOGEN_FLAG': 'character(1)', 'WP_CUSTOMER_SK': 'integer', 'WP_URL': 'character varying(100)', 'WP_TYPE': 'character(50)', 'WP_CHAR_COUNT': 'integer', 'WP_LINK_COUNT': 'integer', 'WP_IMAGE_COUNT': 'integer', 'WP_MAX_AD_COUNT': 'integer'}, 'WEB_RETURNS': {'WR_RETURNED_DATE_SK': 'integer', 'WR_RETURNED_TIME_SK': 'integer', 'WR_ITEM_SK': 'integer', 'WR_REFUNDED_CUSTOMER_SK': 'integer', 'WR_REFUNDED_CDEMO_SK': 'integer', 'WR_REFUNDED_HDEMO_SK': 'integer', 'WR_REFUNDED_ADDR_SK': 'integer', 'WR_RETURNING_CUSTOMER_SK': 'integer', 'WR_RETURNING_CDEMO_SK': 'integer', 'WR_RETURNING_HDEMO_SK': 'integer', 'WR_RETURNING_ADDR_SK': 'integer', 'WR_WEB_PAGE_SK': 'integer', 'WR_REASON_SK': 'integer', 'WR_ORDER_NUMBER': 'bigint', 'WR_RETURN_QUANTITY': 'integer', 'WR_RETURN_AMT': 'numeric(7,2)', 'WR_RETURN_TAX': 'numeric(7,2)', 'WR_RETURN_AMT_INC_TAX': 'numeric(7,2)', 'WR_FEE': 'numeric(7,2)', 'WR_RETURN_SHIP_COST': 'numeric(7,2)', 'WR_REFUNDED_CASH': 'numeric(7,2)', 'WR_REVERSED_CHARGE': 'numeric(7,2)', 'WR_ACCOUNT_CREDIT': 'numeric(7,2)', 'WR_NET_LOSS': 'numeric(7,2)'}, 'WEB_SALES': {'WS_SOLD_DATE_SK': 'integer', 'WS_SOLD_TIME_SK': 'integer', 'WS_SHIP_DATE_SK': 'integer', 'WS_ITEM_SK': 'integer', 'WS_BILL_CUSTOMER_SK': 'integer', 'WS_BILL_CDEMO_SK': 'integer', 'WS_BILL_HDEMO_SK': 'integer', 'WS_BILL_ADDR_SK': 'integer', 'WS_SHIP_CUSTOMER_SK': 'integer', 'WS_SHIP_CDEMO_SK': 'integer', 'WS_SHIP_HDEMO_SK': 'integer', 'WS_SHIP_ADDR_SK': 'integer', 'WS_WEB_PAGE_SK': 'integer', 'WS_WEB_SITE_SK': 'integer', 'WS_SHIP_MODE_SK': 'integer', 'WS_WAREHOUSE_SK': 'integer', 'WS_PROMO_SK': 'integer', 'WS_ORDER_NUMBER': 'bigint', 'WS_QUANTITY': 'integer', 'WS_WHOLESALE_COST': 'numeric(7,2)', 'WS_LIST_PRICE': 'numeric(7,2)', 'WS_SALES_PRICE': 'numeric(7,2)', 'WS_EXT_DISCOUNT_AMT': 'numeric(7,2)', 'WS_EXT_SALES_PRICE': 'numeric(7,2)', 'WS_EXT_WHOLESALE_COST': 'numeric(7,2)', 'WS_EXT_LIST_PRICE': 'numeric(7,2)', 'WS_EXT_TAX': 'numeric(7,2)', 'WS_COUPON_AMT': 'numeric(7,2)', 'WS_EXT_SHIP_COST': 'numeric(7,2)', 'WS_NET_PAID': 'numeric(7,2)', 'WS_NET_PAID_INC_TAX': 'numeric(7,2)', 'WS_NET_PAID_INC_SHIP': 'numeric(7,2)', 'WS_NET_PAID_INC_SHIP_TAX': 'numeric(7,2)', 'WS_NET_PROFIT': 'numeric(7,2)'}, 'WEB_SITE': {'WEB_SITE_SK': 'integer', 'WEB_SITE_ID': 'character(16)', 'WEB_REC_START_DATE': 'date', 'WEB_REC_END_DATE': 'date', 'WEB_NAME': 'character varying(50)', 'WEB_OPEN_DATE_SK': 'integer', 'WEB_CLOSE_DATE_SK': 'integer', 'WEB_CLASS': 'character varying(50)', 'WEB_MANAGER': 'character varying(40)', 'WEB_MKT_ID': 'integer', 'WEB_MKT_CLASS': 'character varying(50)', 'WEB_MKT_DESC': 'character varying(100)', 'WEB_MARKET_MANAGER': 'character varying(40)', 'WEB_COMPANY_ID': 'integer', 'WEB_COMPANY_NAME': 'character(50)', 'WEB_STREET_NUMBER': 'character(10)', 'WEB_STREET_NAME': 'character varying(60)', 'WEB_STREET_TYPE': 'character(15)', 'WEB_SUITE_NUMBER': 'character(10)', 'WEB_CITY': 'character varying(60)', 'WEB_COUNTY': 'character varying(30)', 'WEB_STATE': 'character(2)', 'WEB_ZIP': 'character(10)', 'WEB_COUNTRY': 'character varying(20)', 'WEB_GMT_OFFSET': 'numeric(5,2)', 'WEB_TAX_PERCENTAGE': 'numeric(5,2)'}} 
schema: Dict[str, Dict[str, str]] = {}
useful_schema_dict: Dict[str, Dict[str, Dict[str, str]]] = {}

# -----------------------------------------------------------------------------
# Schema Management
# -----------------------------------------------------------------------------

def get_schema() -> Dict[str, Dict[str, str]]:
    """
    Retrieves and caches database schema information.
    
    Returns:
        Dict[str, Dict[str, str]]: Database schema mapping
            {table_name: {column_name: column_type}}
            
    Warning:
        The table and column names are not quoted.
    """
    global schema
    if not schema:
        try:
            cursor = get_cursor()["execute"]
            
            cursor.execute(
                "SELECT distinct tablename FROM pg_table_def "
                "WHERE schemaname NOT IN ('pg_catalog', 'information_schema')"
            )
            tables = cursor.fetchall()

            for table in tables:
                cursor.execute(
                    f'SELECT "column", "type" FROM pg_table_def '
                    f"WHERE tablename = '{table[0]}'"
                )
                schema[table[0].upper()] = {
                    row[0].upper(): row[1] 
                    for row in cursor.fetchall()
                }
                
            log("schema.txt", str(schema))

        except Exception as e:
            log("error.txt", f"Error: {e}")

    return schema

# -----------------------------------------------------------------------------
# Schema Analysis
# -----------------------------------------------------------------------------

def get_useful_schema(sql: str) -> Dict[str, Dict[str, str]]:
    """
    Extracts relevant schema information for a given SQL query.
    
    Args:
        sql: SQL query to analyze
        
    Returns:
        Dict[str, Dict[str, str]]: Relevant schema information
            {table_name: {column_name: column_type}}
    """
    # Return cached result if available
    if sql in useful_schema_dict:
        return useful_schema_dict[sql]

    # Extract words from SQL query
    word_set = {word for word in sql.split()}
    useful_schema = {}

    # Find relevant schema information
    for outer_word in word_set:
        if outer_word.upper() in get_schema():
            useful_schema[outer_word] = {}
            for inner_word in word_set:
                if inner_word.upper() in get_schema()[outer_word.upper()]:
                    useful_schema[outer_word][inner_word] = get_schema()[outer_word.upper()][inner_word.upper()]
            
            for column_name, column_type in get_schema()[outer_word.upper()].items():
                if column_name.upper() not in [item.upper() for item in useful_schema[outer_word].keys()]:
                    useful_schema[outer_word][column_name] = column_type
    
    useful_schema_dict[sql] = useful_schema

    # Log for testing if enabled
    if get_test_param()["output_useful_schema"]:
        append_test_info("useful_schema", useful_schema)

    return useful_schema

# -----------------------------------------------------------------------------
# Initialization
# -----------------------------------------------------------------------------

# Initialize schema with thread safety
lock: Lock = get_execute_cursor_lock()
with lock:
    schema = get_schema()
