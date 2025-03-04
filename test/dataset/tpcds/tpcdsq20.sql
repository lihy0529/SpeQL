-- start template query20.tpl query 65 in stream 0
select /* TPC-DS query20.tpl 0.65 */  i_item_id
       ,i_item_desc 
       ,i_category 
       ,i_class 
       ,i_current_price
       ,sum(cs_ext_sales_price) as itemrevenue 
       ,sum(cs_ext_sales_price)*100/sum(sum(cs_ext_sales_price)) over
           (partition by i_class) as revenueratio
 from	catalog_sales
     ,item 
     ,date_dim
 where cs_item_sk = i_item_sk 
   and i_category in ('Shoes', 'Sports', 'Electronics')
   and cs_sold_date_sk = d_date_sk
 and d_date between cast('1998-05-13' as date) 
 				and dateadd(day,30,cast('1998-05-13' as date))
 group by i_item_id
         ,i_item_desc 
         ,i_category
         ,i_class
         ,i_current_price
 order by i_category
         ,i_class
         ,i_item_id
         ,i_item_desc
         ,revenueratio
limit 100;

-- end template query20.tpl query 65 in stream 0