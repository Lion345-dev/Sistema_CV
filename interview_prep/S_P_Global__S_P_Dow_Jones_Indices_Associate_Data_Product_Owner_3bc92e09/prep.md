# Interview Preparation Briefing: Associate Data Product Owner (Equity Data)
**Candidate:** Luis Yael Carmona Gutiérrez  
**Company:** S&P Global (S&P Dow Jones Indices) — Mexico City Hub  
**Job ID:** 330713  

---

## Sobre la empresa

S&P Global (NYSE: SPGI) is a global provider of financial information, benchmarks, analytics, and workflow solutions. **S&P Dow Jones Indices (SPDJI)** operates as its primary index licensing division, producing iconic global benchmarks such as the S&P 500, the Dow Jones Industrial Average, and local equity indices across global markets.

* **Industry/Market:** Financial market infrastructure, financial data feeds, and benchmark calculation services.
* **Core Business Unit:** The *Equity Data Value Stream* processes data on global listed equities, underlying share types, identification standards (ISIN, CUSIP, SEDOL), and corporate actions (rights offerings, stock splits, dividends, spinoffs).
* **Operational Footprint:** S&P Global employs over 40,000 employees globally. The Mexico City technology/data hub operates as a core operational engine supporting global product streams, market calculation pipelines, and index maintenance. *(Note: Exact team size within the CDMX Equity Data stream is proprietary and varies by operational shifts).*

---

## Cultura y qué valoran

* **Absolute Precision & Zero-Tolerance for Errors:** A miscalculated stock split ratio or missed ex-date corrupts index calculations globally, exposing clients (ETFs, portfolio managers) to tracking error and financial risk.
* **Transition to Automation ("Citizen Developer" Culture):** Shift from manual spreadsheet processing to automated ETL, SQL querying, Python pipelines, Databricks analytics, and Power Automate workflows.
* **Process Ownership & Data Governance:** Candidates are expected to own the audit trail end-to-end, validating supporting documentation, logging sources, and ensuring compliance.
* **Structured Cross-Functional Communication:** High-velocity collaboration across global Index Design, Commercial, Technology, and Production teams.

---

## Preguntas probables de entrevista

1. **Corporate Action Mechanics & Index Math:**  
   *"Walk me through a complex corporate action (e.g., a rights offering or spin-off). How does it alter share counts, market capitalization, and the index divisor?"*

2. **Data Discrepancy & Vendor Reconciliation:**  
   *"Suppose Bloomberg and Refinitiv report conflicting ex-dates or adjustment ratios for a Mexican equity's dividend. What steps do you take to verify, document, and commit the correct entry under tight market-open deadlines?"*

3. **Data Quality & Technical Validation (SQL/Python):**  
   *"How would you write a SQL query or Python script to automatically detect anomalies or duplicate records in a relational database containing millions of daily corporate action logs?"*

4. **Workflow Automation & Process Improvement:**  
   *"Can you share an example of a manual, repetitive data workflow you identified, redesigned, and automated using Python, Power Automate, or SQL?"*

5. **Stakeholder Communication Under Pressure:**  
   *"How do you prioritize and communicate an urgent data issue to global production teams when market close is approaching and an index rebalance is pending?"*

6. **Data Product Governance:**  
   *"How do you ensure auditability and data governance when updating proprietary data feeds that feed downstream quantitative models?"*

---

## Cómo conectar su experiencia

Connect your actual background directly to the requirements:

* **Python & Automation Capability:**  
  * *Context to leverage:* **AutoInvest Pro** (Independently built Python platform with 12 completed modules).  
  * *How to present:* Highlight how you designed programmatic modules in Python to pull, parse, and process financial data. Mention how this experience prepares you to automate corporate action validation scripts and work within Databricks/Python pipelines at SPDJI.

* **Financial Markets & Securities Domain Knowledge:**  
  * *Context to leverage:* **Figura 3 (Bursatrón) AMIB** (In Progress) and **Fintech y Data Science** (IEB Madrid).  
  * *How to present:* Frame your study of Mexican capital markets, equity structures, and financial data standards directly against equity corporate action handling (splits, dividends, ISIN/CUSIP tracking).

* **Quantitative & Data Engineering Foundation:**  
  * *Context to leverage:* **Ingeniero Citizen Data Scientist** (Tec de Monterrey).  
  * *How to present:* Emphasize your structured knowledge of relational databases, SQL queries, data governance rules, and ETL validation. Relate this directly to SPDJI's data quality auditing requirements.

* **Operational Discipline, Documentation & Communication:**  
  * *Context to leverage:* **Administrative Assistant at CAVII** and **Event Coordinator at COPARMEX**.  
  * *How to present:* Cite your daily responsibility for administrative accuracy, log verification, structured record-keeping, and cross-team coordination. Frame this as evidence of your meticulous attention to detail and ability to work under deadlines.

* **Professional English Fluency:**  
  * *Context to leverage:* **English Testing and Assessment Workshop** (35 hrs, Quick Learning).  
  * *How to present:* Demonstrate clear, fluent articulation of technical and financial concepts during the interview to show readiness for daily collaboration with global teams.

---

## Preguntas inteligentes que puede hacer

1. *"How is the Equity Data stream currently balancing legacy SQL infrastructure with cloud migration platforms like Databricks for real-time corporate action ingestion?"*
2. *"When unexpected corporate action edge cases occur—such as complex multi-jurisdictional restructurings—what is the standard escalation workflow between the Data Product Owner, Index Design, and Production teams?"*
3. *"What are the primary performance metrics for an Associate Data Product Owner in this hub during the first 6 to 12 months (e.g., error rate reduction, SLA compliance, or workflow automation milestones)?"*
4. *"To what extent are Associate Data Product Owners encouraged to introduce low-code/Python automation into daily operations versus following pre-established ETL maintenance schedules?"*

---

## Antes de la entrevista, verifica

* **Index Calculation Basics:** Review how stock splits, cash dividends, special dividends, and rights offerings affect index divisors and index market cap (S&P Dow Jones Indices corporate actions methodology documentation is publicly available online).
* **Identifier Knowledge:** Verify your understanding of security identifiers (ISIN, CUSIP, SEDOL, Ticker formats).
* **Recent Market Events:** Check for any major recent corporate action edge cases in Mexican or US equity markets (e.g., major spin-offs or restructurings) that could serve as discussion points.
* **S&P Global Recent News:** Search for recent updates regarding SPDJI's regional expansion in Latin America or product launches in ESG/Thematic indices to speak knowledgeably about company priorities.