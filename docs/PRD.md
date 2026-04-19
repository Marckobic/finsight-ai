# **📄 FinSight.ai — Product Requirements Document (PRD v1.2)**

---

## **1\. 🚀 Product Vision**

FinSight.ai is an AI-powered financial decision engine that transforms raw financial data into actionable, simulated, and adaptive strategies that improve real user financial outcomes.

Unlike traditional fintech applications focused on dashboards, tracking, or insights, FinSight is a decision system that actively helps users make better financial decisions over time.

---

## **2\. 🎯 Problem Statement**

Users in the US already have access to financial data through banking apps, fintech tools, and dashboards.

However:

* Financial data is fragmented and passive  
* Insights do not reliably translate into action  
* Users struggle to make consistent financial decisions  
* Existing tools are reactive rather than adaptive

**Core Problem:**  
Users understand their financial situation but fail to systematically improve it.

---

## **3\. 💡 Product Thesis**

The next generation of financial products will not be dashboards — they will be decision systems.

FinSight bridges the gap between:

* Financial awareness → Financial action  
* Static insights → Dynamic decision-making  
* Passive tracking → Adaptive optimization

---

## **4\. 🎯 Target Users (US Market)**

### **Primary Segment**

* Age: 25–40  
* Income: $60k–$200k  
* Professionals / early-stage founders  
* Users with financial goals (savings, debt reduction, home purchase)

### **Behavioral Traits**

* Financially aware but inconsistent execution  
* Overwhelmed by financial decisions  
* Distrust traditional financial advisors  
* Want clarity, control, and actionable guidance

### **4.3 User Personas**

Persona 1 — The Early-Career Optimizer

**Test question:** Can FinSight accelerate growth?

1\. Profile

Age: 26–30  
Income: $65k–$90k/year (stable, salaried)  
Context: 2–4 years into first professional role. No dependents. Renting. Financially curious but lacks a structured system. Has savings but no clear optimization strategy.

2\. Financial State

Income: $5,000–$7,500/month take-home  
Fixed expenses: $1,800–$2,500/month (rent, subscriptions, loan payments)  
Variable expenses: $800–$1,500/month (dining, lifestyle, travel)  
Savings balance: $5,000–$20,000  
Volatility: Low — income is predictable, expenses are largely controllable

3\. Behavioral Patterns

Action tendency: High — willing to act on recommendations quickly  
Discipline: Moderate — motivated in short bursts, inconsistent over months  
Risk attitude: Moderate-to-high — open to trade-offs if the upside is clear and quantified  
Engagement style: Responds to progress metrics and milestone feedback; drops off when feedback is absent

4\. Core Problem

Has disposable income and financial intent but no decision system. Money sits in a checking account earning nothing. Goal timelines are vague ("save more," "build an emergency fund"). Without structure, optimization never happens — awareness without action.

5\. Failure Modes

\- Sets a savings goal, makes progress for 2–3 weeks, then reverts to baseline spending when motivation fades  
\- Over-optimizes in one category (e.g., cuts dining) while ignoring larger inefficiencies (e.g., underutilized subscriptions, low savings rate)  
\- Has no mechanism to connect daily spending decisions to long-term goal trajectory — the feedback loop is invisible  
\- Abandons financial tools after 2–4 weeks when the novelty wears off and no new value is delivered

6\. How FinSight Helps

\- Baseline projection (Screen 4\) makes the cost of inaction concrete and visceral — seeing "you'll reach your goal in 18 months at current rate" is a forcing function  
\- Scenario simulation (Screen 6\) quantifies the upside of small changes — "cutting $150/month in dining gets you there 3 months sooner" is actionable in a way that generic advice is not  
\- Weekly check-in cadence (Screen 8\) replaces motivation with structure — the system creates accountability the user cannot self-generate  
\- EWMA adherence model adapts to realistic compliance (70–80% range) rather than assuming perfect execution

7\. Scenario Sensitivity

🔥 Most responsive to: discretionary spending reduction scenarios (dining, lifestyle, subscriptions)  
Key simulation: "What if I increase my savings contribution by $300/month?" — shows compounding effect on goal ETA  
Critical adherence category: variable expenses (food/lifestyle) — adherence defaults 0.5–0.7 are accurate for this persona  
Scenario that creates the most behavioral change: side-by-side baseline vs. optimized comparison on Screen 6 — the delta visualization is the primary conversion moment

Persona 2 — The Constrained Planner

**Test question:** Can FinSight optimize under constraints?

1\. Profile

Age: 33–40  
Income: $90k–$150k/year (stable, dual or single income household)  
Context: Married, 1–2 children. Homeowner or actively saving for home purchase. Financial life is complex — multiple obligations, competing goals, limited discretionary slack. Wants optimization but has few obvious levers.

2\. Financial State

Income: $7,500–$12,500/month take-home (household)  
Fixed expenses: $4,500–$7,000/month (mortgage/rent, childcare, insurance, loans)  
Variable expenses: $1,500–$2,500/month (groceries, transport, family lifestyle)  
Savings balance: $20,000–$80,000  
Volatility: Low-to-medium — income is stable but expenses fluctuate with family events, medical costs, school fees

