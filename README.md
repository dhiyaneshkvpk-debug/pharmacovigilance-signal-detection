# PharmaGuard AI (simple version)

**Goal:** find which medicines are reported with unusual side effects, using the US FDA's
adverse-event database (FAERS).

```
raw zip files -> STEP 1 clean -> STEP 2 statistics -> STEP 3 machine learning -> Streamlit dashboard
                                         |
                                         +--> signals.csv -> Django REST API (database + JSON)
```

## The idea in 2 minutes (read this first)

- **FAERS** = reports of side effects sent to the FDA by doctors, patients and companies.
- A **case** is one report. A **drug-reaction pair** is e.g. *DEPO-PROVERA -> MENINGIOMA*.
- **Question:** is a reaction reported *more often* with one drug than with all other drugs?
- **ROR (Reporting Odds Ratio)** answers it. ROR = 1 means no link, ROR = 10 means 10x more often.
- **Signal rule:** ROR >= 2 **and** the lower end of the 95% confidence interval is above 1.
- A signal is a **hypothesis**, not proof. People may report a drug more because of news or lawsuits.

## Folder

```
data/raw/          <- put faers_ascii_2026q1.zip and faers_ascii_2026q2.zip here
helpers.py         the ROR calculation (used by step 2 and 3)
step1_data_processing.py
step2_statistical_analysis.py
step3_machine_learning.py
app.py             Streamlit dashboard
django_api/        Django REST API (reads outputs/signals.csv)
  manage.py
  config/          settings.py, urls.py
  drugsafety/      models.py, views.py, serializers.py, urls.py, tests.py
```

## How to run (Windows PowerShell, inside VS Code)

**1. Open the right folder.** `dir` must show `app.py` and `helpers.py`. If not, `cd` into the folder.

**2. Create the environment and install**
```powershell
py -m venv venv
venv\Scripts\activate
python -m pip install -r requirements.txt
```
Checkpoint: the prompt starts with `(venv)`.

**3. Copy the two zip files into `data\raw\`.** Check: `dir data\raw`

**4. Step 1 - data processing** (about 30 seconds)
```powershell
python step1_data_processing.py
```
Checkpoint: about **792,000 unique cases**, and `CHECK 1`, `CHECK 2`, `CHECK 3` all say `True`.

**5. Step 2 - statistical analysis** (about 20 seconds)
```powershell
python step2_statistical_analysis.py
```
Checkpoint: `Drug-reaction pairs` about **147,000**, about **5,000 Strong** signals,
and DEPO-PROVERA / MENINGIOMA at the top. Both `CHECK` lines say `True`.

**6. Step 3 - machine learning** (about 30 seconds)
```powershell
python step3_machine_learning.py
```
Checkpoint: the best model's `roc_auc` (about 0.80) is **higher than the baseline** (about 0.67).

**7. Dashboard**
```powershell
streamlit run app.py
```
Your browser opens at http://localhost:8501. Stop it with `Ctrl+C`.
(If asked for an email the first time, just press Enter.)

**One-click:** after step 2 of the list above and copying the zips, double-click `run_all.bat`.

## Django REST API (the backend part)

**Idea:** the dashboard reads CSV files. A real application usually keeps data in a **database** and lets
other programs ask for it through an **API** (a web address that returns JSON). Django stores the
results in a database and Django REST Framework turns them into API endpoints.

```
outputs/signals.csv --load_signals--> database (db.sqlite3) --views--> JSON at /api/...
```

**Run it** (after steps 1-3 so `outputs\signals.csv` exists; open a second terminal, activate `venv`)
```powershell
cd django_api
python manage.py migrate
python manage.py load_signals
python manage.py runserver
```
Checkpoint: `load_signals` prints `Loaded 147,212 rows into the database` and the server says
`Starting development server at http://127.0.0.1:8000/`. Stop it with `Ctrl+C`.
(Or double-click `run_api.bat`.)

**Try these in your browser**

| URL | What you get |
|---|---|
| http://127.0.0.1:8000/api/ | welcome message and the list of endpoints |
| http://127.0.0.1:8000/api/summary/ | total pairs and counts by strength |
| http://127.0.0.1:8000/api/signals/?strength=strong | Strong signals, best first (20 per page) |
| http://127.0.0.1:8000/api/signals/?drug=dupixent&reaction=pruritus | search by drug and reaction |
| http://127.0.0.1:8000/api/signals/?min_cases=100&page=2&page_size=10 | filter and pages |
| http://127.0.0.1:8000/api/drugs/DEPO-PROVERA/ | profile of one drug |

