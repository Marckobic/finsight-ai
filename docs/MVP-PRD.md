# **📄 FinSight.ai — MVP PRD (Decision Intelligence System)**

---

### **TL;DR**

FinSight.ai is a Decision Intelligence system purpose-built for personal finance: it transforms user-entered financial data into deterministic projections, models behavioral simulations (not static scenarios) around actionable decisions, and generates constrained AI explanations. The MVP validates if exposing users to financial truth, behavioral simulation (uncertainty modeling), and a decision-first UI delivers measurable outcome improvement. It is not a dashboard — it is a financial decision control system for US professionals.

---

## **Goals**

### **Business Goals**

* Validate the core decision loop (user sees truth, simulates action, makes a decision).  
* Demonstrate that recommendation adoption directly drives measurable financial improvement.  
* Establish a baseline for AI safety, with systemwide hallucination rate below 1%.  
* Prove method with minimum 50-user live cohort.

### **User Goals**

* Accurately understand their financial baseline in \<5 minutes.  
* Simulate the impact of changing a single behavior on savings and time-to-goal.  
* Confidently make one clear, high-leverage financial decision without advisor or dashboard confusion.  
* Complete the scenario journey (from input to decision) with fewer than 10 clicks.

### **Non-Goals**

* Personalized recommendation engine (e.g., EWMA learning loops).  
* Notifications or retention-focused messaging.  
* Plaid/data aggregation integration.  
* Multi-goal scenario optimization.  
* Income range modeling (low/typical/high months).  
* Autonomous recommendation or execution.

---

## **MVP Validation Criteria**

**The MVP is a learning experiment, not a general launch.**  
‘Validation’ is defined as:

* **Cohort size:** ≥ 50 active users  
* **Time window:** Results measured on or after Day 30 post-cohort launch  
* **Outcome thresholds:**  
  * ≥ 30% of cohort accepts at least one recommendation  
  * ≥ 20% of cohort demonstrates 7-day retention  
  * ≥ 50% of cohort achieves a positive savings delta vs. their self-reported baseline

**Go/No-Go Decision:**

* **ADVANCE** (to Full PRD phase): *All* three thresholds met at Day 30\.  
* **ITERATE** (UX/copy only): Metrics fall between targets and minimum floors (acceptance \< 30% but ≥ 20%; retention \< 20% but ≥ 10%).  
* **PIVOT** (core loop rethink): Acceptance rate \< 20% or retention \< 10%.

*The MVP is a controlled validation experiment; team will only advance, iterate, or pivot based on these defined cohort metrics.*

---

## **User Stories**

### **Persona 1: Early-Career Optimizer**

* As a financially aware professional, I want to see how one specific change affects my goal, so that I can confidently act without needing a financial advisor.  
* As an optimizer, I want deterministic projections rather than vague advice, so that I fully trust the outcome of my decision.

### **Persona 2: Constrained Planner (Dependents)**

* As a person with fixed obligations, I want the system to account for my hard financial constraints, so that the recommendations are truly executable in my real life.  
* As a planner, I want to reject unrealistic scenarios, so that I retain control over my finances.

### **Persona 3: Volatile Earner (Freelance/Founder)**

* As a freelancer with variable income, I want to enter my “typical month” and have the system realistically project outcomes, so that I can make decisions without pretending my income is stable.  
* As a volatile earner, I want recommendations to reflect my income risk, so that projections don’t set me up for disappointment.

---

## **Functional Requirements**

* **Core Engine (Priority: P0)**  
  * Deterministic Cashflow Calculation: Compute cashflow given user-input income/expenses.  
  * Savings Rate Computation: Show user’s savings rate as a percent of income.  
  * Time-to-Goal Projection: Calculate months to target goal at current rate.  
  * Baseline Financial Projection: Present true (no scenario) path to goal.  
* **Scenario Engine (Priority: P0)**  
  * Single-Variable Simulation: Simulate effect of increasing savings by user-adjustable amounts.  
  * Delta Output: Compute and display time-to-goal delta and savings delta between scenario and baseline.  
  * **Probabilistic Output:** Outputs are probabilistic ranges reflecting behavioral uncertainty (not fixed/calculator values). Example: “At 70% adherence, time-to-goal is likely 12–14 months.”  
