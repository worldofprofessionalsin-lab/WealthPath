import io
import math
from dataclasses import dataclass
from datetime import date

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter

st.set_page_config(page_title="WealthPath", page_icon="🏠", layout="wide")
st.markdown("""<style>
:root{--cream:#fffaf0;--green:#174b3a;--saffron:#d97706}
.stApp{background:var(--cream)} h1,h2,h3{color:var(--green)}
div[data-testid=\"stMetric\"]{background:white;border:1px solid #eadfcb;border-radius:14px;padding:12px}
.best{background:#edf7f2;border-left:5px solid #174b3a;padding:16px;border-radius:10px}
</style>""", unsafe_allow_html=True)

def money(x): return f"₹{x:,.0f}"

def emi(principal, annual_rate, months):
    r=annual_rate/1200
    return principal/months if r==0 else principal*r*(1+r)**months/((1+r)**months-1)

def effective_return(row):
    gross=float(row["Expected return %"])/100
    tax=float(row["Tax rate %"])/100 if row["Taxable"] else 0
    return gross*(1-tax)

def weighted_return(inv):
    weights=inv["Current value"]+inv["Monthly contribution"]*12
    if weights.sum()<=0: return 0.0
    return float(np.average(inv.apply(effective_return,axis=1),weights=weights))

@dataclass
class Result:
    name:str; interest:float; close_month:int; corpus:float; net_worth:float; liquidity:float; risk:float; rows:list

