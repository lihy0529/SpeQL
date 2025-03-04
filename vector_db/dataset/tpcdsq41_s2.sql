
select top 100 (i1.i_product_name)
 from item i1
 inner join (select i_product_name, max(i_item_id) as max_id from item group by i_product_name) i2 on i1.i_product_name = i2.max_id
 where i_manufact_id between 583 and 583+40 
   and (select count(*) as item_cnt
        from item
        where (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'blue' or i_color = 'tan') and 
        (i_units = 'Pallet' or i_units = 'Box') and
        (i_size = 'economy' or i_size = 'small')
        ) or
        (i_category = 'Women' and
        (i_color = 'pink' or i_color = 'powder') and
        (i_units = 'Lb' or i_units = 'N/A') and
        (i_size = 'extra large' or i_size = 'petite')
        ) or
        (i_category = 'Men' and
        (i_color = 'misty' or i_color = 'almond') and
        (i_units = 'Gross' or i_units = 'Tsp') and
        (i_size = 'N/A' or i_size = 'medium')
        ) or
        (i_category = 'Men' and
        (i_color = 'cyan' or i_color = 'white') and
        (i_units = 'Bundle' or i_units = 'Oz') and
        (i_size = 'economy' or i_size = 'small')
        ))) or
       (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'goldenrod' or i_color = 'dim') and 
        (i_units = 'Unknown' or i_units = 'Carton') and
        (i_size = 'economy' or i_size = 'small')
        ) or
        (i_category = 'Women' and
        (i_color = 'sienna' or i_color = 'burlywood') and
        (i_units = 'Each' or i_units = 'Pound') and
        (i_size = 'extra large' or i_size = 'petite')
        ) or
        (i_category = 'Men' and
        (i_color = 'gainsboro' or i_color = 'hot') and
        (i_units = 'Dozen' or i_units = 'Ton') and
        (i_size = 'N/A' or i_size = 'medium')
        ) or
        (i_category = 'Men' and
        (i_color = 'plum' or i_color = 'salmon') and
        (i_units = 'Bunch' or i_units = 'Tbl') and
        (i_size = 'economy' or i_size = 'small')
        )))) > 0
 order by i_product_name
 ;


