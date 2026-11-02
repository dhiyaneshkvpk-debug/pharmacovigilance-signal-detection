# PharmaGuard AI
### AI-Enabled Pharmacovigilance & Drug Safety Analytics Platform

[![Python](https://img.shields.io/badge/Python-3.x-blue?logo=python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-REST-092E20?logo=django)](https://www.djangoproject.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?logo=streamlit)](https://streamlit.io/)
[![MySQL](https://img.shields.io/badge/Database-MySQL-4479A1?logo=mysql)](https://www.mysql.com/)
[![Pandas](https://img.shields.io/badge/Data-Pandas-150458?logo=pandas)](https://pandas.pydata.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

**PharmaGuard AI** is an end-to-end pharmacovigilance and drug safety analytics project designed to process FDA Adverse Event Reporting System (FAERS) data, identify potential drug–adverse event safety signals, and present analytical evidence through interactive dashboards and a Django REST API.

The project combines data engineering, statistical signal detection, healthcare analytics, database management, and web application development to support structured exploration of post-marketing drug safety information.

---

## Project Overview

Pharmacovigilance plays an important role in monitoring the safety of medicines after they enter the market. Large-scale adverse event reporting databases provide valuable information, but extracting meaningful patterns requires systematic data processing and statistical analysis.

PharmaGuard AI addresses this challenge through a structured analytical pipeline and an interactive application.

The project extends an FDA FAERS signal detection pipeline into a broader healthcare analytics platform.

### Key Objectives

- Process and validate FDA FAERS datasets.
- Identify potential drug–adverse event associations.
- Calculate statistical disproportionality measures.
- Explore drug safety evidence through interactive dashboards.
- Organize analytical outputs using a relational database.
- Expose application functionality through Django REST Framework.
- Present methodology, validation, and analytical limitations transparently.

---

## Key Features

### 1. Pharmacovigilance Data Processing

- Structured processing of FDA FAERS datasets.
- Data cleaning, transformation, and validation.
- Drug and adverse event data integration.
- Case-level and drug–reaction analysis.
- Reproducible Python-based processing scripts.

### 2. Statistical Safety Signal Detection

The analytical pipeline uses established disproportionality methods to identify potential safety signals.

**Statistical methods include:**

- Proportional Reporting Ratio (PRR)
- Reporting Odds Ratio (ROR)
- Confidence intervals
- Chi-square statistical testing
- Contingency table analysis

These methods help identify disproportionate reporting patterns that may warrant further investigation.

### 3. Interactive Streamlit Dashboard

The application includes multiple analytical pages:

| Module | Description |
|---|---|
| Safety Signal Explorer | Explore potential drug–adverse event signals |
| Drug Safety Profile | Examine drug-level safety information |
| Evidence Analytics | Review aggregated analytical evidence |
| Methodology & Validation | Understand analytical methods and validation |

### 4. Django REST Framework Backend

The Django application provides the backend structure for PharmaGuard AI.

Implemented components include:

- Django application architecture
- Data models
- Serializers
- API views and URL routing
- Database integration
- Management commands for data import and analytics refresh

### 5. Database Management

MySQL is used to organize structured application data and support analytical workflows.

The project includes database models and supporting data import functionality for pharmacovigilance information.

---

## Technology Stack

| Category | Technologies |
|---|---|
| Programming | Python, SQL |
| Data Analysis | Pandas, NumPy |
| Statistical Analysis | SciPy |
| Backend Development | Django, Django REST Framework |
| Dashboard Development | Streamlit |
| Database | MySQL |
| Frontend | HTML, CSS, JavaScript |
| Data Visualization | Streamlit visualizations |
| Version Control | Git, GitHub |

---

## Project Architecture

```text
                 FDA FAERS DATA
                       |
                       v
             DATA PROCESSING PIPELINE
                       |
                       v
              DATA CLEANING & VALIDATION
                       |
                       v
            STATISTICAL SIGNAL DETECTION
                       |
                       v
              ANALYTICAL OUTPUTS
                       |
                       v
                MYSQL DATABASE
                       |
             +---------+---------+
             |                   |
             v                   v
       DJANGO REST API      STREAMLIT APP
             |                   |
             v                   v
       BACKEND SERVICES    ANALYTICS DASHBOARD
             |                   |
             +---------+---------+
                       |
                       v
              DRUG SAFETY EVIDENCE
```

---

## Repository Structure

```text
pharmacovigilance-signal-detection/
│
├── Data/
│
├── dashboard/
│   └── Data/
│
├── output/
│
├── src/
│
├── pipeline_v2/
│   └── output/
│
├── Django RestAPI/
│   │
│   ├── config/
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   │
│   ├── PharmaGuard_AI/
│   │   ├── migrations/
│   │   ├── management/
│   │   ├── static/
│   │   ├── Templates/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   └── urls.py
│   │
│   ├── Pipeline_v2/
│   │
│   ├── pages/
│   │   ├── 02_Safety_Signal_Explorer.py
│   │   ├── 03_Drug_Safety_Profile.py
│   │   ├── 04_Evidence_Analytics.py
│   │   └── 05_Methodology_Validation.py
│   │
│   ├── dashboard.py
│   ├── import_faers_v7.py
│   └── manage.py
│
├── .gitignore
└── README.md
```

---

## Installation & Setup

### Prerequisites

Ensure that the following tools are installed:

- Python 3.x
- MySQL Server
- Git
- pip

### 1. Clone the Repository

```bash
git clone https://github.com/dhiyaneshkvpk-debug/pharmacovigilance-signal-detection.git

cd pharmacovigilance-signal-detection
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate the environment on Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

Install the project's required Python packages.

If a requirements file is available:

```bash
pip install -r requirements.txt
```

Otherwise, install the dependencies used by the relevant application modules.

### 4. Configure Environment Variables

Configure the following environment variables before starting Django:

```env
DJANGO_SECRET_KEY=your-secret-key
DJANGO_DEBUG=True
DB_PASSWORD=your-database-password
```

Configure the database name, username, host, and port according to your local MySQL setup.

**Security:** Never upload `.env` files, passwords, database credentials, or Django secret keys to GitHub.

### 5. Run Database Migrations

Navigate to the Django project directory:

```bash
cd "Django RestAPI"
```

Run:

```bash
python manage.py migrate
```

### 6. Start the Django Development Server

```bash
python manage.py runserver
```

The local development server will be available at:

```text
http://127.0.0.1:8000/
```

### 7. Launch the Streamlit Dashboard

Open another terminal, activate the virtual environment, and navigate to the application directory.

Run:

```bash
streamlit run dashboard.py
```

The dashboard will start on the local Streamlit address displayed in your terminal.

**Note:** Application startup requires the relevant datasets, dependencies, and database configuration. The repository excludes certain generated datasets and local files, so these may need to be prepared separately.

---

## Analytical Methodology

The project uses statistical disproportionality analysis to explore potential drug safety signals.

| Method | Purpose |
|---|---|
| PRR | Measures disproportional reporting of an event for a drug |
| ROR | Estimates the odds of reporting an event for a drug relative to other drugs |
| Confidence Interval | Evaluates statistical uncertainty |
| Chi-square Test | Assesses departure from expected reporting patterns |

The analytical results are intended for exploratory pharmacovigilance research and should be interpreted with appropriate caution.

---

## Important Limitations

PharmaGuard AI is an analytical and educational portfolio project, not a clinical decision-support system.

- FAERS contains spontaneous adverse event reports and is subject to under-reporting, duplicate reporting, and reporting bias.
- A reported adverse event does not establish that a medicine caused the event.
- Disproportionality measures identify potential statistical signals, not confirmed adverse drug reactions.
- Confounding factors and missing information may affect analytical findings.
- Clinical validation and further epidemiological investigation are necessary before drawing conclusions.

---

## Future Enhancements

Potential future development includes:

- Machine learning-based adverse event classification.
- Natural language processing for adverse event report analysis.
- Advanced drug safety trend monitoring.
- Automated signal prioritization.
- Expanded REST API documentation.
- Automated data refresh and validation workflows.
- Deployment of the application to a cloud environment.

---

## About the Developer

**Dhiyanesh E**

M.Sc. Biotechnology | Healthcare Analytics | Data Analytics | Python

I am interested in combining life sciences, data analytics, and software development to solve practical problems in healthcare and pharmaceutical research.

**Technical Interests:**
- Healthcare Data Analytics
- Pharmacovigilance
- Python & SQL
- Statistical Analysis
- Power BI & Data Visualization
- Django REST Framework
- Machine Learning

### Connect

- GitHub: [dhiyaneshkvpk-debug](https://github.com/dhiyaneshkvpk-debug)

---

## Disclaimer

This project is developed for educational, research, and portfolio demonstration purposes. It is not intended to replace professional medical judgment, regulatory assessment, or clinical safety evaluation.

**PharmaGuard AI — Turning pharmacovigilance data into structured safety insights.**
