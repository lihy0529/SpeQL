
select top 100 (i1.i_product_name)
 from item i1
 inner join (select i_product_name, max(i_item_id) as max_id from item group by i_product_name) i2 on i1.i_product_name = i2.max_id
 where i_manufact_id between 377 and 377+40 
   and (select count(*) as item_cnt
        from item
        where (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'wheat' or i_color = 'smoke') and 
        (i_units = 'Each' or i_units = 'Gram') and
        (i_size = 'small' or i_size = 'medium')
        ) or
        (i_category = 'Women' and
        (i_color = 'burlywood' or i_color = 'misty') and
        (i_units = 'Ton' or i_units = 'Bundle') and
        (i_size = 'petite' or i_size = 'extra large')
        ) or
        (i_category = 'Men' and
        (i_color = 'gainsboro' or i_color = 'goldenrod') and
        (i_units = 'Oz' or i_units = 'Cup') and
        (i_size = 'large' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'yellow' or i_color = 'white') and
        (i_units = 'Tsp' or i_units = 'Bunch') and
        (i_size = 'small' or i_size = 'medium')
        ))) or
       (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'chocolate' or i_color = 'coral') and 
        (i_units = 'Dozen' or i_units = 'Dram') and
        (i_size = 'small' or i_size = 'medium')
        ) or
        (i_category = 'Women' and
        (i_color = 'pale' or i_color = 'forest') and
        (i_units = 'Box' or i_units = 'Case') and
        (i_size = 'petite' or i_size = 'extra large')
        ) or
        (i_category = 'Men' and
        (i_color = 'aquamarine' or i_color = 'puff') and
        (i_units = 'Gross' or i_units = 'Lb') and
        (i_size = 'large' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'royal' or i_color = 'firebrick') and
        (i_units = 'Carton' or i_units = 'Ounce') and
        (i_size = 'small' or i_size = 'medium')
        )))) > 0
 order by i_product_name
 ;