def simulate(name, loan, rate, tenure_m, payment, start_corpus, inv_r, invest_share,
             prepay_frequency=None, annual_growth=0, leveraged=False):
    balance=loan; invested=start_corpus+(loan if leveraged else 0); cash=0.0; total_interest=0; rows=[]
    monthly_r=inv_r/12; loan_r=rate/1200; close_month=tenure_m
    for m in range(1,361):
        opening_balance=balance
        opening_investment=invested
        yearly_factor=(1+annual_growth/100)**((m-1)//12)
        capacity=payment*yearly_factor
        scheduled=emi(loan,rate,tenure_m) if balance>0 else 0
        interest=balance*loan_r
        principal=max(0,min(balance,scheduled-interest))
        balance-=principal; total_interest+=interest
        do_prepay=(prepay_frequency=="monthly" or
                   prepay_frequency=="quarterly" and m%3==0 or
                   prepay_frequency=="annual" and m%12==0)
        prepay=capacity*(1-invest_share) if do_prepay and balance>0 else 0
        prepay=min(balance,prepay); balance-=prepay
        invest=capacity*invest_share
        if name=="Only EMI": cash+=capacity
        if balance<=0 and close_month==tenure_m: close_month=m
        emi_redirect=scheduled if balance<=0 else 0
        if balance<=0: invest += emi_redirect
        investment_growth=invested*monthly_r
        invested=invested*(1+monthly_r)+invest
        corpus=invested+cash
        if prepay>0 and invest>0: action="Pay EMI, prepay and invest"
        elif prepay>0: action="Pay EMI and make prepayment"
        elif invest>0: action="Pay EMI and invest"
        elif scheduled>0: action="Pay regular EMI; retain surplus"
        else: action="Loan closed; continue wealth building"
        rows.append({"Month":m,"Action":action,"Opening loan balance":opening_balance,
                     "Scheduled EMI":min(scheduled,opening_balance+interest),"Interest":interest,
                     "Principal repaid":principal,"Prepayment":prepay,"Loan outstanding":max(0,balance),
                     "Opening investment value":opening_investment,"Investment":invest,
                     "Expected investment growth":investment_growth,"Investment corpus":corpus,
                     "EMI redirected after closure":emi_redirect,"Monthly capacity":capacity})
    property_equity=max(0,loan-balance)
    risk=invest_share*8+(2 if leveraged else 0)
    return Result(name,total_interest,close_month,corpus,corpus+property_equity-balance,invest_share*10,risk,rows)

st.title("🏠 WealthPath — Home Loan & Wealth Optimizer")
st.caption("Compare loan prepayment and investing using your actual income, expenses, assets and investment assumptions.")

with st.sidebar:
    st.header("Your priority")
    objective=st.selectbox("What matters most?",["Balanced plan","Close loan fastest","Maximise net worth","Lowest risk","Highest liquidity"],
        help="This changes how strategies are ranked; it does not change the underlying calculations.")
    leveraged=st.toggle("Can loan proceeds be invested?",False,help="Normally No for a home loan. Yes models a high-risk leveraged scenario.")
    run_mc=st.toggle("Run 10,000 market simulations",False)

t1,t2,t3,t4=st.tabs(["1 · Income & expenses","2 · Loan","3 · Assets & investments","4 · Results"])
with t1:
    st.subheader("Monthly cash flow")
    st.info("The tool calculates available surplus; you do not enter a planned investment amount.")
    c1,c2,c3=st.columns(3)
    salary=c1.number_input("Monthly in-hand income",0.0,value=120000.0,step=5000.0,help="Household take-home income available before expenses and EMIs.")
    spouse=c2.number_input("Spouse/other monthly income",0.0,value=0.0,step=5000.0)
    growth=c3.number_input("Annual income growth %",0.0,30.0,6.0,0.5,help="Raises future surplus; treated as an assumption, not guaranteed.")
    expenses=st.data_editor(pd.DataFrame({"Expense":["Household","Education","Insurance & medical","Travel","Other"],"Monthly amount":[35000,5000,5000,3000,2000]}),num_rows="dynamic",use_container_width=True)
    existing_emi=st.number_input("Other loan EMIs",0.0,value=0.0,step=1000.0)
    buffer_pct=st.slider("Safety buffer (% of income)",0,30,10,help="Protected cash not allocated to investment or prepayment.")
    total_income=salary+spouse; total_exp=float(expenses["Monthly amount"].sum())
    safe_surplus=max(0,total_income-total_exp-existing_emi-total_income*buffer_pct/100)
    st.metric("Calculated safe monthly surplus",money(safe_surplus),help="Income − expenses − other EMIs − safety buffer.")

with t2:
    st.subheader("Home loan")
    c1,c2,c3=st.columns(3)
    property_value=c1.number_input("Property value",0.0,value=7500000.0,step=100000.0)
    loan=c2.number_input("Loan amount",0.0,value=5500000.0,step=100000.0)
    charges=c3.number_input("Registration and other charges",0.0,value=500000.0,step=50000.0)
    rate=c1.number_input("Current interest rate %",0.0,30.0,8.5,0.05,help="Monthly reducing-balance rate. Update this when a floating rate changes.")
    tenure_y=int(c2.number_input("Remaining tenure (years)",1,40,20))
    annual_prepay=c3.number_input("Optional annual lump sum",0.0,value=0.0,step=10000.0,help="Bonus or other amount available once each year, separate from monthly surplus.")
    loan_start=st.date_input("Loan/report start date",value=date.today().replace(day=1),help="Used to convert Month 1, Month 2 and later actions into calendar months in the Excel report.")
    base_emi=emi(loan,rate,tenure_y*12)
    own_contribution=max(0,property_value+charges-loan)
    a,b=st.columns(2); a.metric("Calculated EMI",money(base_emi)); b.metric("Own contribution",money(own_contribution))

with t3:
    st.subheader("Existing assets")
    assets=st.data_editor(pd.DataFrame({"Asset":["Bank / emergency fund","FD / debt","Equity / mutual funds","PF / NPS","Gold"],"Current value":[300000,100000,500000,400000,100000],"Available for plan %":[0,50,100,0,0]}),num_rows="dynamic",use_container_width=True,
        column_config={"Available for plan %":st.column_config.NumberColumn(min_value=0,max_value=100,help="Only this portion is counted as usable starting wealth.")})
    usable_assets=float((assets["Current value"]*assets["Available for plan %"]/100).sum())
    st.metric("Assets available to the plan",money(usable_assets))
    st.subheader("Investment assumptions")
    st.caption("Enter the actual holdings/options you want evaluated. Returns are projections, not guarantees.")
    investments=st.data_editor(pd.DataFrame({"Investment":["Equity mutual fund","Debt / FD"],"Current value":[400000,100000],"Monthly contribution":[5000,0],"Expected return %":[11.0,7.0],"Taxable":[True,True],"Tax rate %":[12.5,20.0],"Liquidity score (1-10)":[8,9]}),num_rows="dynamic",use_container_width=True)
    inv_r=weighted_return(investments)
    st.metric("Weighted expected post-tax return",f"{inv_r*100:.2f}%")

payment=safe_surplus+annual_prepay/12
specs=[
    ("Only EMI",0.0,None),("Monthly prepayment",0.0,"monthly"),("Quarterly prepayment",0.0,"quarterly"),
    ("Annual prepayment",0.0,"annual"),("Invest everything",1.0,None),("50% invest + 50% prepay",0.5,"monthly"),
    ("Conservative blend",0.25,"monthly")]
results=[simulate(n,loan,rate,tenure_y*12,payment,usable_assets,inv_r,s,f,growth,leveraged) for n,s,f in specs]
baseline=results[0]

def score(r):
    if objective=="Close loan fastest": return -r.close_month
    if objective=="Maximise net worth": return r.net_worth
    if objective=="Lowest risk": return -r.risk*1e7+r.net_worth
    if objective=="Highest liquidity": return r.liquidity*1e7+r.net_worth
    return r.net_worth-r.interest*0.4-r.risk*100000

best=max(results,key=score)
with t4:
    st.markdown(f"<div class='best'><b>Recommended for “{objective}”:</b> {best.name}<br>Allocate {next(s for n,s,f in specs if n==best.name)*100:.0f}% of the calculated surplus to investments and the remainder to prepayment.</div>",unsafe_allow_html=True)
    table=pd.DataFrame([{"Strategy":r.name,"Total interest":r.interest,"Interest saved":baseline.interest-r.interest,"Loan closes in (years)":r.close_month/12,"Investment corpus (30y)":r.corpus,"Projected net worth":r.net_worth,"Liquidity / 10":r.liquidity,"Risk / 10":r.risk} for r in results]).sort_values("Projected net worth",ascending=False)
    st.dataframe(table.style.format({"Total interest":money,"Interest saved":money,"Loan closes in (years)":"{:.1f}","Investment corpus (30y)":money,"Projected net worth":money,"Liquidity / 10":"{:.1f}","Risk / 10":"{:.1f}"}),use_container_width=True)
    chosen=st.selectbox("View action plan",[r.name for r in results],index=[r.name for r in results].index(best.name))
    selected=next(r for r in results if r.name==chosen); schedule=pd.DataFrame(selected.rows)
    yearly=schedule[schedule.Month%12==0].copy(); yearly["Year"]=yearly.Month//12
    fig=px.line(yearly,x="Year",y=["Loan outstanding","Investment corpus"],title=f"{chosen}: loan and wealth path")
    st.plotly_chart(fig,use_container_width=True)
    first=schedule.head(120).copy(); first["Date/action"]=first.Month.apply(lambda m:f"Month {m}")
    st.dataframe(first[["Date/action","Investment","Prepayment","Interest","Loan outstanding"]].style.format({c:money for c in ["Investment","Prepayment","Interest","Loan outstanding"]}),use_container_width=True)
    def build_excel_report():
        output=io.BytesIO()
        inputs=pd.DataFrame([
            ["Selected objective",objective,"Controls which strategy is recommended"],
            ["Recommended strategy",best.name,"Highest-ranked strategy for the selected objective"],
            ["Monthly household income",total_income,"Salary plus spouse/other income"],
            ["Monthly expenses",total_exp,"Total entered recurring expenses"],
            ["Other monthly EMIs",existing_emi,"Debt repayments excluding this home loan"],
            ["Safety buffer %",buffer_pct,"Protected portion of income"],
            ["Calculated safe monthly surplus",safe_surplus,"Income − expenses − other EMIs − safety buffer"],
            ["Property value",property_value,"Entered property price"],
            ["Registration and other charges",charges,"Purchase costs outside property price"],
            ["Home loan amount",loan,"Opening loan principal"],
            ["Home loan interest rate %",rate,"Annual rate used on monthly reducing balance"],
            ["Remaining tenure years",tenure_y,"Remaining contractual loan period"],
            ["Calculated EMI",base_emi,"Monthly reducing-balance EMI"],
            ["Expected post-tax investment return %",inv_r*100,"Weighted return after entered tax assumptions"],
            ["Annual income growth %",growth,"Applied to future monthly capacity"],
            ["Loan proceeds invested","Yes" if leveraged else "No","Normally No for a home loan"],
        ],columns=["Input / output","Value","How it affects the plan"])
        with pd.ExcelWriter(output,engine="openpyxl") as writer:
            inputs.to_excel(writer,sheet_name="Inputs & Assumptions",index=False,startrow=2)
            table.to_excel(writer,sheet_name="Strategy Comparison",index=False,startrow=2)
            expenses.to_excel(writer,sheet_name="Expense Details",index=False,startrow=2)
            assets.to_excel(writer,sheet_name="Asset Details",index=False,startrow=2)
            investments.to_excel(writer,sheet_name="Investment Details",index=False,startrow=2)
            for result in results:
                monthly=pd.DataFrame(result.rows)
                monthly.insert(1,"Calendar month",monthly["Month"].apply(lambda m:pd.Timestamp(loan_start)+pd.DateOffset(months=m-1)))
                monthly["Total payment this month"]=monthly["Scheduled EMI"]+monthly["Prepayment"]+monthly["Investment"]
                monthly["Net worth indicator"]=monthly["Investment corpus"]+(loan-monthly["Loan outstanding"])
                sheet_name=result.name[:31]
                monthly.to_excel(writer,sheet_name=sheet_name,index=False,startrow=2)
                ws=writer.book[sheet_name]
                ws["A1"]=f"Monthly action plan — {result.name}"
                ws["A2"]="Follow the Action column and update the calculator whenever income, expenses, loan rate or investment assumptions change."
            for ws in writer.book.worksheets:
                ws.freeze_panes="A4"
                ws.auto_filter.ref=f"A3:{get_column_letter(ws.max_column)}{ws.max_row}"
                ws.sheet_view.showGridLines=False
                if not ws["A1"].value: ws["A1"]=ws.title
                ws["A1"].font=Font(bold=True,size=16,color="174B3A")
                for cell in ws[3]:
                    cell.font=Font(bold=True,color="FFFFFF")
                    cell.fill=PatternFill("solid",fgColor="174B3A")
                for column_cells in ws.columns:
                    letter=column_cells[0].column_letter
                    width=min(42,max(12,max(len(str(c.value or "")) for c in column_cells[:80])+2))
                    ws.column_dimensions[letter].width=width
                for row in ws.iter_rows():
                    for cell in row:
                        if isinstance(cell.value,(int,float)) and any(k in str(ws.cell(3,cell.column).value or "").lower() for k in ["amount","income","expense","emi","interest","principal","balance","prepayment","investment","corpus","worth","value","payment","capacity"]):
                            cell.number_format='₹#,##0.00;[Red]-₹#,##0.00'
                if ws.title not in ["Inputs & Assumptions","Strategy Comparison","Expense Details","Asset Details","Investment Details"]:
                    for cell in ws[4]:
                        if cell.value=="Calendar month":
                            for c in ws.iter_cols(min_col=cell.column,max_col=cell.column,min_row=4):
                                for x in c: x.number_format="mmm yyyy"
        output.seek(0)
        return output.getvalue()
    st.download_button("Download complete month-wise Excel report",data=build_excel_report(),file_name="wealthpath_month_wise_plan.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    if run_mc:
        rng=np.random.default_rng(42); sims=10000
        returns=np.clip(rng.normal(inv_r,0.05,sims),-0.20,0.30)
        corpus=np.array([usable_assets*(1+x/12)**360+payment*((1+x/12)**360-1)/(x/12) if abs(x)>1e-9 else usable_assets+payment*360 for x in returns])
        q=np.percentile(corpus,[10,50,90]); st.subheader("Monte Carlo range")
        a,b,c=st.columns(3); a.metric("Weak case (10th percentile)",money(q[0])); b.metric("Expected case (median)",money(q[1])); c.metric("Strong case (90th percentile)",money(q[2]))

st.divider()
st.caption("Educational planning tool—not personalised financial advice. Review taxes, prepayment rules, floating rates and market assumptions with qualified professionals.")
