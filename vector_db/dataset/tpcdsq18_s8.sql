
select top 100 i_item_id,
        ca_country,
        ca_state, 
        ca_county,
        avg( cast(cs_quantity as numeric(12,2))) agg1,
        avg( cast(cs_list_price as numeric(12,2))) agg2,
        avg( cast(cs_coupon_amt as numeric(12,2))) agg3,
        avg( cast(cs_sales_price as numeric(12,2))) agg4,
        avg( cast(cs_net_profit as numeric(12,2))) agg5,
        avg( cast(c_birth_year as numeric(12,2))) agg6,
        avg( cast(cd1.cd_dep_count as numeric(12,2))) agg7
 from catalog_sales, customer_demographics cd1, 
      customer_demographics cd2, customer, customer_address, date_dim, item
 where cs_sold_date_sk = d_date_sk and
       cs_item_sk = i_item_sk and
       cs_bill_cdemo_sk = cd1.cd_demo_sk and
       cs_bill_customer_sk = c_customer_sk and
       cd1.cd_gender = 'F' and 
       cd1.cd_education_status = 'Secondary' and
       c_current_cdemo_sk = cd2.cd_demo_sk and
       c_current_addr_sk = ca_address_sk and
       c_birth_month in (3,4,11,12,7,1) and
       d_year = 2000 and
       ca_state in ('TX','MO','AR'
                   ,'VA','MS','AZ','OR')
 group by rollup (i_item_id, ca_country, ca_state, ca_county)
 order by ca_country,
        ca_state, 
        ca_county,
	i_item_id
 ;


