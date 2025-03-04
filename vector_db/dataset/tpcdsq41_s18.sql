
select top 100 (i1.i_product_name)
 from item i1
 inner join (select i_product_name, max(i_item_id) as max_id from item group by i_product_name) i2 on i1.i_product_name = i2.max_id
 where i_manufact_id between 397 and 397+40 
   and (select count(*) as item_cnt
        from item
        where (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'mint' or i_color = 'saddle') and 
        (i_units = 'Bunch' or i_units = 'Unknown') and
        (i_size = 'petite' or i_size = 'small')
        ) or
        (i_category = 'Women' and
        (i_color = 'blanched' or i_color = 'dodger') and
        (i_units = 'Tsp' or i_units = 'Bundle') and
        (i_size = 'medium' or i_size = 'economy')
        ) or
        (i_category = 'Men' and
        (i_color = 'olive' or i_color = 'beige') and
        (i_units = 'Cup' or i_units = 'Box') and
        (i_size = 'large' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'burlywood' or i_color = 'floral') and
        (i_units = 'Pallet' or i_units = 'Gross') and
        (i_size = 'petite' or i_size = 'small')
        ))) or
       (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'linen' or i_color = 'salmon') and 
        (i_units = 'Carton' or i_units = 'Each') and
        (i_size = 'petite' or i_size = 'small')
        ) or
        (i_category = 'Women' and
        (i_color = 'pink' or i_color = 'cornflower') and
        (i_units = 'Gram' or i_units = 'Tbl') and
        (i_size = 'medium' or i_size = 'economy')
        ) or
        (i_category = 'Men' and
        (i_color = 'magenta' or i_color = 'gainsboro') and
        (i_units = 'Case' or i_units = 'Dozen') and
        (i_size = 'large' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'frosted' or i_color = 'goldenrod') and
        (i_units = 'Oz' or i_units = 'N/A') and
        (i_size = 'petite' or i_size = 'small')
        )))) > 0
 order by i_product_name
 ;


