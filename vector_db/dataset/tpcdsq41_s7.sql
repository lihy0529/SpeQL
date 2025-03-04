
select top 100 (i1.i_product_name)
 from item i1
 inner join (select i_product_name, max(i_item_id) as max_id from item group by i_product_name) i2 on i1.i_product_name = i2.max_id
 where i_manufact_id between 430 and 430+40 
   and (select count(*) as item_cnt
        from item
        where (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'ivory' or i_color = 'cornflower') and 
        (i_units = 'Case' or i_units = 'Each') and
        (i_size = 'large' or i_size = 'small')
        ) or
        (i_category = 'Women' and
        (i_color = 'salmon' or i_color = 'powder') and
        (i_units = 'Tsp' or i_units = 'Dozen') and
        (i_size = 'medium' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'tan' or i_color = 'floral') and
        (i_units = 'Bunch' or i_units = 'Box') and
        (i_size = 'economy' or i_size = 'extra large')
        ) or
        (i_category = 'Men' and
        (i_color = 'yellow' or i_color = 'blanched') and
        (i_units = 'Ton' or i_units = 'Tbl') and
        (i_size = 'large' or i_size = 'small')
        ))) or
       (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'midnight' or i_color = 'antique') and 
        (i_units = 'Ounce' or i_units = 'Cup') and
        (i_size = 'large' or i_size = 'small')
        ) or
        (i_category = 'Women' and
        (i_color = 'almond' or i_color = 'green') and
        (i_units = 'Pound' or i_units = 'Gross') and
        (i_size = 'medium' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'burnished' or i_color = 'royal') and
        (i_units = 'Oz' or i_units = 'Bundle') and
        (i_size = 'economy' or i_size = 'extra large')
        ) or
        (i_category = 'Men' and
        (i_color = 'navy' or i_color = 'light') and
        (i_units = 'Lb' or i_units = 'Gram') and
        (i_size = 'large' or i_size = 'small')
        )))) > 0
 order by i_product_name
 ;


