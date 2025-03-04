
select top 100 (i1.i_product_name)
 from item i1
 inner join (select i_product_name, max(i_item_id) as max_id from item group by i_product_name) i2 on i1.i_product_name = i2.max_id
 where i_manufact_id between 517 and 517+40 
   and (select count(*) as item_cnt
        from item
        where (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'aquamarine' or i_color = 'frosted') and 
        (i_units = 'Unknown' or i_units = 'Dozen') and
        (i_size = 'petite' or i_size = 'medium')
        ) or
        (i_category = 'Women' and
        (i_color = 'steel' or i_color = 'orange') and
        (i_units = 'Pallet' or i_units = 'Bundle') and
        (i_size = 'extra large' or i_size = 'small')
        ) or
        (i_category = 'Men' and
        (i_color = 'khaki' or i_color = 'pink') and
        (i_units = 'Ounce' or i_units = 'Oz') and
        (i_size = 'N/A' or i_size = 'economy')
        ) or
        (i_category = 'Men' and
        (i_color = 'burlywood' or i_color = 'linen') and
        (i_units = 'Ton' or i_units = 'Carton') and
        (i_size = 'petite' or i_size = 'medium')
        ))) or
       (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'papaya' or i_color = 'lawn') and 
        (i_units = 'Cup' or i_units = 'N/A') and
        (i_size = 'petite' or i_size = 'medium')
        ) or
        (i_category = 'Women' and
        (i_color = 'red' or i_color = 'almond') and
        (i_units = 'Tsp' or i_units = 'Dram') and
        (i_size = 'extra large' or i_size = 'small')
        ) or
        (i_category = 'Men' and
        (i_color = 'cyan' or i_color = 'rosy') and
        (i_units = 'Lb' or i_units = 'Tbl') and
        (i_size = 'N/A' or i_size = 'economy')
        ) or
        (i_category = 'Men' and
        (i_color = 'blanched' or i_color = 'grey') and
        (i_units = 'Box' or i_units = 'Case') and
        (i_size = 'petite' or i_size = 'medium')
        )))) > 0
 order by i_product_name
 ;


