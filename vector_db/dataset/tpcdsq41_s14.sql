
select top 100 (i1.i_product_name)
 from item i1
 inner join (select i_product_name, max(i_item_id) as max_id from item group by i_product_name) i2 on i1.i_product_name = i2.max_id
 where i_manufact_id between 609 and 609+40 
   and (select count(*) as item_cnt
        from item
        where (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'thistle' or i_color = 'cyan') and 
        (i_units = 'Dozen' or i_units = 'Tsp') and
        (i_size = 'extra large' or i_size = 'medium')
        ) or
        (i_category = 'Women' and
        (i_color = 'slate' or i_color = 'puff') and
        (i_units = 'Ton' or i_units = 'Box') and
        (i_size = 'economy' or i_size = 'petite')
        ) or
        (i_category = 'Men' and
        (i_color = 'orange' or i_color = 'peach') and
        (i_units = 'Tbl' or i_units = 'Unknown') and
        (i_size = 'large' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'green' or i_color = 'forest') and
        (i_units = 'N/A' or i_units = 'Gram') and
        (i_size = 'extra large' or i_size = 'medium')
        ))) or
       (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'plum' or i_color = 'brown') and 
        (i_units = 'Bundle' or i_units = 'Case') and
        (i_size = 'extra large' or i_size = 'medium')
        ) or
        (i_category = 'Women' and
        (i_color = 'aquamarine' or i_color = 'cream') and
        (i_units = 'Oz' or i_units = 'Ounce') and
        (i_size = 'economy' or i_size = 'petite')
        ) or
        (i_category = 'Men' and
        (i_color = 'bisque' or i_color = 'seashell') and
        (i_units = 'Lb' or i_units = 'Bunch') and
        (i_size = 'large' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'maroon' or i_color = 'rosy') and
        (i_units = 'Dram' or i_units = 'Pound') and
        (i_size = 'extra large' or i_size = 'medium')
        )))) > 0
 order by i_product_name
 ;


