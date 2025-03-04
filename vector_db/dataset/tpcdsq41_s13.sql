
select top 100 (i1.i_product_name)
 from item i1
 inner join (select i_product_name, max(i_item_id) as max_id from item group by i_product_name) i2 on i1.i_product_name = i2.max_id
 where i_manufact_id between 393 and 393+40 
   and (select count(*) as item_cnt
        from item
        where (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'ivory' or i_color = 'khaki') and 
        (i_units = 'Box' or i_units = 'Bunch') and
        (i_size = 'economy' or i_size = 'petite')
        ) or
        (i_category = 'Women' and
        (i_color = 'floral' or i_color = 'lace') and
        (i_units = 'Case' or i_units = 'Unknown') and
        (i_size = 'extra large' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'coral' or i_color = 'tomato') and
        (i_units = 'Ton' or i_units = 'Dozen') and
        (i_size = 'large' or i_size = 'small')
        ) or
        (i_category = 'Men' and
        (i_color = 'aquamarine' or i_color = 'sienna') and
        (i_units = 'Oz' or i_units = 'Carton') and
        (i_size = 'economy' or i_size = 'petite')
        ))) or
       (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'mint' or i_color = 'cyan') and 
        (i_units = 'Lb' or i_units = 'Pound') and
        (i_size = 'economy' or i_size = 'petite')
        ) or
        (i_category = 'Women' and
        (i_color = 'blanched' or i_color = 'royal') and
        (i_units = 'Cup' or i_units = 'Dram') and
        (i_size = 'extra large' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'red' or i_color = 'burlywood') and
        (i_units = 'N/A' or i_units = 'Gross') and
        (i_size = 'large' or i_size = 'small')
        ) or
        (i_category = 'Men' and
        (i_color = 'dim' or i_color = 'burnished') and
        (i_units = 'Tsp' or i_units = 'Each') and
        (i_size = 'economy' or i_size = 'petite')
        )))) > 0
 order by i_product_name
 ;