3\. Behavioral Patterns

Action tendency: Moderate — willing to act but needs high confidence that the recommendation is safe given obligations  
Discipline: High — follows through when committed, but needs the plan to be realistic within constraints  
Risk attitude: Low-to-moderate — conservative; loss aversion is high; prefers certainty over upside  
Engagement style: Responds to constraint-aware recommendations; disengages if system ignores fixed obligations or suggests unrealistic cuts

4\. Core Problem

The financial picture is complex but the optimization space is narrow. Most of the budget is committed to non-negotiable obligations. The user knows they need to optimize but cannot identify where — and generic advice ("spend less on dining") is insulting given the reality of their financial life. Decision fatigue is high. The problem is not motivation — it is finding real leverage within a constrained system.

5\. Failure Modes

\- Receives generic recommendations that ignore fixed obligations (e.g., "cut subscriptions" when subscriptions are $40/month of a $7,000 expense base) — immediately loses trust and disengages  
\- Tries to optimize one goal (e.g., emergency fund) while another degrades (e.g., retirement contribution drops) — no system to manage competing goal trade-offs  
\- Over-saves in high-anxiety periods (e.g., after a large expense) then under-saves the following month — behavior is reactive, not strategic  
\- Abandons financial planning tools because they feel built for simpler financial lives

6\. How FinSight Helps

\- Manual financial snapshot (Screen 3\) captures the full expense picture including fixed obligations — the baseline is accurate to their actual constraints, not a simplified model  
\- Scenario engine surfaces only realistic levers — recommendations are bounded by the user's actual cashflow, not theoretical optima  
\- Multi-goal awareness: goal setup (Screen 2\) allows definition of primary and secondary goals; scenario simulations show impact on both  
\- Adherence model is critical for this persona — the system assumes partial compliance (50–70% range for variable categories) and builds realistic projections rather than best-case outcomes  
\- Low-risk scenario framing ("What if you redirected $200/month from variable expenses?") feels safe and testable rather than threatening

7\. Scenario Sensitivity

🔥 Most responsive to: fixed expense optimization scenarios (refinancing, subscription audit, insurance review) and savings rate micro-adjustments  
Key simulation: "What if you increased your monthly savings contribution by $200?" — small number, meaningful ETA delta, low perceived risk  
Critical adherence category: savings increase (defaults 0.6–0.8) — this persona tends to execute savings changes more reliably than lifestyle changes  
Scenario that creates the most behavioral change: constraint-aware baseline (Screen 4\) showing exactly how much discretionary slack exists — many users in this persona underestimate their actual margin  
Red flag scenario: any simulation that requires cutting fixed expenses — system should deprioritize these and focus on variable and savings categories

Persona 3 — The Volatile Earner

**Test question:** Can FinSight handle uncertainty?

1\. Profile

Age: 28–38  
Income: $60k–$200k/year (highly variable — freelance, early-stage founder, commission-based, contract worker)  
Context: No stable paycheck. Income can swing ±50% month-to-month. Financial planning feels impossible because the inputs keep changing. May have periods of high income followed by dry spells. Savings behavior is feast-or-famine.

2\. Financial State

Income: $3,000–$16,000/month (wide variance, unpredictable timing)  
Fixed expenses: $2,000–$4,000/month (lean by necessity — variable earners tend to minimize fixed commitments)  
Variable expenses: $1,000–$3,000/month (expands in high-income months, contracts in low-income months)  
Savings balance: $5,000–$50,000 (often lumpy — large deposits followed by drawdowns)  
Volatility: High — both income and expenses are unpredictable; standard monthly models break down

3\. Behavioral Patterns

Action tendency: High in high-income periods, low in low-income periods — motivation is income-correlated  
Discipline: Low-to-moderate — irregular income makes consistent behavior structurally difficult, not just a willpower failure  
Risk attitude: High — accustomed to uncertainty; comfortable with probabilistic framing  
Engagement style: Responds to scenario ranges and confidence intervals rather than single-point projections; distrusts tools that assume stable inputs

4\. Core Problem

Standard financial planning assumes stable monthly income. This persona's income is not stable — it is a distribution. Every financial tool they've tried has either broken on irregular input or produced projections so optimistic they're useless. The core problem is that uncertainty is not modeled — it is ignored. FinSight's probabilistic adherence model and scenario engine are structurally suited to this problem in a way no standard tool is.

5\. Failure Modes

\- Inputs a high-income month as the baseline → system produces an over-optimistic projection → user over-spends → dry spell hits → plan collapses  
\- Uses a low-income month as the baseline → system produces an overly conservative projection → user disengages because the goal feels unreachable  
\- No mechanism to model income variance — existing tools produce a single timeline based on a single income figure, which is structurally wrong for this persona  
\- High-income windfalls are not captured as savings opportunities — money gets spent because there is no real-time system to redirect it  
\- Stops using financial tools entirely during low-income periods because "the plan doesn't apply right now" — re-engagement never happens

