# WealthPath Streamlit

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
streamlit run app.py
```

## Publish with Streamlit Community Cloud

1. Create a GitHub repository and upload `app.py`, `requirements.txt`, and the `.streamlit/config.toml` theme file. Keep the `.streamlit` folder name unchanged.
2. Open https://share.streamlit.io and choose **Create app**.
3. Select the repository, branch, and `app.py`, then deploy.

GitHub Pages cannot run Python. It would require rewriting the calculation engine in JavaScript. Streamlit is recommended for this calculator because it supports Python calculations, simulations, charts, and Excel downloads directly.

## Calculation model

- EMI uses the monthly reducing-balance formula.
- Safe surplus = household income − expenses − other EMIs − safety buffer.
- Strategies maintain separate monthly investment and prepayment cash flows.
- Existing assets are separately classified for property contribution and continued investment, preventing double use.
- Property and loan funding can be entered as multiple dated tranches; interest begins only when each loan tranche is disbursed.
- The planner calculates the monthly amount that must first be reserved for the own contribution, protects the chosen minimum cash balance, and allocates only the remaining surplus to investment or prepayment.
- Pre-EMI and full-EMI staged-disbursement methods are supported.
- Investment returns are weighted and reduced by the entered tax rate.
- EMI is redirected into investment after the loan closes.
- The Excel download contains inputs, property funding dates, contribution sources, contribution feasibility, year-end liquidity, strategy comparison, expense/asset/investment details, and a separate 360-month action schedule for every strategy.
- Each monthly schedule shows the calendar month, action to take, EMI, interest, principal, prepayment, investment, closing loan balance, projected investment corpus, and net-worth indicator.
- Results are projections and market-linked returns are not guaranteed.