Checkpoint: `/api/drugs/DEPO-PROVERA/` shows `strong_signals: 3` with MENINGIOMA first.
Wrong input, e.g. `?strength=huge`, returns a clear error message instead of crashing.

**Run the API tests:** `python manage.py test` (inside `django_api`). Checkpoint: `Ran 8 tests ... OK`.

**Which file does what**

| File | Job |
|---|---|
| `models.py` | describes the database table (one row = one drug-reaction pair) |
| `management/commands/load_signals.py` | copies `signals.csv` into the table |
| `views.py` | the 4 functions that answer the URLs |
| `serializers.py` | turns a database row into JSON |
| `urls.py` | connects each URL to its view |
| `admin.py` | lets you browse the data at http://127.0.0.1:8000/admin/ (needs `python manage.py createsuperuser`) |

## What each step does

| Step | Skill | What happens |
|---|---|---|
| 1 | Data processing | read zips, remove deleted cases, keep latest version of each case, keep primary-suspect drug, clean text, convert age to years, save CSVs |
| 2 | Statistics | descriptive stats (age, sex, top drugs) + ROR, PRR, confidence interval, chi-square test, p-value for every pair |
| 3 | Machine learning | use Quarter 1 numbers to predict which pairs are signals in Quarter 2; compare 3 models with a baseline |
| App | Dashboard | 6 pages: overview, top drugs, signal explorer, drug profile, ML results, about |
| Django | Backend API | stores `signals.csv` in a database and serves it as JSON (4 endpoints) |

## Words you will see

| Word | Meaning |
|---|---|
| a, b, c, d | the 4 numbers of the 2x2 table (cases with/without the drug and the reaction) |
| CI (confidence interval) | the range the true ROR probably lies in; we rank by its **lower** end |
| p-value | chance of seeing this result if there was no real link (`< 0.001` = very unlikely) |
| Baseline | a simple guess the model must beat |
| ROC-AUC | model score: 0.5 = guessing, 1.0 = perfect |
| Data leakage | letting the model see the answer; we avoid it by using Quarter 1 for features, Quarter 2 for the answer |

## Try it yourself (practice)

1. In `helpers.py` change `min_cases=3` to `5` in step 2, rerun. How many pairs remain?
2. In `helpers.py` change the Strong rule from `a >= 20` to `a >= 50`. How many Strong signals now?
3. In `step3_machine_learning.py` change `n_estimators=200` to `50`. Does the Random Forest score change?
4. Add a word to `IGNORE_WORDS` in `helpers.py` and see which pairs become "Excluded".
5. In `django_api/drugsafety/views.py`, change the default `page_size` from `20` to `5` and reload `/api/signals/`.
6. Add a new filter `?max_p=0.01` to `signal_list` (hint: copy the `min_cases` lines and use `p_value__lte`).

## Common problems

- **`requirements.txt` not found** - you are in the wrong folder; `cd` into the folder with `app.py`.
- **`No zip files found`** - the zips must be inside `data\raw\`.
- **`streamlit` not recognized** - run `venv\Scripts\activate` first.
- **Dashboard says "Results not found"** - run steps 1, 2 and 3 first.
- Run every command from the project folder (not from inside `data`). Django commands run inside `django_api`.
- **Django: `no such table`** - run `python manage.py migrate` first.
- **Django: `File not found ... signals.csv`** - run step 2 first.
- **Django: `load_signals` is slow** - it loads 147,000 rows; about 15 seconds is normal.

## How to explain it in an interview

"I cleaned 800,000 FDA adverse-event reports with pandas, calculated Reporting Odds Ratios with
confidence intervals and chi-square tests to detect drug-safety signals, then trained models on
Quarter 1 statistics to predict Quarter 2 signals, which beat a simple baseline (ROC-AUC 0.80 vs 0.67).
I split the data by drug and by time to avoid data leakage, and I built a Streamlit dashboard.
I stored the results in a database and exposed them through a Django REST API with filtering, pagination,
validation and unit tests. I know FAERS signals are hypotheses, not proof of causation."
