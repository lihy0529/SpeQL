
select top 100 (i1.i_product_name)
 from item i1
 inner join (select i_product_name, max(i_item_id) as max_id from item group by i_product_name) i2 on i1.i_product_name = i2.max_id
 where i_manufact_id between 402 and 402+40 
   and (select count(*) as item_cnt
        from item
        where (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'blanched' or i_color = 'cream') and 
        (i_units = 'Gram' or i_units = 'Tsp') and
        (i_size = 'extra large' or i_size = 'small')
        ) or
        (i_category = 'Women' and
        (i_color = 'khaki' or i_color = 'almond') and
        (i_units = 'Unknown' or i_units = 'Bunch') and
        (i_size = 'large' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'misty' or i_color = 'bisque') and
        (i_units = 'Tbl' or i_units = 'Each') and
        (i_size = 'petite' or i_size = 'economy')
        ) or
        (i_category = 'Men' and
        (i_color = 'salmon' or i_color = 'slate') and
        (i_units = 'Oz' or i_units = 'Box') and
        (i_size = 'extra large' or i_size = 'small')
        ))) or
       (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'medium' or i_color = 'cyan') and 
        (i_units = 'Ounce' or i_units = 'N/A') and
        (i_size = 'extra large' or i_size = 'small')
        ) or
        (i_category = 'Women' and
        (i_color = 'aquamarine' or i_color = 'ivory') and
        (i_units = 'Lb' or i_units = 'Pound') and
        (i_size = 'large' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'indian' or i_color = 'metallic') and
        (i_units = 'Case' or i_units = 'Dozen') and
        (i_size = 'petite' or i_size = 'economy')
        ) or
        (i_category = 'Men' and
        (i_color = 'hot' or i_color = 'tomato') and
        (i_units = 'Dram' or i_units = 'Ton') and
        (i_size = 'extra large' or i_size = 'small')
        )))) > 0
 order by i_product_name
 ;


