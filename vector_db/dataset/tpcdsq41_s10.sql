
select top 100 (i1.i_product_name)
 from item i1
 inner join (select i_product_name, max(i_item_id) as max_id from item group by i_product_name) i2 on i1.i_product_name = i2.max_id
 where i_manufact_id between 535 and 535+40 
   and (select count(*) as item_cnt
        from item
        where (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'puff' or i_color = 'brown') and 
        (i_units = 'Tsp' or i_units = 'Cup') and
        (i_size = 'small' or i_size = 'economy')
        ) or
        (i_category = 'Women' and
        (i_color = 'blanched' or i_color = 'beige') and
        (i_units = 'Pallet' or i_units = 'Gross') and
        (i_size = 'N/A' or i_size = 'petite')
        ) or
        (i_category = 'Men' and
        (i_color = 'drab' or i_color = 'honeydew') and
        (i_units = 'Box' or i_units = 'Ton') and
        (i_size = 'large' or i_size = 'medium')
        ) or
        (i_category = 'Men' and
        (i_color = 'aquamarine' or i_color = 'metallic') and
        (i_units = 'Pound' or i_units = 'Oz') and
        (i_size = 'small' or i_size = 'economy')
        ))) or
       (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'bisque' or i_color = 'almond') and 
        (i_units = 'Unknown' or i_units = 'Case') and
        (i_size = 'small' or i_size = 'economy')
        ) or
        (i_category = 'Women' and
        (i_color = 'forest' or i_color = 'navy') and
        (i_units = 'Dozen' or i_units = 'Lb') and
        (i_size = 'N/A' or i_size = 'petite')
        ) or
        (i_category = 'Men' and
        (i_color = 'pink' or i_color = 'chartreuse') and
        (i_units = 'Gram' or i_units = 'Bundle') and
        (i_size = 'large' or i_size = 'medium')
        ) or
        (i_category = 'Men' and
        (i_color = 'salmon' or i_color = 'slate') and
        (i_units = 'Ounce' or i_units = 'Dram') and
        (i_size = 'small' or i_size = 'economy')
        )))) > 0
 order by i_product_name
 ;


