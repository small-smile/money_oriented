import baostock as bs
import pandas as pd

# 登录
print("\n[1] 登录 baostock...")
lg = bs.login()
if lg.error_code != '0':
    print(f"登录失败: {lg.error_msg}")
    exit(0)
print("登录成功")

# 查询除权除息记录
# code = "sh.601398"  # 工商银行
code = "sh.600036"  # 工商银行
rs_dividend = bs.query_dividend_data(code=code, year="", yearType="operate")
print(len(rs_dividend.get_row_data()), rs_dividend.data, rs_dividend.fields)

# 提取数据
print("\n[2] 除权除息记录：")
dividend_list = []
while (rs_dividend.error_code == '0') & rs_dividend.next():
    dividend_list.append(rs_dividend.get_row_da())

if len(dividend_list) > 0:
    df_dividend = pd.DataFrame(dividend_list, columns=rs_dividend.fields)
    print(df_dividend.to_string(index=False))

    # 筛选2011年之后的记录
    df_dividend['dividDivDate'] = pd.to_datetime(df_dividend['dividDivDate'])
    df_after_2011 = df_dividend[df_dividend['dividDivDate'] >= '2011-01-01']

    print(f"\n[3] 2011年之后的除权除息记录数量：{len(df_after_2011)}")
    if len(df_after_2011) > 0:
        print(df_after_2011[['dividDivDate', 'typeDes']].to_string(index=False))
    else:
        print("✅ 2011年后无任何除权除息记录（符合条件）")
else:
    print("无除权除息记录")

# 登出
bs.logout()
