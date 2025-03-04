
select top 100 (i1.i_product_name)
 from item i1
 inner join (select i_product_name, max(i_item_id) as max_id from item group by i_product_name) i2 on i1.i_product_name = i2.max_id
 where i_manufact_id between 348 and 348+40 
   and (select count(*) as item_cnt
        from item
        where (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'ivory' or i_color = 'ghost') and 
        (i_units = 'Each' or i_units = 'Dozen') and
        (i_size = 'N/A' or i_size = 'small')
        ) or
        (i_category = 'Women' and
        (i_color = 'green' or i_color = 'almond') and
        (i_units = 'Oz' or i_units = 'Gram') and
        (i_size = 'economy' or i_size = 'large')
        ) or
        (i_category = 'Men' and
        (i_color = 'chiffon' or i_color = 'olive') and
        (i_units = 'Tsp' or i_units = 'Lb') and
        (i_size = 'petite' or i_size = 'medium')
        ) or
        (i_category = 'Men' and
        (i_color = 'seashell' or i_color = 'forest') and
        (i_units = 'Box' or i_units = 'Gross') and
        (i_size = 'N/A' or i_size = 'small')
        ))) or
       (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'misty' or i_color = 'navy') and 
        (i_units = 'Case' or i_units = 'Bundle') and
        (i_size = 'N/A' or i_size = 'small')
        ) or
        (i_category = 'Women' and
        (i_color = 'papaya' or i_color = 'sky') and
        (i_units = 'Unknown' or i_units = 'Pallet') and
        (i_size = 'economy' or i_size = 'large')
        ) or
        (i_category = 'Men' and
        (i_color = 'goldenrod' or i_color = 'firebrick') and
        (i_units = 'Dram' or i_units = 'Ounce') and
        (i_size = 'petite' or i_size = 'medium')
        ) or
        (i_category = 'Men' and
        (i_color = 'cornsilk' or i_color = 'khaki') and
        (i_units = 'Pound' or i_units = 'Tbl') and
        (i_size = 'N/A' or i_size = 'small')
        )))) > 0
 order by i_product_name
 ;


