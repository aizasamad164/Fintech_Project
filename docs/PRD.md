## 3. Functional Requirements

### 3.1 User Management & Personalization Engine (F-01)

* **FR-1.1:** The system shall support user registration and authentication using email/password credentials or OAuth providers via JWT tokens.
* **FR-1.2:** The system shall allow users to input and dynamically modify a target cash investment budget (e.g., $100 to $10,000+).
* **FR-1.3:** The system shall provide three selectable risk strategies: Conservative, Balanced, and Aggressive.
* *Conservative:* Weights allocations toward lower-volatility, higher market-capitalization equities.
* *Balanced:* Distributes allocations across established core assets and moderate-growth equities.
* *Aggressive:* Maximizes allocation toward higher-volatility, high-growth potential equities.
* **FR-1.4:** The system shall allow users to filter allocations by specific individual sectors (e.g., Technology, Healthcare, Renewable Energy) or select a Combined Multi-Sector view.


### 3.2 Data Ingestion & Preprocessing Pipeline (F-02)

* **FR-2.1:** The system shall fetch historical daily Close, Open, High, Low, and Volume (OHLCV) candle data covering up to 15 years for candidate sector stocks.
* **FR-2.2:** The system shall calculate fundamental ratios (P/E ratio, Market Capitalization) for candidate stock pools.
* **FR-2.3:** The system shall compute technical indicators, including RSI (14-day), MACD, Exponential Moving Averages (50-day / 200-day EMA), and Average True Range (ATR) using `pandas-ta`.
* **FR-2.4:** The system shall store fetched market data in an in-memory cache to ensure compliance with external API rate limits (e.g., maximum 60 requests/minute).


### 3.3 Quantitative & ML Signal Generation Engine (F-03)

* **FR-3.1:** The system shall execute SciPy signal processing (`scipy.signal.find_peaks`) to detect price support, resistance, and geometric chart breakout formations.
* **FR-3.2:** The system shall pass technical indicator matrices through sector-specialized LightGBM/XGBoost classification models to compute a probability score $P(\text{Bullish})$ for each candidate stock.
* **FR-3.3:** The system shall utilize sector-specific specialized models for individual industry inputs and fall back to a combined general model when multi-sector allocation is requested.


### 3.4 Portfolio Optimization & Allocation Engine (F-04)

* **FR-4.1:** The system shall evaluate candidate stock confidence scores and historical covariance matrices to solve discrete mean-variance optimization using `scipy.optimize` or `PyPortfolioOpt`.
* **FR-4.2:** The system shall translate calculated asset weights $w_i$ into concrete dollar amounts and discrete share counts based on the user's total budget $B$:
$$\text{Amount}_i = B \times w_i, \quad \text{Shares}_i = \left\lfloor \frac{\text{Amount}_i}{\text{Price}_i} \right\rfloor$$
* **FR-4.3:** The system shall compute the historical 1-year performance percentage for the generated portfolio and project an illustrative monetary return based on the user's budget.


### 3.5 LLM Explanation & Plain-English Translation Engine (F-05)

* **FR-5.1:** The system shall compile quantitative allocation vectors, technical indicators, and sector tags into a structured JSON context payload.
* **FR-5.2:** The system shall submit the JSON context to the Groq Cloud API (`llama-3.1-8b`) to generate 3 plain-language bullet-point explanations detailing the rationale behind the portfolio structure.
* **FR-5.3:** The system shall append an explicit educational boundary disclaimer to every recommendation output stating that the result is an educational simulation, not regulated financial advice.


### 3.6 Cross-Platform User Interface (F-06)

* **FR-6.1:** The user interface shall render interactive allocation pie charts, stock breakdown tables (showing ticker, percentage, dollar value, and share counts), and risk ratings.
* **FR-6.2:** The system shall support real-time user adjustment of risk toggles and budget inputs without requiring full page reloads.
* **FR-6.3:** The UI shall adapt responsively to screen dimensions, converting dense data tables into swipeable cards on screens $\le 768\text{px}$.

---

## 4. Non-Functional Requirements

### 4.1 Performance Requirements

* **NFR-1.1 (Latency):** The complete end-to-end execution pipeline—from user request submission to the rendering of portfolio tables and LLM explanations—shall complete within **3.0 seconds**.
* **NFR-1.2 (CPU Efficiency):** Signal generation and portfolio allocation calculations shall run entirely on standard vCPU hosting instances without requiring dedicated GPU infrastructure.
* **NFR-1.3 (Throughput):** The system shall support up to 50 concurrent user allocation requests using asynchronous FastAPI request handlers.

### 4.2 Security & Data Privacy Requirements

* **NFR-2.1 (API Key Vaulting):** No external third-party API keys (Groq, Finnhub, Polygon) shall be exposed to or embedded within client-side web or mobile application bundles. All external requests must be proxied through the backend.
* **NFR-2.2 (Transport Encryption):** All communication between client applications, API gateways, databases, and third-party services shall be encrypted using TLS 1.3 / HTTPS protocols.
* **NFR-2.3 (Password Security):** User passwords shall be salted and hashed using Bcrypt or Argon2 algorithms before storage.
* **NFR-2.4 (Data Minimization):** The platform shall store no banking details, payment card details, brokerage credentials, or custodial financial holdings.

### 4.3 Reliability & Fault Tolerance

* **NFR-3.1 (Graceful Degradation):** If the external LLM translation service (Groq API) times out or fails, the platform shall deliver the completed quantitative portfolio allocation table alongside a default static explanation.
* **NFR-3.2 (Data Fallback):** If live market data feeds become unresponsive, the backend shall fall back to cached daily close market data without throwing unhandled client errors.

### 4.4 Software Quality Attributes

* **NFR-4.1 (Usability):** Financial terms (e.g., volatility, diversification, $P/E$ ratio) displayed in the user interface shall be accompanied by contextual tooltip definitions written for beginners.
* **NFR-4.2 (Portability):** The application frontend shall maintain identical feature functionality across Desktop Web (React) and Mobile OS environments (iOS/Android wrapped via Capacitor).
