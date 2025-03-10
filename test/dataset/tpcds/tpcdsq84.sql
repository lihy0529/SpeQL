-- start template query84.tpl query 80 in stream 0
select /* TPC-DS query84.tpl 0.80 */  c_customer_id as customer_id
       , coalesce(c_last_name,'') || ', ' || coalesce(c_first_name,'') as customername
 from customer
     ,customer_address
     ,customer_demographics
     ,household_demographics
     ,income_band
     ,store_returns
 where ca_city	        =  'Greenville'
   and c_current_addr_sk = ca_address_sk
   and ib_lower_bound   >=  36218
   and ib_upper_bound   <=  36218 + 50000
   and ib_income_band_sk = hd_income_band_sk
   and cd_demo_sk = c_current_cdemo_sk
   and hd_demo_sk = c_current_hdemo_sk
   and sr_cdemo_sk = cd_demo_sk
 order by c_customer_id
 limit 100;

-- end template query84.tpl query 80 in stream 0