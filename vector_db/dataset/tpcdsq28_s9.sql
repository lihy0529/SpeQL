
select top 100 *
from (select avg(ss_list_price) B1_LP
            ,count(ss_list_price) B1_CNT
            ,count(distinct ss_list_price) B1_CNTD
      from store_sales
      where ss_quantity between 0 and 5
        and (ss_list_price between 30 and 30+10 
             or ss_coupon_amt between 2177 and 2177+1000
             or ss_wholesale_cost between 36 and 36+20)) B1,
     (select avg(ss_list_price) B2_LP
            ,count(ss_list_price) B2_CNT
            ,count(distinct ss_list_price) B2_CNTD
      from store_sales
      where ss_quantity between 6 and 10
        and (ss_list_price between 128 and 128+10
          or ss_coupon_amt between 8657 and 8657+1000
          or ss_wholesale_cost between 41 and 41+20)) B2,
     (select avg(ss_list_price) B3_LP
            ,count(ss_list_price) B3_CNT
            ,count(distinct ss_list_price) B3_CNTD
      from store_sales
      where ss_quantity between 11 and 15
        and (ss_list_price between 15 and 15+10
          or ss_coupon_amt between 17585 and 17585+1000
          or ss_wholesale_cost between 13 and 13+20)) B3,
     (select avg(ss_list_price) B4_LP
            ,count(ss_list_price) B4_CNT
            ,count(distinct ss_list_price) B4_CNTD
      from store_sales
      where ss_quantity between 16 and 20
        and (ss_list_price between 140 and 140+10
          or ss_coupon_amt between 14755 and 14755+1000
          or ss_wholesale_cost between 40 and 40+20)) B4,
     (select avg(ss_list_price) B5_LP
            ,count(ss_list_price) B5_CNT
            ,count(distinct ss_list_price) B5_CNTD
      from store_sales
      where ss_quantity between 21 and 25
        and (ss_list_price between 162 and 162+10
          or ss_coupon_amt between 6792 and 6792+1000
          or ss_wholesale_cost between 61 and 61+20)) B5,
     (select avg(ss_list_price) B6_LP
            ,count(ss_list_price) B6_CNT
            ,count(distinct ss_list_price) B6_CNTD
      from store_sales
      where ss_quantity between 26 and 30
        and (ss_list_price between 81 and 81+10
          or ss_coupon_amt between 17802 and 17802+1000
          or ss_wholesale_cost between 0 and 0+20)) B6
;


