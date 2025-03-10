-- start template query82.tpl query 67 in stream 0
select /* TPC-DS query82.tpl 0.67 */  i_item_id
       ,i_item_desc
       ,i_current_price
 from item, inventory, date_dim, store_sales
 where i_current_price between 12 and 12+30
 and inv_item_sk = i_item_sk
 and d_date_sk=inv_date_sk
 and d_date between cast('2002-04-05' as date) and dateadd(day,60,cast('2002-04-05' as date))
 and i_manufact_id in (400,448,910,149)
 and inv_quantity_on_hand between 100 and 500
 and ss_item_sk = i_item_sk
 group by i_item_id,i_item_desc,i_current_price
 order by i_item_id
 limit 100;

-- end template query82.tpl query 67 in stream 0