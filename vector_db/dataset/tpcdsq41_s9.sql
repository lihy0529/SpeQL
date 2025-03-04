
select top 100 (i1.i_product_name)
 from item i1
 inner join (select i_product_name, max(i_item_id) as max_id from item group by i_product_name) i2 on i1.i_product_name = i2.max_id
 where i_manufact_id between 605 and 605+40 
   and (select count(*) as item_cnt
        from item
        where (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'light' or i_color = 'misty') and 
        (i_units = 'Dozen' or i_units = 'Gross') and
        (i_size = 'extra large' or i_size = 'medium')
        ) or
        (i_category = 'Women' and
        (i_color = 'royal' or i_color = 'chocolate') and
        (i_units = 'Pallet' or i_units = 'Box') and
        (i_size = 'small' or i_size = 'petite')
        ) or
        (i_category = 'Men' and
        (i_color = 'dim' or i_color = 'gainsboro') and
        (i_units = 'Gram' or i_units = 'Bunch') and
        (i_size = 'large' or i_size = 'economy')
        ) or
        (i_category = 'Men' and
        (i_color = 'khaki' or i_color = 'black') and
        (i_units = 'Tbl' or i_units = 'Bundle') and
        (i_size = 'extra large' or i_size = 'medium')
        ))) or
       (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'orange' or i_color = 'lemon') and 
        (i_units = 'Lb' or i_units = 'Ounce') and
        (i_size = 'extra large' or i_size = 'medium')
        ) or
        (i_category = 'Women' and
        (i_color = 'orchid' or i_color = 'turquoise') and
        (i_units = 'Cup' or i_units = 'Dram') and
        (i_size = 'small' or i_size = 'petite')
        ) or
        (i_category = 'Men' and
        (i_color = 'dark' or i_color = 'metallic') and
        (i_units = 'Oz' or i_units = 'Tsp') and
        (i_size = 'large' or i_size = 'economy')
        ) or
        (i_category = 'Men' and
        (i_color = 'burnished' or i_color = 'ivory') and
        (i_units = 'Ton' or i_units = 'Carton') and
        (i_size = 'extra large' or i_size = 'medium')
        )))) > 0
 order by i_product_name
 ;