* **Event-Driven Decision Loop (Priority: P0)**  
  * User input triggers deterministic baseline computation  
  * Baseline triggers scenario simulation  
  * Scenario output triggers AI explanation  
  * User decision (accept/reject) triggers feedback logging  
  * Feedback logged triggers system adaptation signal  
  * This is a loop, not a linear flow — each step depends on the previous and feeds the next  
* **AI Layer (Priority: P0)**  
  * Constrained Explanation Only: Provide scenario explanations in natural language, with strict use of engine outputs only (no numeric generation).  
  * Structured Contracts: Input/output schemas enforced.  
  * Validation Gateway: Catch violations, fallback to deterministic message template.  
* **UI System (Priority: P0)**  
  * 4-Screen Decision Flow: Goal Setup → Financial Input → Baseline → Scenario Decision.  
  * Decision-First Interface: User makes clear accept/reject choice on each scenario.  
  * Scenario Comparison as Core: Side-by-side cards showing baseline vs. scenario.  
* **Data Input (Priority: P0)**  
  * Manual Financial Input: All fields entered by user, no external data pulled.  
  * Income Volatility Toggle: Switch for stable vs. variable; routes to “typical month.”  
  * JSON Normalized Output: Prepare for future providers.  
* **Autotest System (Priority: P0)**  
  * Continuous Integration Gates: Must pass before deployment.  
  * Regression Suite: ≥ 50 automated test cases for deterministic/AI/validation paths.  
  * Deterministic Engine: ≥ 95% test coverage, includes edge inputs (zero/negative/goal-met).

---

## **User Experience**

**Entry Point & First-Time User Experience**

* Users access FinSight via direct signup; there is no onboarding tour (minimize friction).  
* First session begins with a clear Goal Setup prompt.

**Screen 1: Goal Setup**

* UI: Selector for goal type (Emergency Fund / Pay Off Debt / Save for Home / Build Wealth / Custom), amount input, deadline picker.  
* CTA: “Set Goal” (disabled until valid input)  
* Error States:  
  * No type selected: CTA disabled.  
  * Amount \= $0: Inline error ("Set a goal greater than $0").  
  * Deadline in past: Inline error.

**Screen 2: Financial Input**

* UI: Income input (with Stable/Variable toggle), fields for fixed and variable expenses, current savings balance, real-time surplus preview (green if positive, red if negative).  
* CTA: “Build My Baseline” (disabled if blank fields)  
* Error States:  
  * Blank fields: CTA disabled.  
  * Expenses \> Income: Real-time red warning, non-blocking.  
  * Non-numeric chars: Blocked at keystroke.

**Screen 3: Baseline View**

* UI: Financial Snapshot Card (monthly cashflow, savings rate, time to goal, monthly gap).  
* Headline: “At your current rate, you will reach your goal in X months.”  
* CTA: “Show Me What’s Possible” (orange)  
* Error States:  
  * Engine latency \> 300ms: Show skeleton cards.  
  * Calculation error: Full error card, back button.  
  * Goal already met: Show “Congratulations” state.

**Screen 4: Scenario Decision Screen (CORE)**

* UI: Side-by-side cards — LEFT (Baseline, grey), RIGHT (Scenario, white). Headline: “What if you increase savings by $300/month?” Delta label: “14 → 9 months • You reach your goal 5 months sooner.”  
* Orange adherence slider (10–95%, live recalc).  
* CTAs: Accept (black) / Reject (ghost)  
* Error States:  
  * Calculation error: Card collapses, retry CTA.  
  * Adherence slider \< 10%: Floor block.  
  * Negative delta: Red warning card.  
  * Scenario latency \> 1.5s: Show skeleton for scenario side; baseline remains visible.

**Advanced/Edge Cases**

* All recommendations rejected: "You're in control" state, Review Baseline CTA.  
* Goal date \> 30 years: Long-timeline warning, option to revise.

**UI/UX Highlights**

