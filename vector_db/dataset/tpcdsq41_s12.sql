
select top 100 (i1.i_product_name)
 from item i1
 inner join (select i_product_name, max(i_item_id) as max_id from item group by i_product_name) i2 on i1.i_product_name = i2.max_id
 where i_manufact_id between 336 and 336+40 
   and (select count(*) as item_cnt
        from item
        where (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'lime' or i_color = 'hot') and 
        (i_units = 'Box' or i_units = 'Case') and
        (i_size = 'economy' or i_size = 'medium')
        ) or
        (i_category = 'Women' and
        (i_color = 'wheat' or i_color = 'black') and
        (i_units = 'Unknown' or i_units = 'Oz') and
        (i_size = 'petite' or i_size = 'extra large')
        ) or
        (i_category = 'Men' and
        (i_color = 'cornflower' or i_color = 'lace') and
        (i_units = 'Pound' or i_units = 'Gram') and
        (i_size = 'large' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'azure' or i_color = 'maroon') and
        (i_units = 'N/A' or i_units = 'Bunch') and
        (i_size = 'economy' or i_size = 'medium')
        ))) or
       (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'olive' or i_color = 'ghost') and 
        (i_units = 'Tbl' or i_units = 'Lb') and
        (i_size = 'economy' or i_size = 'medium')
        ) or
        (i_category = 'Women' and
        (i_color = 'green' or i_color = 'puff') and
        (i_units = 'Ounce' or i_units = 'Each') and
        (i_size = 'petite' or i_size = 'extra large')
        ) or
        (i_category = 'Men' and
        (i_color = 'moccasin' or i_color = 'grey') and
        (i_units = 'Cup' or i_units = 'Dram') and
        (i_size = 'large' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'yellow' or i_color = 'coral') and
        (i_units = 'Gross' or i_units = 'Bundle') and
        (i_size = 'economy' or i_size = 'medium')
        )))) > 0
 order by i_product_name
 ;


