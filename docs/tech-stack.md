### Resource & Tool Specification

#### 1. Machine Learning & Quantitative Backend

* **FastAPI (Python Framework):** High-performance, asynchronous web framework used to build microservices and REST APIs.
* **LightGBM / Scikit-Learn:** Lightweight, CPU-friendly gradient boosting libraries for stock signal classification.
* **pandas-ta & SciPy:** Open-source Python libraries for calculating 130+ technical indicators (RSI, MACD) and detecting geometric chart patterns via peak detection.
* **PyPortfolioOpt:** Mathematical optimization library used to run discrete mean-variance allocation based on user budgets.


* **Ease of Use:** High (Python ecosystem is well-documented with pre-built math/ML primitives).
* **Feasibility:** **100% Feasible** (Runs natively on basic CPU cloud instances without requiring GPUs).

#### 2. Large Language Model (LLM) Explanation Layer

* **Groq Cloud API (`llama-3.1-8b` / `deepseek-r1`):** Ultra-fast LPU (Language Processing Unit) inference provider used to translate JSON outputs into plain-English summaries.


* **Ease of Use:** High (Standard REST API endpoint compatible with OpenAI client SDKs).
* **Feasibility:** **100% Feasible** (Sub-second execution speeds fit well within the 3-second application latency target).

#### 3. Cross-Platform Frontend & State Management

* **React.js + Tailwind CSS:** Modular UI library paired with a utility-first CSS framework for web dashboard development.
* **Capacitor (by Ionic):** Native runtime wrapper that packages the React web application into native iOS and Android binaries.
* **Recharts / Victory Native:** SVG-based chart rendering libraries optimized for responsive mobile and web layouts.
* **Ease of Use:** High (Enables single-codebase development across Web, iOS, and Android).
* **Feasibility:** **100% Feasible** (Eliminates the need to maintain separate Swift and Kotlin codebases).

#### 4. Database, Auth & Hosting Infrastructure

* **Supabase (PostgreSQL):** Open-source Firebase alternative providing managed PostgreSQL databases, Row-Level Security (RLS), and JWT authentication.
* **Render / Railway / Cloudflare Pages:** Cloud platform-as-a-service providers for hosting FastAPI backend containers and static web assets.
* **Ease of Use:** Medium-High (Automates database administration, SSL certificates, and CI/CD deployment pipelines).
* **Feasibility:** **100% Feasible** (All providers offer persistent hobby tiers adequate for MVP testing).

---

### Detailed Cost & Infrastructure Matrix

| Category | Recommended Tool / Resource | Cost Structure (MVP Stage) | Cost Structure (Scale / 1k Users) | Feasibility Rating |
| --- | --- | --- | --- | --- |
| **Backend Hosting** | Render / Railway (FastAPI container) | **$0 / mo** (Free Hobby Tier) | ~$7 - $20 / mo | **High** |
| **Frontend Hosting** | Vercel / Cloudflare Pages | **$0 / mo** (Free Tier) | $0 - $20 / mo | **High** |
| **Database & Auth** | Supabase (PostgreSQL + Auth) | **$0 / mo** (500MB DB Free Tier) | $25 / mo | **High** |
| **LLM Inference** | Groq Cloud API (`llama-3.1-8b`) | **$0 / mo** (14,400 daily requests free) | Pay-as-you-go (~$0.05 / 1M tokens) | **High** |
| **Market Data Feed** | Finnhub / `yfinance` API | **$0 / mo** (60 calls/min free) | $50 - $150 / mo (Commercial feeds) | **High** |
| **Mobile Runtime** | Capacitor CLI | **$0** (Open Source) | $0 | **High** |
| **Developer Accounts** | Apple Developer / Google Play | **$0** (Web-only) / **$124** (App stores) | $99/yr (Apple) + $25 one-time (Google) | **Medium** |
| **TOTAL ESTIMATED COST** | — | **$0 - $124 (One-time for Stores)** | **~$32 - $115 / month** | **High** |

---

### Industry Standards & References

To align your architecture and code structure with quantitative finance and software engineering best practices, consult these industry standards:

#### 1. Quantitative Machine Learning & Feature Engineering

* **Reference:** Advances in Financial Machine Learning (Marcos López de Prado)
* **Standard:** Follow best practices regarding cross-validation for time-series data (Purged Group TimeSeries Split) to avoid data leakage and lookahead bias during model training.

#### 2. Portfolio Sizing & Modern Portfolio Theory

* **Reference:** PyPortfolioOpt Open-Source Documentation
* **Standard:** Implement Mean-Variance Optimization using quadratic programming and apply discrete allocation algorithms to convert weights into exact integer share counts.

#### 3. API Design & Security Architecture

* **Reference:** OWASP API Security Top 10 Standards
* **Standard:** Implement stateless JWT authentication, enforce rate-limiting middleware on public endpoints, and ensure no third-party API keys are embedded within client-side binaries.

#### 4. Cross-Platform Mobile Packaging

* **Reference:** Capacitor Documentation & Architecture Guide
* **Standard:** Bridge web applications to native mobile APIs through clean web views, leveraging native system biometrics (Face ID) and local storage adapters for offline state persistence.