6\. How FinSight Helps

\- Financial snapshot (Screen 3\) should be updated frequently — the "Update My Finances" CTA on Screen 8 is critical for this persona; monthly refreshes are expected behavior  
\- Scenario engine's adherence model is the key differentiator: probabilistic outputs with confidence intervals reflect income uncertainty naturally — the system doesn't pretend to know exactly when the goal will be reached  
\- Scenario simulation (Screen 6\) with the adherence slider maps directly to income uncertainty — "at 50% effort" effectively models a mixed-income period  
\- Low-income period mode: when updated snapshot shows negative cashflow, system re-runs AI strategy focused on expense minimization rather than savings optimization  
\- High-income windfall scenario: system should detect when income spike occurs (via snapshot update) and surface a dedicated scenario: "You have $X more than usual this month. Here's what to do with it."  
\- EWMA feedback loop adapts quickly to behavioral changes because α \= 0.3 weights recent behavior heavily — critical for a persona whose behavior changes month to month

7\. Scenario Sensitivity

🔥 Most responsive to: income variance scenarios, windfall allocation simulations, and minimum-viable savings scenarios for low-income periods  
Key simulation: "What if this month's income is 30% lower than usual?" — stress-test scenario that builds trust by showing the system understands their reality  
Critical adherence category: savings increase has lowest adherence for this persona (0.3–0.5 range in low-income months) — system must use conservative defaults  
Scenario that creates the most behavioral change: windfall detection \+ real-time redirection recommendation — "You earned $3,000 more than your baseline this month. Redirect $1,500 to your goal and reach it 4 months sooner."  
Red flag scenario: any single-point projection presented as certain — this persona will immediately distrust and disengage; all projections must include range language ("between 8 and 14 months")

---

## **5\. 🚀 MVP Objective**

Build a system that converts financial data into:

* Actionable recommendations  
* Simulated outcomes  
* Adaptive strategies based on user behavior

Success is defined by measurable improvement in user financial outcomes.

---

## **6\. 🧩 Core User Flow**

1. User signs up  
2. User defines financial goal  
3. System builds financial baseline  
4. AI generates strategy  
5. System simulates outcomes (what-if scenarios)  
6. User accepts / rejects recommendations  
7. System adapts based on feedback loop

---

## **7\. 🧠 System Architecture**

FinSight is composed of four core layers:

### **7.1 Data Layer (Input Layer)**

Aggregates and normalizes financial data:

* income  
* expenses  
* transactions  
* savings  
* goals

**Output:**  
Structured financial state

---

### **7.2 Deterministic Financial Engine (Truth Layer)**

Core system of financial correctness.

**Responsibilities:**

* cashflow calculation  
* savings rate computation  
* baseline projections  
* goal timeline estimation

**Constraints:**

* fully deterministic  
* no AI usage  
* single source of truth for all financial math

Testing Requirements

* All financial calculation functions (cashflow, savings rate, goal timeline) must have unit test coverage of ≥ 95%  
* Tests must cover edge cases: zero income, zero expenses, negative cashflow, goal amount of $0, and goal already met  
* Deterministic engine must produce identical output for identical inputs across 100% of test runs (no variance allowed)  
* Autotest suite must be authored and passing before AI layer integration begins (Phase 1 gate)

---

### **7.3 Scenario Engine (What-if Simulation Layer)**

Simulates financial outcomes under behavioral changes.

**Example:**

* reduce discretionary spending  
* increase savings rate  
* adjust monthly budget

**Outputs:**

* new time-to-goal  
* savings delta  
* risk/behavioral assumptions

**Includes:**

* probabilistic adherence modeling (real-world behavior realism)

Testing Requirements

* Each scenario type (baseline, single action, multi-action) must have automated integration tests covering at least 5 input permutations per type  
* Adherence rate boundary values (0.1 floor, 0.95 ceiling, and midpoint 0.5) must be explicitly tested  
* Scenario output schema must be validated automatically on every build — any missing or malformed field fails the build  
* Output delta calculations (time-to-goal delta, savings delta) must be regression-tested against a fixed set of known inputs and expected outputs

---

### **7.4 AI Layer (LLM Reasoning Engine)**

**Responsible for:**

* generating financial strategies  
* prioritizing recommendations  
* explaining outputs in natural language

**Constraints:**

* LLM does NOT perform financial calculations  
* LLM only operates on structured outputs

Testing Requirements

* Every failure mode listed (hallucinated numbers, missing fields, inconsistent logic) must have a corresponding automated test case in the regression suite  
* The regression suite must include ≥ 50 representative prompt/response pairs covering: valid outputs, schema violations, numeric outliers, and contradictory recommendations  
* Schema validation and numeric sanity checks must run automatically on every AI output in CI (not just in production)  
* A hallucination rate gate must be enforced in CI: if \> 1% of test cases fail validation, the build does not pass  
* Test suite must be maintained and expanded with every new prompt template or recommendation category added

---

### **7.5 Orchestration Layer**

Combines deterministic outputs with AI reasoning:

