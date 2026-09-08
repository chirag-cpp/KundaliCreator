KUNDALI GENERATOR — WEB APP
===========================

DEPLOY (free, ~10 minutes, gives you a shareable URL)
-----------------------------------------------------
1. Create a GitHub repo and push all files in this zip to its root.
2. Go to share.streamlit.io, sign in with GitHub, click "New app".
3. Pick the repo, set main file = app.py, click Deploy.
4. Share the resulting URL with your friends. No install on their side.

Streamlit Cloud reads requirements.txt automatically and builds pyswisseph
from source on Linux — takes ~2 minutes on first deploy.

RESTRICTING ACCESS (optional)
-----------------------------
The URL is public by default. For a small group either:
  - Streamlit Cloud > app Settings > Sharing > invite specific emails, or
  - add a shared password via st.secrets (simplest for friends).

RUN LOCALLY
-----------
  pip install -r requirements.txt
  streamlit run app.py

CLI STILL WORKS
---------------
  python3 generate_kundali.py --dob 1990-05-15 --time 14:30 \
      --place "Ghaziabad" --country IN --name "Full Name"
  python3 generate_kundali.py --dob 1990-05-15 --time 14:30 \
      --lat 28.6654 --lon 77.4391 --tz Asia/Kolkata --place-label "Ghaziabad"

FILES
-----
app.py               Streamlit UI (form -> report -> download button)
generate_kundali.py  build_report() + CLI
core.py              ephemeris, panchanga, divisional charts, Jaimini
strength.py          Shadbala, Bhava Bala, Ashtakavarga
dasha.py             Vimshottari
tables.py            lookup data
requirements.txt     dependencies
