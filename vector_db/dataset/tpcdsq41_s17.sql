
select top 100 (i1.i_product_name)
 from item i1
 inner join (select i_product_name, max(i_item_id) as max_id from item group by i_product_name) i2 on i1.i_product_name = i2.max_id
 where i_manufact_id between 385 and 385+40 
   and (select count(*) as item_cnt
        from item
        where (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'violet' or i_color = 'saddle') and 
        (i_units = 'Ton' or i_units = 'Pound') and
        (i_size = 'economy' or i_size = 'medium')
        ) or
        (i_category = 'Women' and
        (i_color = 'navajo' or i_color = 'ivory') and
        (i_units = 'Tbl' or i_units = 'Box') and
        (i_size = 'petite' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'cornflower' or i_color = 'goldenrod') and
        (i_units = 'Bundle' or i_units = 'Oz') and
        (i_size = 'large' or i_size = 'extra large')
        ) or
        (i_category = 'Men' and
        (i_color = 'steel' or i_color = 'indian') and
        (i_units = 'Case' or i_units = 'Carton') and
        (i_size = 'economy' or i_size = 'medium')
        ))) or
       (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'lavender' or i_color = 'bisque') and 
        (i_units = 'Ounce' or i_units = 'Bunch') and
        (i_size = 'economy' or i_size = 'medium')
        ) or
        (i_category = 'Women' and
        (i_color = 'dim' or i_color = 'lace') and
        (i_units = 'Lb' or i_units = 'Unknown') and
        (i_size = 'petite' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'cornsilk' or i_color = 'ghost') and
        (i_units = 'Each' or i_units = 'Gram') and
        (i_size = 'large' or i_size = 'extra large')
        ) or
        (i_category = 'Men' and
        (i_color = 'khaki' or i_color = 'rose') and
        (i_units = 'N/A' or i_units = 'Cup') and
        (i_size = 'economy' or i_size = 'medium')
        )))) > 0
 order by i_product_name
 ;