* Silver background, black cards, white text, orange interactive controls, green (positive delta) and red (negative delta) deltas.  
* Every screen supports minimal cognitive load (target: user understands next action in \<3 seconds).  
* No dashboards or passive data views.

---

## **Narrative**

Alex is a 29-year-old product designer earning $78,000 a year. Despite having $12,000 in checking, Alex lacks a structure for reaching a real emergency fund goal. Alex signs up for FinSight, sets a $20,000, 12-month objective, and enters income/expenses in under 3 minutes. FinSight immediately presents the baseline: At Alex’s current rate, the goal will take 18 months, not 12\. Curious, Alex taps “Show Me What’s Possible.” The system simulates one change — increasing monthly savings by $300. The scenario card updates: 18 → 11 months. Alex uses the effort slider, realistically sets adherence to 70%, and sees the projection adjust: 13 months. Satisfied with this actionable, credible scenario, Alex hits “Accept.” No adviser. No complex dashboard. Just one decision, one outcome, one click. This experience defines the MVP.

---

## **Success Metrics**

### **User-Centric Metrics**

* Recommendation acceptance rate (measured at Day 7 and Day 30): Target ≥ 30%.  
* 7-day retention (users returning within 7 days): Target ≥ 20%.  
* Positive savings delta (at Day 30 vs. baseline): Target ≥ 50% of active cohort.

### **Business Metrics**

* Cohort validation: First 50-user pilot completes by Day 30\.  
* Go/no-go decision by Day 35\.

### **Technical Metrics**

* Deterministic engine latency: \< 300ms (p95)  
* Scenario engine latency: \< 1.5s (p95)  
* AI response: \< 3s (p95)  
* Hallucination rate: \< 1%  
* Schema failure rate: \< 1%  
* System uptime: ≥ 99.5%

### **Tracking Plan**

* `goal_set` (goal type, amount, deadline)  
* `baseline_viewed`  
* `scenario_simulated` (action, delta\_months, adherence\_rate)  
* `recommendation_accepted`  
* `recommendation_rejected`  
* `slider_adjusted` (adherence value)  
* `session_duration`  
* `screen_drop_off` (per screen)

---

## **Technical Considerations**

### **Technical Needs**

* **5-Layer Architecture:**  
  * Layer 1: Deterministic Engine (TRUTH LAYER) — cashflow, savings rate, time-to-goal, baseline projections. Fully deterministic, no AI, single source of truth. 95%+ test coverage required.  
  * Layer 2: Scenario Engine (BEHAVIORAL SIMULATION LAYER) — single-variable simulation. Inputs: financial state, behavioral change, adherence assumption (0.1–0.95). Outputs: time-to-goal range (probabilistic, not fixed), savings delta, scenario trajectory. Key principle: outputs reflect behavioral uncertainty, not mechanical precision.  
  * Layer 3: AI Layer (EXPLANATION LAYER) — strictly constrained. Allowed: explain scenario results, summarize tradeoffs, format recommendation narrative. Not allowed: compute numbers, override deterministic engine, invent financial values. **AI operates only within the event-driven loop — it never initiates, only responds to structured engine outputs.**  
  * Layer 4: Validation Gateway (HARD SAFETY LAYER) — schema validity checks, numeric consistency vs engine, missing field detection, hallucinated value rejection. Fallback: deterministic template response.  
  * Layer 5: UI Layer (DECISION ENFORCEMENT LAYER) — enforces one decision per screen, decision-first interface, no dashboards, no passive data views.  
* **Event-Driven Decision Loop:**  
  The system operates as a closed loop, not a linear flow:  
  1. User inputs financial data  
  2. Deterministic engine computes baseline  
  3. Scenario engine simulates behavioral change  
  4. AI layer explains scenario output  
  5. User decides (accept / reject)  
  6. Decision event is logged  
  7. System adaptation signal generated  
     Each step depends on the previous and feeds the next. A rejected decision re-enters the loop at step 3 with a new scenario.  
