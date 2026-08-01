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
- Existing assets are counted only to the percentage marked available.
- Investment returns are weighted and reduced by the entered tax rate.
- EMI is redirected into investment after the loan closes.
- The Excel download contains inputs, strategy comparison, expense/asset/investment details, and a separate 360-month action schedule for every strategy.
- Each monthly schedule shows the calendar month, action to take, EMI, interest, principal, prepayment, investment, closing loan balance, projected investment corpus, and net-worth indicator.
- Results are projections and market-linked returns are not guaranteed.
