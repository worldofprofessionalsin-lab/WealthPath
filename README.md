# WealthPath Streamlit

Version 4.5 fixes CSV/JSON table restoration on current Streamlit releases by
separating imported table data from read-only data-editor widget state. It also
includes the strategy explanations and complete monthly property-funding and
cash trail introduced in version 4.4.

## Data import and backup

Open **Import, export or restore planner data** at the top of the app.

- Download the CSV template, edit only the `Value` column, and import it back.
- Export the current planner as CSV when bulk editing is useful.
- Export JSON for a complete backup. Importing it later restores all entered
  inputs, editable tables, dates, toggles, and the selected objective.
- Calculated results are regenerated after import so they remain consistent
  with the current calculation engine.

Backups download to the device used to access Streamlit. Streamlit Community
Cloud does not permanently store an individual user's planner data between
browser sessions, so download the JSON backup before clearing the app or
switching devices.

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
- Each monthly schedule separately shows the buyer's own contribution, the bank's loan contribution, total property payment, closing own-contribution fund, and closing cash balance.
- Conservative blend means 25% of available surplus is invested and 75% is used for monthly loan prepayment, after reserving required property contributions and protected liquidity.
- Each monthly schedule also shows the calendar month, action to take, EMI, interest, principal, prepayment, investment, closing loan balance, projected investment corpus, and net-worth indicator.
- Results are projections and market-linked returns are not guaranteed.
