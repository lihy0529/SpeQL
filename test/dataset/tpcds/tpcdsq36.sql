-- start template query36a.tpl query 21 in stream 0
with /* TPC-DS query36a.tpl 0.21 */ results as
 (select 
    sum(ss_net_profit) as ss_net_profit, sum(ss_ext_sales_price) as ss_ext_sales_price,
    sum(ss_net_profit)/sum(ss_ext_sales_price) as gross_margin
   ,i_category
   ,i_class
   ,0 as g_category, 0 as g_class
 from
    store_sales
   ,date_dim       d1
   ,item
   ,store
 where
    d1.d_year = 2002 
    and d1.d_date_sk = ss_sold_date_sk
    and i_item_sk  = ss_item_sk 
    and s_store_sk  = ss_store_sk
    and s_state in ('MN','TN','MI','WV',
                 'NC','GA','TN','OH')
 group by i_category,i_class)
 ,
 results_rollup as
 (select gross_margin ,i_category ,i_class,0 as t_category, 0 as t_class, 0 as lochierarchy from results
 union
 select sum(ss_net_profit)/sum(ss_ext_sales_price) as gross_margin,
   i_category, NULL AS i_class, 0 as t_category, 1 as t_class, 1 as lochierarchy from results group by i_category
 union
 select sum(ss_net_profit)/sum(ss_ext_sales_price) as gross_margin,
   NULL AS i_category ,NULL AS i_class, 1 as t_category, 1 as t_class, 2 as lochierarchy from results)
  select 
  gross_margin ,i_category ,i_class, lochierarchy,rank() over (
 	partition by lochierarchy, case when t_class = 0 then i_category end 
 	order by gross_margin asc) as rank_within_parent
 from results_rollup
 order by
   lochierarchy desc
  ,case when lochierarchy = 0 then i_category end
  ,rank_within_parent
  limit 100;

-- end template query36a.tpl query 21 in stream 0