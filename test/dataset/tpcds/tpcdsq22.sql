-- start template query22a.tpl query 55 in stream 0
with /* TPC-DS query22a.tpl 0.55 */ results as 
(select  i_product_name
             ,i_brand
             ,i_class
             ,i_category
             ,avg(inv_quantity_on_hand) qoh
       from inventory
           ,date_dim
           ,item
--         ,warehouse
       where  inv_date_sk=d_date_sk
              and inv_item_sk=i_item_sk
--            and inv_warehouse_sk = w_warehouse_sk
              and d_month_seq between 1183 and 1183 + 11
       group by i_product_name,i_brand,i_class,i_category),
results_rollup as 
(select i_product_name, i_brand, i_class, i_category,avg(qoh) qoh 
from results 
group by i_product_name,i_brand,i_class,i_category
union all 
select i_product_name, i_brand, i_class, null i_category,avg(qoh) qoh 
from results
group by i_product_name,i_brand,i_class
union all 
select i_product_name, i_brand, null i_class, null i_category,avg(qoh) qoh 
from results
group by i_product_name,i_brand
union all 
select i_product_name, null i_brand, null i_class, null i_category,avg(qoh)  qoh 
from results
group by i_product_name
union all 
select null i_product_name, null i_brand, null i_class, null i_category,avg(qoh) qoh 
from results)
 select  i_product_name, i_brand, i_class, i_category,qoh
      from results_rollup
      order by qoh, i_product_name, i_brand, i_class, i_category
limit 100;

-- end template query22a.tpl query 55 in stream 0