* ensures grounding of all AI outputs  
* prevents hallucinations  
* merges scenario results with recommendations

---

### **7.6 Feedback Loop System**

Continuously improves personalization based on user behavior.

**Inputs:**

* accepted recommendations  
* rejected recommendations  
* modified actions (user-adjusted amounts or timelines)  
* observed financial behavior (actual vs. projected savings delta)

**Update Mechanism:**

Adherence rates update using an Exponential Weighted Moving Average (EWMA) with smoothing factor **α \= 0.3**.

Formula:  
`new_rate = (α × observed_execution) + ((1 − α) × prior_rate)`

* Minimum data threshold: adherence rates do not update until ≥ 3 data points exist per category  
* Categories are updated independently (e.g., subscriptions and food spending do not influence each other)  
* Updates trigger after each weekly check-in or recommendation resolution event

**Outputs:**

* updated per-category adherence rates  
* recommendation priority re-ranking  
* personalization tuning (categories with consistently low adherence are deprioritized or reframed)

**Safeguards:**

* adherence rate is floor-capped at **0.1** (system never assumes zero compliance)  
* adherence rate is ceiling-capped at **0.95** (system never assumes perfect compliance)  
* if fewer than 3 events exist, system uses category defaults from Section 7.3.2

---

## **8\. 🧩 Core MVP Features**

### **8.1 Financial Profile**

* income tracking  
* expense tracking  
* savings tracking  
* goal definition

---

### **8.2 Financial Engine**

* monthly cashflow calculation  
* savings rate computation  
* baseline financial projection

---

### **8.3 AI Recommendation System**

Each recommendation includes:

* action  
* expected financial impact  
* explanation  
* priority score

**Confidence Score Definition:**  
The confidence score (0–100%) represents the AI layer's assessed reliability of a recommendation given the user's current financial state and historical adherence data. It is computed as a weighted composite of:  
(a) scenario engine output stability across adherence rate range 0.1–0.95 (40% weight),  
(b) similarity of user's financial profile to historically successful recommendation patterns (40% weight),  
(c) data completeness of the current financial snapshot (20% weight).  
Scores below 60% are not surfaced to the user.  
Scores 60–79% display as "moderate confidence."  
Scores 80%+ display as the numeric value (e.g., 82%).

---

### **8.4 Scenario Simulation Engine (Core Differentiator)**

For each recommendation:

* baseline vs scenario comparison  
* time-to-goal impact  
* savings delta  
* behavioral assumptions

---

### **8.5 Feedback System**

* accept / reject / modify recommendations  
* behavioral tracking  
* adaptive learning signals

---

## **9\. 🖥️ User Experience Flow**

FinSight.ai is a decision-first interface. Every screen drives a single action. No passive dashboards. No data dumps.

### **Screen 1 — Sign Up / Authentication**

**What the user sees:**

* Full-screen silver background with centered black FinSight.ai logo  
* Email \+ password fields  
* "Get Started" black CTA button  
* Subtext: "Not a financial advisor. A financial decision system."

**Key Interactions:**

* User enters email and password and taps "Get Started"  
* System validates email format and password strength (min 8 characters, 1 number) in real time  
* On success: transition to Screen 2 (Goal Setup)

**Error States:**

* Invalid email format → inline red error: "Enter a valid email address"  
* Password too short → inline red error: "Password must be at least 8 characters"  
* Email already registered → inline red error: "Account exists. Sign in instead." with sign-in link  
* Network failure → toast notification: "Connection error. Please try again."

---

### **Screen 2 — Goal Setup**

**What the user sees:**

* Black card centered on silver background  
* Headline: "What are you working toward?"  
* Goal type selector (single select): Save for emergency fund / Pay off debt / Save for home / Build wealth / Custom  
* Goal amount input field (numeric, USD)  
* Goal deadline selector (month/year picker)  
* "Set My Goal" black CTA button

**Key Interactions:**

* User selects goal type — selecting a type pre-fills a suggested goal amount and timeline (e.g., Emergency Fund → $10,000 / 12 months)  
* User can override pre-filled values  
* Goal amount validates as positive integer only  
* Deadline must be at least 30 days from today

**Error States:**

* No goal type selected → CTA disabled, greyed out with tooltip: "Select a goal to continue"  
* Goal amount \= $0 or blank → inline red error: "Enter a goal amount greater than $0"  
* Deadline in the past → inline red error: "Select a future date"  
* Goal already met (user enters current savings ≥ goal amount in Screen 3\) → system flags on Screen 4 with a congratulation state and prompts goal revision

---

### **Screen 3 — Financial Snapshot Input**

**What the user sees:**

* Black card with white text  
* Headline: "Tell us about your finances"  
* 5 manual input fields:  
  1. Monthly take-home income (USD)  
  2. Monthly fixed expenses (rent, subscriptions, loans)  
  3. Monthly variable expenses (food, transport, lifestyle)  
  4. Current savings balance (USD)  
  5. Monthly savings contribution (USD)  
* Progress indicator: Step 3 of 4  
* "Build My Baseline" black CTA button

**Key Interactions:**

