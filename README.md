# stock-dashboard

Streamlit-based family wealth cockpit with a cinematic neon/glassmorphic theme. The live UI, hero banner, KPI grid, and charts all live in `dashboard.py` (this file is the Streamlit entry point). Recent styling changes are already committed to this branch.

## Run locally
1. Install Python 3.9+.
2. Install dependencies: `pip install -r requirements.txt`.
3. Launch the app: `streamlit run dashboard.py`.

Streamlit will print a local URL to open the dashboard in your browser.

## The super-simple way to make your live app look fancy
Think of this as three big buttons you press in order. No coding—just copy/paste the commands.

1. **Tell this folder where your GitHub is (one time).**
   - Command to paste: `git remote add origin <your-github-url>`
   - Replace `<your-github-url>` with the link to your repo (the same link you see in your browser’s address bar on GitHub).

2. **Send the fancy code up to GitHub.**
   - Command to paste: `git push origin work`
   - After it finishes, refresh your GitHub page. You should see `dashboard.py` now has **620+ lines** (longer than the old ~496-line file).

3. **Press the redeploy button on Streamlit.**
   - On Streamlit Community Cloud, open your app page, click the **Rerun** or **Deploy** button. This makes Streamlit pull the new code you just pushed.
   - Reload your app. The neon/glassmorphic look should appear.

### What to check if something looks wrong
- In GitHub, does `dashboard.py` show ~620 lines? If not, repeat steps 1–2.
- In Streamlit, did you press **Rerun/Deploy** after pushing? If not, do step 3.

### Extra reassurance (optional)
- Show the most recent commit message: `git log -1 --oneline` (look for the neon/restyle message).
- Count lines locally: `wc -l dashboard.py` (should say around 620).
