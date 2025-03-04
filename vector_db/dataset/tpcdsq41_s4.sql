
select top 100 (i1.i_product_name)
 from item i1
 inner join (select i_product_name, max(i_item_id) as max_id from item group by i_product_name) i2 on i1.i_product_name = i2.max_id
 where i_manufact_id between 427 and 427+40 
   and (select count(*) as item_cnt
        from item
        where (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'tomato' or i_color = 'pale') and 
        (i_units = 'Cup' or i_units = 'Carton') and
        (i_size = 'extra large' or i_size = 'small')
        ) or
        (i_category = 'Women' and
        (i_color = 'papaya' or i_color = 'dodger') and
        (i_units = 'Pallet' or i_units = 'Pound') and
        (i_size = 'large' or i_size = 'economy')
        ) or
        (i_category = 'Men' and
        (i_color = 'green' or i_color = 'tan') and
        (i_units = 'Bunch' or i_units = 'Case') and
        (i_size = 'petite' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'goldenrod' or i_color = 'red') and
        (i_units = 'Dram' or i_units = 'Bundle') and
        (i_size = 'extra large' or i_size = 'small')
        ))) or
       (i_manufact = i1.i_manufact and
        ((i_category = 'Women' and 
        (i_color = 'azure' or i_color = 'seashell') and 
        (i_units = 'Tbl' or i_units = 'Oz') and
        (i_size = 'extra large' or i_size = 'small')
        ) or
        (i_category = 'Women' and
        (i_color = 'lemon' or i_color = 'almond') and
        (i_units = 'Unknown' or i_units = 'Gross') and
        (i_size = 'large' or i_size = 'economy')
        ) or
        (i_category = 'Men' and
        (i_color = 'deep' or i_color = 'firebrick') and
        (i_units = 'Box' or i_units = 'Ton') and
        (i_size = 'petite' or i_size = 'N/A')
        ) or
        (i_category = 'Men' and
        (i_color = 'frosted' or i_color = 'chiffon') and
        (i_units = 'Each' or i_units = 'Gram') and
        (i_size = 'extra large' or i_size = 'small')
        )))) > 0
 order by i_product_name
 ;