* All fields are numeric (USD), formatted with commas on blur  
* System computes monthly cashflow in real time as user types: cashflow \= income − fixed expenses − variable expenses (displayed as a live preview below the form in green if positive, red if negative)  
* User can tap each field label for a tooltip explaining what to include

**Error States:**

* Any field left blank → CTA disabled until all fields completed  
* Income \= $0 → inline warning (not block): "Are you sure? We'll use this to build your baseline."  
* Monthly expenses \> income → live red preview: "Your expenses exceed your income. We'll account for this in your plan."  
* Negative savings balance entered → inline red error: "Savings balance cannot be negative"  
* Non-numeric input → field rejects character on keystroke

Income Volatility Handling (MVP)

The monthly income field accepts a single value in MVP — for variable earners, the system prompts: "Is your income consistent month to month?" with two options: "Yes, roughly the same" / "No, it varies"

* If user selects "No, it varies" → an additional prompt appears: "Enter your typical monthly income — not your best month or worst month, just a realistic average."  
* The "typical income" value is used as the baseline input to the deterministic engine  
* A volatility flag (`income_volatile: true`) is stored on the user profile and used to: (a) apply more conservative adherence rate defaults for savings-increase categories (floor shifted to 0.3 from 0.6), (b) append range language to all time-to-goal projections ("approximately X–Y months" instead of "X months"), (c) surface the "Update My Finances" CTA more prominently on Screen 8  
* This is an MVP bridge solution. The full income range model (low / typical / high) is specified in Section 17 as a post-MVP enhancement.

---

### **Screen 4 — Baseline Financial State**

**What the user sees:**

* Black Financial Snapshot Card showing:  
  * Monthly cashflow (green or red delta)  
  * Current savings rate (%)  
  * Baseline time-to-goal (months)  
  * Monthly savings gap (how much more is needed to hit goal on time)  
* Headline: "Here's where you stand"  
* Subtext: "Based on your current behavior, here's your financial trajectory."  
* "Show Me What's Possible" orange CTA button

**Key Interactions:**

* All numbers are read-only — computed by deterministic engine  
* User can tap any metric for an explanation tooltip  
* "Show Me What's Possible" triggers AI strategy generation and transitions to Screen 5

**Error States:**

* Engine computation error → full-screen error state: "Something went wrong building your baseline. Please review your inputs." with back button to Screen 3  
* Latency \> 300ms → skeleton loading state shown (no spinner, skeleton cards matching layout)  
* Goal already met state (savings ≥ goal) → congratulation card \+ "Update Your Goal" CTA redirecting to Screen 2

---

### **Screen 5 — AI Strategy View**

**What the user sees:**

* Headline: "Your Financial Strategy"  
* 3–5 AI Recommendation Cards (black, white text), each showing:  
  * Action (e.g., "Reduce dining out by $150/month")  
  * Category (lifestyle / fixed / savings)  
  * Priority badge (1, 2, 3...)  
  * Confidence score (e.g., 82%)  
  * Expected impact: "Reach your goal 3 months sooner"  
* Each card has two buttons: "Simulate This" (orange) and "Skip" (ghost button)

**Key Interactions:**

* "Simulate This" → opens scenario simulation for that recommendation on Screen 6  
* "Skip" → marks recommendation as rejected, logs feedback signal, card collapses  
* User can expand any card to read full AI explanation (natural language)  
* User can swipe through recommendations or scroll vertically

**Error States:**

* AI layer returns \< 3 recommendations → system supplements with deterministic fallback recommendations (e.g., "Increase monthly savings by $X") displayed with a "System Suggested" badge instead of confidence score  
* AI output fails schema validation → recommendation card not rendered; fallback card shown: "We couldn't generate a personalized recommendation for this category."  
* All recommendations skipped → screen transitions to a "You're in control" state with a single CTA: "Review My Baseline" (returns to Screen 4\)  
* AI response latency \> 3s → skeleton recommendation cards shown with loading pulse animation

---

### **Screen 6 — Scenario Simulation (Core Interaction)**

**What the user sees:**

* Headline: "What if you \[action\]?"  
* Two side-by-side cards:  
  * LEFT: Baseline card (current trajectory) — grey tint  
  * RIGHT: Scenario card (projected with action) — white/highlighted  
* Each card shows: time-to-goal, monthly savings, savings delta  
* Orange slider: "Adjust your effort level" (maps to adherence rate 10%–95%)  
* Green delta label: "You'd reach your goal X months sooner" (updates in real time as slider moves)  
* Two CTAs: "Accept This Plan" (black) and "Try Another Scenario" (ghost)

**Key Interactions:**

* Slider adjusts adherence rate in real time → scenario output recalculates instantly  
* All scenario math is computed by the deterministic \+ scenario engine, never the AI layer  
* "Accept This Plan" → logs acceptance event, updates adherence model, transitions to Screen 7  
* "Try Another Scenario" → returns to Screen 5 with current recommendation marked as "reviewed"  
* User can tap the scenario card metrics for explanation tooltips

**Error States:**