* **Manual Data Input Layer:**  
  * Collected from user, stored in normalized JSON schema (includes user ID, date, income \[+type/+volatile\], expenses, savings, cashflow, and goal).  
  * **DataProvider Architecture:** In MVP, only ManualInputProvider is active. The PlaidProvider interface is designed and coded, but inactive.  
    * **Framing:** All downstream systems consume ONLY the normalized financial state JSON. No engine changes are required when PlaidProvider is activated — the interface contract is the only integration point.  
* **AI System Design:**

Input Contract:  
 {  
  "baseline\_months": 14,  
  "scenario\_months": 9,  
  "delta\_months": 5,  
  "monthly\_savings\_increase": 300  
}

* 

Output Contract:  
 {  
  "recommendation": "Increase monthly savings by $300",  
  "explanation": "This reduces your time to goal by 5 months under current assumptions."  
}

*   
  * Failure Handling:  
    * If AI output invalid: reject response, fallback to deterministic template, log event in validation system.  
  * Hallucination Prevention:  
    * No free-form numeric generation, no raw financial inference, strict schema validation, engine-owned truth layer.

### **Integration Points**

* None in MVP; fully manual input; no third-party financial data integrations required.

### **Data Storage & Privacy**

* Data at rest: AES-256 encryption.  
* In transit: TLS 1.2+.  
* No third-party data sharing.  
* CCPA-aligned: users can export data and request erasure; minimum 90-day post-deletion retention for audit.

### **Scalability & Performance**

* MVP supports ≤ 500 active users; single-server deployment is sufficient.

### **Potential Challenges**

* AI hallucination in financial outputs (mitigated by validation gateway and CI hallucination-rate gating).  
* Income volatility distorting simulations (mitigated via “typical month” flag and conservative scenario defaults).  
* User trust issues from generic or inapplicable recommendations (addressed via constraint-aware scenario engine and explicit accept/reject interface).  
* Over-reliance on deterministic outputs — users may treat projections as guarantees rather than models. **Mitigation:** range language on all projections, explicit adherence slider, AI explanation frames outputs as estimates.  
* Testing reliability: Deterministic Engine ≥ 95% unit test coverage; AI regression suite (≥ 50 cases); CI/build fails if hallucination or schema failure rates \>1%.

---

## **Milestones & Sequencing**

### **Project Estimate**

* **Medium:** 4–6 weeks.

### **Team Size & Composition**

* **Lean team:** 2 people (1 full-stack/backend engineer, 1 product+design lead).

### **Suggested Phases**

**Phase 1 — Core Engine (Weeks 1–2)**

* Key Deliverables: Deterministic engine, scenario engine (single-variable), manual data input, normalized JSON schema, full autotest suite for engine.  
* Owner: Engineering  
* Dependencies: None

**Phase 2 — AI & UI Implementation (Weeks 3–4)**

* Key Deliverables: AI explanation layer with validation gateway, complete 4-screen UI flow, implement income volatility toggle, activate CI gates.  
* Owners: Engineering \+ Design Lead  
* Dependencies: Phase 1 complete

**Phase 3 — Validation Launch (Weeks 5–6)**

* Key Deliverables: End-to-end QA, AI regression suite (≥ 50 prompt/response cases), privacy/legal review, onboard 50-user cohort, execute Day 30 go/no-go assessment.  
* Owners: Full team  
* Dependencies: Phase 2 complete

**Go/No-Go Checkpoint (Day 35\)**

* Advance if all MVP criteria achieved.  
* Iterate if results within margin.  
* Pivot if below core loop floors.

### **Out of Scope for MVP**

* Plaid/data integrations  
* Personalization engine (EWMA)  
* Notification/retention system  
* Multi-goal optimization  
* Income range model  
* Autonomous execution

---

## **14\. 🧠 Final Product Definition**

FinSight is a Decision Intelligence system that combines:

* deterministic financial modeling (truth)  
* behavioral scenario simulation (uncertainty modeling)  
* constrained AI reasoning (explanation only)  
* event-driven decision loop (structure)  
* decision-first UI (enforcement)

to improve real user financial outcomes.

FinSight is not a dashboard. It is a financial decision control system.

