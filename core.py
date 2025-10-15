from typing import Union, List, Dict
from data import CITY_SOCIAL_UPPER_LIMITS, CITY_HOUSING_FUND_LIMITS, TAX_RATE_TABLE

# ------------------- 核心计算逻辑 -------------------
def calculate_monthly_details(
    monthly_salaries: Union[float, List[float]],
    social_security_bases: Union[float, List[float]],
    city: str = "北京",
    five_insurance_rate: float = 0.105,
    housing_fund_rate: float = 0.12
) -> Dict[str, List[Union[float, Dict]]]:
    """
    计算本年每月详细薪资数据
    
    返回：
        - monthly: 每个月的当月值明细（表格用）
        - annual_summary: 全年累计值汇总（年度区域用）
    """
    # 输入标准化（保持不变）
    if isinstance(monthly_salaries, (int, float)):
        monthly_salaries = [monthly_salaries] * 12
    elif isinstance(monthly_salaries, list) and len(monthly_salaries) != 12:
        raise ValueError("月薪需为单个数值或12个元素的列表")
    
    if isinstance(social_security_bases, (int, float)):
        social_security_bases = [social_security_bases] * 12
    elif isinstance(social_security_bases, list) and len(social_security_bases) != 12:
        raise ValueError("社保基数需为单个数值或12个元素的列表")
    
    # 初始化变量（保持不变）
    cumulative_income = 0.0                  # 累计税前收入
    cumulative_social_housing = 0.0          # 累计五险一金
    cumulative_housing_fund = 0.0          # 累计公积金
    cumulative_tax = 0.0                     # 累计已缴个税
    monthly_details = []                     # 每月**当月值**明细
    annual_summary = {}                      # 全年**累计值**汇总


    for month in range(1, 13):
        current_salary = monthly_salaries[month-1]       # 当月税前收入
        current_social_base = social_security_bases[month-1]  # 当月社保基数
        
        # ------------------- 1. 计算当月社保/公积金（修正医疗保险上限） -------------------
        # 养老保险（含城市上限）
        pension_upper = CITY_SOCIAL_UPPER_LIMITS[city]["pension"]
        pension = min(current_social_base * 0.08, pension_upper) 
        # 医疗保险（**新增上限**）
        medical_upper = CITY_SOCIAL_UPPER_LIMITS[city]["medical"]
        medical = min(current_social_base * 0.02, medical_upper)  # 医疗保险比例2%
        # 失业保险（含城市上限）
        unemployment_upper = CITY_SOCIAL_UPPER_LIMITS[city]["unemployment"]
        unemployment = min(current_social_base * 0.005, unemployment_upper) 
        # 当月社保合计
        social_total = pension + medical + unemployment
        # 当月公积金（**使用补全的公积金上限**）
        housing_limit = CITY_HOUSING_FUND_LIMITS.get(city, float('inf'))
        housing_fund = min(current_social_base, housing_limit) * housing_fund_rate
        # 当月五险一金合计
        total_social_housing = social_total + housing_fund


        # ------------------- 2. 计算累计值（用于个税，不放入表格） -------------------
        cumulative_income += current_salary                          # 累计税前收入
        cumulative_social_housing += total_social_housing            # 累计五险一金
        cumulative_housing_fund += housing_fund                      # 累计公积金

        # ------------------- 3. 计算当月个税（保持不变） -------------------
        cumulative_taxable_income = cumulative_income - 5000 * month - cumulative_social_housing
        cumulative_monthly_tax = 0.0
        for limit, rate, deduction in TAX_RATE_TABLE:
            if cumulative_taxable_income <= limit:
                cumulative_monthly_tax = cumulative_taxable_income * rate - deduction
                break
        current_month_tax = cumulative_monthly_tax - cumulative_tax
        current_month_tax = max(current_month_tax, 0.0)
        cumulative_tax = cumulative_monthly_tax


        # ------------------- 4. 计算当月税后收入（保持不变） -------------------
        takehome = current_salary - social_total - housing_fund - current_month_tax
        takehome = max(takehome, 0.0)


        # ------------------- 5. 保存当月**单月值**到表格（新增医疗保险上限） -------------------
        monthly_details.append({
            "month": month,
            "pre_tax_income": round(current_salary, 2),
            "pension": round(pension, 2),
            "medical": round(medical, 2),  # 修正后的医疗保险（含上限）
            "unemployment": round(unemployment, 2),
            "housing_fund": round(housing_fund, 2),
            "taxable_income": round(cumulative_taxable_income, 2),
            "current_tax": round(current_month_tax, 2),
            "takehome": round(takehome, 2)
        })


    # ------------------- 6. 计算全年累计值 -------------------
    total_pre_tax = round(cumulative_income, 2) # 全年税前收入
    total_housing_fund = round(cumulative_housing_fund, 2) # 全年累计单边公积金
    total_tax = round(cumulative_tax, 2) # 全年累计税收
    total_takehome = round(cumulative_income - cumulative_social_housing - cumulative_tax, 2) # 全年累计税后收入
    total_takehome_with_housing = total_takehome + total_housing_fund*2 # 全年累计税后收入, 含双边公积金


    annual_summary = {
        "total_pre_tax": total_pre_tax,
        "total_housing_fund": total_housing_fund,
        "total_tax": total_tax,
        "total_takehome": total_takehome,
        "total_takehome_with_housing": total_takehome_with_housing
    }


    return {"monthly": monthly_details, "annual": annual_summary}