* Scenario engine returns error → full card error state: "Simulation unavailable. Try adjusting your inputs." with retry button  
* Adherence slider set to 0 → slider floor-capped at 0.1 (10%), cannot be set to zero  
* Delta calculation results in negative savings → scenario card shows red delta: "This action may slow your progress. Consider adjusting your effort level."  
* Scenario engine latency \> 1.5s → right card shows skeleton loading while left (baseline) remains visible

---

### **Screen 7 — Decision Confirmation**

**What the user sees:**

* Headline: "You're committed to a plan"  
* Summary card showing:  
  * Accepted recommendation(s)  
  * Combined time-to-goal delta  
  * New projected goal completion date  
  * Estimated monthly savings increase  
* "Start Tracking" black CTA button  
* Secondary link: "Go back and adjust"

**Key Interactions:**

* Read-only confirmation screen — no edits made here  
* "Start Tracking" activates the feedback loop, sets weekly check-in schedule, transitions to Screen 8  
* "Go back and adjust" returns to Screen 5

**Error States:**

* No accepted recommendations → this screen is unreachable (CTA on Screen 6 only appears after acceptance)  
* Projected goal date \> 30 years → system shows warning: "This goal has a very long timeline. Consider adjusting your goal amount or deadline." with option to revise

---

### **Screen 8 — Feedback Loop Dashboard (Ongoing)**

**What the user sees:**

* Headline: "How are you doing?"  
* Weekly check-in prompt card: "Did you \[accepted action\] this week?"  
* Three response buttons: "Yes, fully" / "Partially" / "Not this week" (maps to execution rates 1.0 / 0.5 / 0.0)  
* Updated Goal Progress Card showing:  
  * Current savings vs. goal  
  * Revised time-to-goal based on latest adherence data  
  * Savings delta (this week vs. last week)  
* "Update My Finances" CTA (re-enters Screen 3 to refresh financial snapshot)

**Key Interactions:**

* Weekly check-in response logs a feedback event and triggers EWMA adherence rate update (per Section 7.6)  
* Adherence rate update only applies after ≥ 3 check-in events per category  
* Goal Progress Card refreshes after each check-in  
* "Update My Finances" available at any time — re-running Screen 3 and 4 resets the baseline

**Error States:**

* User skips weekly check-in for 2+ weeks → nudge notification: "Your plan may be out of date. Check in to keep your strategy accurate."  
* Financial snapshot update results in negative cashflow → system re-runs AI strategy generation and surfaces a revised plan with a banner: "Your financial situation changed. Here's an updated strategy."  
* Savings balance decreases vs. previous check-in → red delta displayed with explanation: "Your savings dipped this week. Here's what you can adjust."

---

Notification & Re-engagement System

* **Weekly check-in reminder:** push/email notification sent every Monday at 9am user local time — "Time to check in on your plan. 2 minutes to keep your strategy on track."  
* **Missed check-in nudge:** if no check-in recorded by Wednesday → second notification: "Your plan may be drifting. Quick check-in?"  
* **Positive milestone notification:** when savings delta is positive for 3 consecutive weeks → "You're ahead of schedule. Here's what's working."  
* **Goal velocity alert:** when time-to-goal improves by ≥ 10% in a single week → "Big progress this week. You're on track to reach your goal X months sooner."  
* **Stale data alert:** after 30 days without financial snapshot update → "Your data may be outdated. Update your finances to keep your strategy accurate."  
* **Plan drift alert:** when adherence rate drops below 0.3 for 2 consecutive weeks → "Your plan may need adjusting. Let's look at what's realistic."  
* All notifications are opt-in. User can configure frequency (weekly / off) in settings. No notifications sent between 9pm–8am user local time.

---

## **10\. 🗄️ Data Integration Architecture**

FinSight.ai is designed for manual data input at MVP with a Plaid-ready abstraction layer that requires zero re-engineering to activate bank connectivity in a future phase.

### **10.1 MVP Data Input — Manual Entry**

All financial data is collected via structured manual input (Screen 3).

**Input fields collected:**

* monthly\_income (float, USD)  
* fixed\_expenses (float, USD)  
* variable\_expenses (float, USD)  
* current\_savings (float, USD)  
* monthly\_savings\_contribution (float, USD)

**Validation rules applied at input layer:**

* All values must be non-negative floats  
* monthly\_income must be \> 0  
* fixed\_expenses \+ variable\_expenses must not exceed monthly\_income × 3 (sanity cap — flags for review, does not block)  
* current\_savings must be ≥ 0

Income Volatility Fields (MVP addition):

* `income_type`: "stable" | "variable" (captured via volatility toggle on Screen 3\)  
* `income_volatile`: boolean (true if user selects "No, it varies")

{   "user\_id": "uuid",   "snapshot\_date": "ISO8601",   "income": { "monthly": float, "income\_type": "stable | variable", "income\_volatile": boolean },   "expenses": { "fixed": float, "variable": float, "total": float },   "savings": { "balance": float, "monthly\_contribution": float },   "cashflow": { "monthly": float },   "goal": { "target\_amount": float, "deadline": "ISO8601", "type": string } }  
---

