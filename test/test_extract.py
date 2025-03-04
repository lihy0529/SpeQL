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
from extract import extract

input = [
    """
SELECT "SPEQLITE_TEMP_TABLE_5"."D_WEEK_SEQ" AS "D_WEEK_SEQ1" , ROUND ( "SPEQLITE_TEMP_TABLE_5"."SUN_SALES" / "WSWSCS_2"."SUN_SALES" , 2 ) AS "_COL_1" , ROUND ( "SPEQLITE_TEMP_TABLE_5"."MON_SALES" / "WSWSCS_2"."MON_SALES" , 2 ) AS "_COL_2" , ROUND ( "SPEQLITE_TEMP_TABLE_5"."TUE_SALES" / "WSWSCS_2"."TUE_SALES" , 2 ) AS "_COL_3" , ROUND ( "SPEQLITE_TEMP_TABLE_5"."WED_SALES" / "WSWSCS_2"."WED_SALES" , 2 ) AS "_COL_4" , ROUND ( "SPEQLITE_TEMP_TABLE_5"."THU_SALES" / "WSWSCS_2"."THU_SALES" , 2 ) AS "_COL_5" , ROUND ( "SPEQLITE_TEMP_TABLE_5"."FRI_SALES" / "WSWSCS_2"."FRI_SALES" , 2 ) AS "_COL_6" , ROUND ( "SPEQLITE_TEMP_TABLE_5"."SAT_SALES" / "WSWSCS_2"."SAT_SALES" , 2 ) AS "_COL_7" FROM "SPEQLITE_TEMP_TABLE_5" AS "SPEQLITE_TEMP_TABLE_5" JOIN "DATE_DIM" AS "DATE_DIM" ON "DATE_DIM"."D_WEEK_SEQ" = "SPEQLITE_TEMP_TABLE_5"."D_WEEK_SEQ" AND "DATE_DIM"."D_YEAR" = 2001 CROSS JOIN UNNEST ( "SPEQLITE_TEMP_TABLE_5" ) AS _T0 ( "WSWSCS_2" ) JOIN "DATE_DIM" AS "DATE_DIM_2" ON "DATE_DIM_2"."D_WEEK_SEQ" = "WSWSCS_2"."D_WEEK_SEQ" AND "DATE_DIM_2"."D_YEAR" = 2000
"""]


async def test(query):
    print(extract(query))


if __name__ == "__main__":
    set_recent_tid(new_priority=1, new_running_sql="test", type="llm")
    for query in input:
        asyncio.run(test(query))
        break
    reset_recent_tid(type="llm")

