# Personal Finance Advisor Bot — AI-Powered Financial Management System

A full-stack, intelligent web application designed to help individuals, students, freelancers, and households gain clarity and control over their finances. The system combines modern financial tracking with **Google Gemini AI** and a robust **Rule-Based Fallback Engine** to deliver personalized budgets, spending forensics, automated savings targets, and interactive financial advisory.

---

## 🌟 Key Features

### 1. Specialized Financial Modes
- **College Student Mode**: Track monthly allowances, weekly spending pacing, college categories (canteen, campus transit, books, entertainment), and burn-rate warnings.
- **Freelancer Mode**: Adapt to variable project payouts, calculate safe spending baselines, track tax-deductible business costs, and maintain emergency buffers.
- **Household Mode**: Manage shared family groceries, rent, utilities, and joint savings milestones under one roof.
- **Standard Mode**: Classic 50/30/20 wealth framework with proactive category limits and utilization alerts.

### 2. Income & Expense Management
- **Income Ledger**: Categorize sources (Salary, Freelancing, Business, Allowance, Investments, Other), recurring monthly toggle, and inflow metrics.
- **Expense Tracking**: Fast expense logging across 12 categories, payment methods (UPI, Cards, Cash, Net Banking), notes, and work-related tax tags.
- **Unified Transaction Ledger**: Real-time search, category filtering, date-range filtering, and multi-directional sorting (Date, Amount).
- **Periodic Summaries**: Instant visibility into daily spending, rolling 7-day totals, and monthly burn.

### 3. Smart Budget Planner
- **Personalized Budget Generator**: Synthesizes monthly income, previous spending habits, and active financial mode to build realistic, tailored category caps.
- **Budget Discipline Tracking**: Real-time progress bars with three status indicators:
  - 🟢 **On Track** (< 80% utilized)
  - 🟡 **Warning Alert** (80% – 99% utilized)
  - 🔴 **Over Budget** (≥ 100% utilized)
- **1-Click Apply**: Commit generated budgets directly to your account with a single click.

### 4. AI Financial Advisor (Google Gemini + Fallback Engine)
- **Conversational Chatbot**: Chat naturally with an assistant that queries your real financial records (e.g., *"How much did I spend this month?"*, *"Where is most of my money going?"*, *"How can I save ₹2,000 next month?"*).
- **Spending Forensic Analysis**: Pinpoints money leaks, discretionary-to-essential ratios, and unusual surges.
- **Savings Growth Tactics**: Milestone pacing and micro-savings strategies.
- **Monthly Health Report Card**: Executive grade (A/B/C/D), key observations, and next-month directives.
- **Zero-Setup Fallback Guarantee**: If no Gemini API key is configured or network is unavailable, the application seamlessly activates its built-in rule-based intelligence engine.

### 5. Savings Goals & Contributions
- Target amounts and target completion dates.
- Contribution deposit ledger.
- Automated monthly required savings calculation to reach goals on schedule.

### 6. Reports & Data Exports
- Interactive **Chart.js** visualizations:
  - 6-Month Income vs. Expense Trend Bar Chart
  - Expense Category Doughnut Chart
  - Monthly Savings Velocity Line Chart
  - Budget Utilization Comparison Chart
- **Export to CSV**: Download transaction ledgers, budget caps, and savings goals into Excel-compatible CSVs.
- **Printable Monthly Statement**: High-contrast, clean print layout suitable for physical records.

### 7. Demo Data Seeder
- One-click **"Load Realistic Demo Data"** button in Settings / Dashboard to instantly populate transactions, budgets, and goals for academic grading or demonstrations without manual data entry.

---

## 🛠️ Technology Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.9+, Flask 3.1, Werkzeug, python-dotenv |
| **Database & ORM** | SQLite, Flask-SQLAlchemy |
| **Authentication** | Flask-Login (PBKDF2 SHA-256 secure password hashing) |
| **Form Security** | Flask-WTF, CSRF Protection, email-validator |
| **AI Integration** | Official Google GenAI Python SDK (`google-genai`), Gemini 2.5 Flash |
| **Frontend** | HTML5, CSS3, JavaScript, Bootstrap 5, Bootstrap Icons, Chart.js |
| **Testing** | pytest, pytest fixtures with in-memory database |

---

## 📁 Project Structure