### **10.2 Data Abstraction Layer (Plaid-Ready Architecture)**

The data input layer is built as a provider-agnostic abstraction. The deterministic engine only ever consumes the normalized financial state JSON defined in 10.1 — it has no awareness of the data source.

**Abstraction interface:**

DataProvider (interface)  
→ ManualInputProvider (MVP — active)  
→ PlaidProvider (future phase — inactive)  
→ CSVImportProvider (future phase — inactive)

When Plaid is activated in a future phase:

* PlaidProvider maps Plaid transaction data to the same normalized JSON schema  
* No changes required to the deterministic engine, scenario engine, or AI layer  
* Only the DataProvider implementation swaps

---

### **10.3 Data Refresh & Staleness**

* Financial snapshot is considered stale after 30 days without an update  
* System prompts user to refresh via "Update My Finances" CTA on Screen 8  
* Stale data warning displayed on Goal Progress Card after 30 days: "Your financial data may be outdated. Update to keep your plan accurate."  
* Stale data does not block the system — recommendations continue using last known snapshot with a staleness badge

---

### **10.4 Data Storage & Privacy**

* All financial data stored encrypted at rest (AES-256)  
* Data transmitted over TLS 1.2+  
* No financial data shared with third parties in MVP  
* User can delete all data at any time (right to erasure)  
* Data retained for 90 days post account deletion for fraud/audit compliance, then purged  
* No raw transaction data stored in MVP (manual input only — no PII beyond user-entered values)  
* CCPA alignment: user can request data export in JSON format

---

### **10.5 Future Integration Path (Post-MVP)**

* Plaid integration is explicitly out of scope for MVP. When prioritized:  
  * Activate PlaidProvider implementation  
  * Map Plaid transaction categories to FinSight expense categories (fixed / variable)  
  * Add user consent flow for bank connection (OAuth)  
  * Add data sync frequency setting (daily / weekly / manual)  
  * No changes to financial engine, scenario engine, or AI layer required

---

## **11\. ⚠️ Constraints & Guardrails**

* No financial advisor positioning  
* No autonomous financial execution (MVP)  
* No AI-generated numerical calculations  
* All numeric outputs must originate from deterministic engine  
* All recommendations must be explainable and grounded  
* Trust \> intelligence

---

## **12\. 📊 Metrics**

### **North Star Metric**

* Savings rate increase (target: \+5 percentage points avg over 6 months)  
* Time-to-goal reduction (target: 20% median reduction within 6 months)

### **Product Metrics**

* Recommendation acceptance rate (target: ≥ 50% weekly)  
* Goal completion rate (target: ≥ 60% show positive savings delta at Day 30\)  
* Week 4 retention (target: ≥ 40% of onboarded users active at Day 28\)  
* Behavioral improvement over time (tracked via EWMA adherence rate trend per user)

### **AI Metrics**

* Hallucination rate (target: \< 1% of outputs fail validation)  
* Explanation clarity score (target: ≥ 4.0/5.0 in-app)  
* Recommendation usefulness score (target: ≥ 4.0/5.0 in-app)

---

## **13\. 🧪 MVP Scope**

### **Must Have**

* user onboarding  
* goal setup  
* financial input (manual or mock)  
* deterministic financial engine  
* AI recommendation system  
* scenario simulation engine  
* feedback loop system

### **Should Have**

* basic integrations (e.g., Plaid later)  
* recurring insights

### **Out of Scope (MVP)**

* payments automation  
* investing / trading features  
* full banking replacement

---

## **14\. 🧠 Product Principles**

* Action \> Insight  
* Simulation \> Static advice  
* Deterministic truth \> AI output  
* Minimal input → maximal outcome value  
* Trust is a core product feature

---

## **15\. 🛑 Risks**

* AI hallucination in financial context  
* Incorrect behavioral modeling  
* User trust loss  
* Regulatory constraints  
* Over-automation risk

---

## **16\. 📌 MVP Definition of Done**

MVP is complete when all of the following are true:

### **Functional Completeness**

* User can complete full onboarding flow (goal setup \+ financial input) in under 5 minutes  
* Deterministic engine produces baseline projection within 300ms  
* Scenario engine returns at least 3 scenario outputs per recommendation session  
* AI layer produces structured recommendation output with action, priority, confidence, and expected impact  
* Feedback loop records accept/reject/modify events and updates adherence rates after ≥ 3 events

### **Outcome Thresholds (measured at Day 30 post-launch with first user cohort)**

* ≥ 50% of active users accept at least one recommendation per week  
* ≥ 60% of active users show a positive savings delta compared to their baseline at onboarding  
* \< 1% of AI outputs fail schema or numeric sanity validation  
* ≥ 4.0/5.0 average explanation clarity score (in-app feedback)

### **Ship Criteria**

