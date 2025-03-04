import sys, asyncio
from pathlib import Path

root_dir = str(Path(__file__).parent.parent)
sys.path.extend(
    [
        root_dir,
        str(Path(root_dir) / "src"),
        str(Path(root_dir) / "util"),
    ]
)

from concurrency import set_recent_tid, reset_recent_tid
from create_rewrite import rewrite
from create_struct import temporary_table_pool
from format import format

input = [
    {
        "original_script_list": [
            format(
"""
SELECT "ITEM"."I_ITEM_ID" AS "I_ITEM_ID" , AVG ( "STORE_SALES"."SS_QUANTITY" ) AS "AGG1" , AVG ( "STORE_SALES"."SS_LIST_PRICE" ) AS "AGG2" , AVG ( "STORE_SALES"."SS_COUPON_AMT" ) AS "AGG3" , AVG ( "STORE_SALES"."SS_SALES_PRICE" ) AS "AGG4" FROM "STORE_SALES" AS "STORE_SALES" 
JOIN "DATE_DIM" AS "DATE_DIM" ON "DATE_DIM"."D_DATE_SK" = "STORE_SALES"."SS_SOLD_DATE_SK" 
JOIN "ITEM" AS "ITEM" ON "ITEM"."I_ITEM_SK" = "STORE_SALES"."SS_ITEM_SK" JOIN "PROMOTION" AS "PROMOTION" ON "PROMOTION"."P_PROMO_SK" = "STORE_SALES"."SS_PROMO_SK" GROUP BY "ITEM"."I_ITEM_ID"
"""
            ),
        ],
        "target_script": format(
"""
SELECT "ITEM"."I_ITEM_ID" AS "I_ITEM_ID" , AVG ( "STORE_SALES"."SS_QUANTITY" ) AS "AGG1" , AVG ( "STORE_SALES"."SS_LIST_PRICE" ) AS "AGG2" , AVG ( "STORE_SALES"."SS_COUPON_AMT" ) AS "AGG3" , AVG ( "STORE_SALES"."SS_SALES_PRICE" ) AS "AGG4" FROM "STORE_SALES" AS "STORE_SALES" 
JOIN "CUSTOMER_DEMOGRAPHICS" AS "CUSTOMER_DEMOGRAPHICS" ON "CUSTOMER_DEMOGRAPHICS"."CD_DEMO_SK" = "STORE_SALES"."SS_CDEMO_SK" AND "CUSTOMER_DEMOGRAPHICS"."CD_EDUCATION_STATUS" = \'4 yr Degree\' AND "CUSTOMER_DEMOGRAPHICS"."CD_GENDER" = \'M\' AND "CUSTOMER_DEMOGRAPHICS"."CD_MARITAL_STATUS" = \'M\' 
JOIN "DATE_DIM" AS "DATE_DIM" ON "DATE_DIM"."D_DATE_SK" = "STORE_SALES"."SS_SOLD_DATE_SK" AND "DATE_DIM"."D_YEAR" = 2001 
JOIN "ITEM" AS "ITEM" ON "ITEM"."I_ITEM_SK" = "STORE_SALES"."SS_ITEM_SK" JOIN "PROMOTION" AS "PROMOTION" ON ( "PROMOTION"."P_CHANNEL_EMAIL" = \'N\' OR "PROMOTION"."P_CHANNEL_EVENT" = \'N\' ) AND "PROMOTION"."P_PROMO_SK" = "STORE_SALES"."SS_PROMO_SK" 
GROUP BY "ITEM"."I_ITEM_ID" ORDER BY "I_ITEM_ID" NULLS LAST LIMIT 100
"""
        ),
    },
]


async def test(query):
    temporary_table_pool.update(query["original_script_list"][0], is_sample=False, size=0)
    print("\033[93m", rewrite(query["original_script_list"], query["target_script"]), "\033[0m")


if __name__ == "__main__":
    set_recent_tid(new_priority=1, new_running_sql="test", type="llm")
    for query in input:
        asyncio.run(test(query))
        break
    reset_recent_tid(type="llm")