```
Personal Finance Advisor Bot/
├── app.py                      # Application entrypoint & factory
├── config.py                   # Environment configuration & test setup
├── models.py                   # SQLAlchemy ORM models (User, Income, Expense, Budget, SavingsGoal, etc.)
├── forms.py                    # Flask-WTF form definitions and validators
├── requirements.txt            # Python dependencies
├── .env.example                # Environment variables template
├── .env                        # Active environment configuration
├── README.md                   # Documentation & setup guide
│
├── routes/                     # Blueprint modular route handlers
│   ├── __init__.py
│   ├── auth.py                 # Register, login, profile, settings, demo seeder
│   ├── dashboard.py            # Financial summary, mode switcher, alerts
│   ├── income.py               # Income CRUD & month filters
│   ├── expenses.py             # Expense CRUD & unified transaction search
│   ├── budgets.py              # Smart budget planner & limit manager
│   ├── savings.py              # Goals & deposit contributions
│   ├── reports.py              # Visual analytics & CSV downloads
│   └── ai_advisor.py           # Gemini chatbot API & advisory views
│
├── services/                   # Business logic layer
│   ├── __init__.py
│   ├── analytics_service.py    # Aggregate queries, metrics & alert triggers
│   ├── budget_service.py       # Smart budget algorithms tailored by mode
│   ├── gemini_service.py       # Gemini SDK client + rule-based fallback engine
│   └── report_service.py       # CSV generators & data exporters
│
├── static/
│   ├── css/
│   │   └── style.css           # Modern fintech design system
│   └── js/
│       ├── main.js             # Sidebar toggle & notifications
│       ├── charts.js           # Chart.js renderers
│       └── ai_advisor.js       # Live AI chatbot messaging
│
├── templates/                  # Jinja2 HTML templates
│   ├── base.html               # Responsive shell layout
│   ├── index.html              # Modern fintech landing page
│   ├── login.html              # Authentication sign in
│   ├── register.html           # Account registration with mode choice
│   ├── dashboard.html          # Executive financial dashboard
│   ├── income.html             # Inflow management
│   ├── income_edit.html        # Edit income
│   ├── expenses.html           # Outflow management
│   ├── expenses_edit.html      # Edit expense
│   ├── transactions.html       # Transaction search & filter table
│   ├── budgets.html            # Category spending limits & smart plan
│   ├── ai_advisor.html         # AI Chatbot & Strategy Hub
│   ├── savings.html            # Goals & deposits
│   ├── savings_edit.html       # Edit savings goal
│   ├── reports.html            # Charts & daily breakdown
│   ├── printable_summary.html  # Print-friendly monthly statement
│   ├── profile.html            # User account settings
│   ├── settings.html           # System preferences & demo data
│   ├── 404.html                # Not found handler
│   └── 500.html                # Server error handler
│
├── instance/
│   └── finance.db              # SQLite production database (auto-generated)
│
└── tests/                      # Automated test suite
    ├── conftest.py             # In-memory test fixtures
    ├── test_auth.py            # Authentication & session tests
    ├── test_income.py          # Income CRUD tests
    ├── test_expenses.py        # Expense & search filter tests
    ├── test_budgets.py         # Smart budget & student mode tests
    └── test_savings_and_ai.py  # Goals, deposits & AI fallback tests
```

---

## 🚀 Local Setup Instructions

Follow these simple steps to run the application in VS Code or any terminal:

### 1. Create a Virtual Environment
```bash
python3 -m venv venv
```

### 2. Activate the Virtual Environment
- **macOS / Linux**:
  ```bash
  source venv/bin/activate
  ```
- **Windows (Command Prompt)**:
  ```cmd
  venv\Scripts\activate.bat
  ```
- **Windows (PowerShell)**:
  ```powershell
  venv\Scripts\Activate.ps1
  ```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables
Copy `.env.example` to `.env` (a default `.env` is already provided):
```bash
cp .env.example .env
```
Inside `.env`:
```ini
FLASK_SECRET_KEY=your-secret-key-here
GEMINI_API_KEY=
GEMINI_MODEL=gemini-2.5-flash
DATABASE_URL=sqlite:///finance.db
DEFAULT_CURRENCY=₹
```

### 5. Running the Application
```bash
python app.py
```
The database (`instance/finance.db`) will be automatically created with all tables on first startup.

Open your browser and navigate to:
```
http://127.0.0.1:5000
```

---

## 🤖 Google Gemini AI Configuration

1. Visit [Google AI Studio](https://aistudio.google.com/) and generate a free API key.
2. Open `.env` and paste your key:
   ```ini
   GEMINI_API_KEY=AIzaSyYourActualKeyHere
   ```
3. Restart the Flask application.
4. The AI Advisor badge will switch from **"Rule-Based Fallback Engine Active"** to **"Gemini API Connected"**.

> **Note:** If you do not have an API key, the system remains 100% operational using the built-in rule-based financial advisory engine!

---

## 🧪 Running Automated Tests

Run the full suite of 16 tests using pytest:

```bash
pytest -v
```

All 16 test cases validate authentication, session isolation, income/expense CRUD, budget limits, smart budget formulas, and the AI chatbot fallback engine.

---

## 💡 Quick Demo Tip for Reviewers
1. Register an account and sign in.
2. Go to **Settings** (`/settings`) and click **"Load Realistic Demo Data"**.
3. Return to the **Dashboard** (`/dashboard`) to view populated charts, expense allocations, savings goals, and alerts.
4. Navigate to **AI Advisor** (`/ai-advisor`) and click any suggested question chip to test the chatbot!