* All Must Have features from Section 13 are live and tested  
* Hallucination rate QA test suite passes with \< 1% failure rate  
* Privacy and compliance review completed (FTC alignment, no advisory framing)  
* Deterministic engine autotest suite passes at ≥ 95% function coverage with zero failures  
* Scenario engine integration tests pass across all 3 scenario types and all boundary adherence values  
* AI layer regression suite (≥ 50 test cases) passes with \< 1% hallucination/schema failure rate in CI  
* All three autotest suites run automatically on every merge to main branch (CI gate enforced)

---

## **17\. 📅 Roadmap & Phasing**

**Project Estimate:** Medium — 4–6 weeks

**Team:** 2–3 people (1 full-stack engineer, 1 AI/backend engineer, 1 product/design)

### **Phase 1 — Core Engine (Weeks 1–2)**

* **Key Deliverables:** deterministic financial engine, scenario engine with adherence model, data input layer (manual), structured output schema  
* **Dependencies:** none  
* **Owner:** engineering

### **Phase 2 — AI Layer \+ UX Shell (Weeks 3–4)**

* **Key Deliverables:** LLM reasoning layer with guardrails, orchestration layer, recommendation UI (onboarding → goal → scenario → decision flow), feedback loop event capture  
* **Dependencies:** Phase 1 complete  
* **Owner:** engineering \+ design

### **Phase 3 — Feedback Loop \+ MVP Launch (Weeks 5–6)**

* **Key Deliverables:** adherence rate update mechanism (EWMA), personalization tuning, QA test suite for hallucination rate, privacy/compliance review, Day 0 cohort onboarding  
* **Dependencies:** Phase 2 complete  
* **Owner:** full team

### **Post-MVP Enhancement: Income Range Model**

**Problem:** The fixed monthly income input is structurally incorrect for variable earners (Persona 3 — Volatile Earner). A single income figure produces a single-point projection that overstates certainty and distorts recommendations during income swings. For users whose income varies ±30–50% month-to-month, this leads to either over-optimistic plans (based on a high-income month) or unnecessarily conservative plans (based on a low-income month). Both erode trust.

**MVP Bridge:** The "typical income" input with `income_volatile` flag (Section 9, Screen 3\) is an acceptable MVP approximation. It reduces projection error and enables conservative adherence defaults for volatile earners without requiring a full range model.

Post-MVP Solution: Income Range Model

Replace the single `monthly_income` field with a three-point income range input:

* **income\_low**: worst realistic month (USD)  
* **income\_typical**: average/expected month (USD)  
* **income\_high**: best realistic month (USD)

This enables multi-scenario forecasting:

* **Pessimistic scenario:** computed using `income_low` \+ conservative adherence defaults  
* **Base scenario:** computed using `income_typical` \+ standard adherence defaults  
* **Optimistic scenario:** computed using `income_high` \+ upper adherence defaults

Scenario engine output for volatile earners becomes a range: "Based on your income range, you'll reach your goal in 9–16 months depending on how your income plays out." All three scenario bands are displayed simultaneously on Screen 6 (replacing the single scenario card with a range visualization).

Additional post-MVP features enabled by income range model:

* **Windfall detection:** when user updates snapshot with income significantly above `income_typical` (\> 120% of typical), system surfaces a dedicated windfall allocation scenario: "You had a strong month. Here's how to use the surplus to accelerate your goal."  
* **Low-income period mode:** when updated snapshot shows income near `income_low`, system switches recommendation focus from savings optimization to expense minimization, with a contextual banner: "Tough month? Here's how to protect your progress."  
* **Stress-test scenario:** "What if your income drops 30% for 3 months?" — proactive resilience planning surfaced for all volatile earners

**Engineering note:** The DataProvider abstraction layer (Section 10.2) and normalized JSON schema require a non-breaking extension to support the three-point income model. The deterministic engine requires a new multi-scenario computation path. No changes to the AI layer or orchestration layer are required — the AI layer already consumes `scenario_outputs[]` as an array, which will simply contain three entries instead of one.

**Priority:** High — schedule for Phase 4 (first post-MVP sprint) given Persona 3 represents a significant addressable segment and income volatility handling is a primary product differentiator.

### **Out of Scope for MVP (Future Phases)**

* Plaid / bank integrations  
* Optimized multi-action scenario (Section 7.3.4)  
* Automated financial execution  
* Investing / trading features

---

## **18\. 🎨 UI / UX Design Direction**

FinSight.ai uses a minimal, high-contrast, decision-first UI system.

### **Visual Style**

* Background: silver / light metallic gray  
* Logo: black “FinSight.ai”  
* Cards: black  
* Text on cards: white  
* Interactive sliders: orange  
* Buttons: black  
* Deltas:  
  * green \= positive impact  
  * red \= negative impact

### **UX Principles**

* Action-first interface (no passive dashboards)  
* Every screen drives a decision  
* Scenario comparison is core UI element  
* Changes immediately reflect outcome simulation  
* Minimal cognitive load (\<3 seconds to understand impact)

### **Core UI Components**

* Financial Snapshot Card  
* AI Recommendation Card  
* Scenario Simulation Card (what-if core)  
* Goal Progress Card

### **UX Philosophy**

FinSight is not a dashboard.

It is a financial decision control system.

