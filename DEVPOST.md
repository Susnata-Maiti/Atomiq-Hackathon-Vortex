# Vortex: Hybrid Quantum-Classical Term Deposit Campaign Pipeline

## Tagline
**Vortex: End-to-End Hybrid Quantum-Classical Pipeline for High-Precision Customer Conversion, Constrained QAOA Selection, and Quantum Campaign Risk Simulation.**

---

## Inspiration

In retail banking, commercial customer acquisition campaigns represent a high-stakes balancing act. Direct marketing calls are expensive in staff hours and customer goodwill; contacting every customer indiscriminately burns operating budget and frustrates clients. Conversely, naive greedy heuristics, such as calling prospects with the highest predicted subscription scores, ignore operational realities: contact costs vary significantly across communication channels, branch consultation capacity is strictly limited, and conversion rates exhibit stochastic downside risk.

When the **Atomiq Hackathon (part of the global Qiskit Fall Fest 2026)** challenged us to build a **fully connected, three-stage hybrid quantum-classical pipeline**, where machine learning prediction errors in Stage 1 directly propagate into combinatorial portfolio selection in Stage 2, which in turn defines an amplitude-encoded quantum simulation of campaign risk in Stage 3, we were inspired to architect **Vortex**.

Our vision was to create a production-grade algorithmic decision engine that demonstrates how near-term quantum algorithms (QML kernel methods, QAOA combinatorial optimization, and parameterized quantum state preparation) can be integrated with classical statistical rigor to deliver superior business value under tight operational constraints.

---

## What It Does

**Vortex** unifies quantum machine learning, combinatorial quantum optimization, and stochastic quantum simulation into an autonomous three-stage pipeline:

```
[Stage 1: Predict]
   |--> 300 Labeled Training Customers (bank.csv dataset)
   |--> Preprocessing Pipeline (StandardScaler + OneHotEncoder on Train only)
   |--> Classical Baseline: Calibrated Logistic Regression (Platt Sigmoid)
   |--> Quantum Classifier: Qiskit ZZFeatureMap Hilbert Space Kernel + QSVC
   |--> 5-Fold Stratified Cross-Validation (Zero Test Set Leakage)
   |--> Predicts Continuous Subscription Probabilities for 100 Test Prospects
   |--> Ranks Candidates (Tie-breaker: customer_id) -> Top 10 Candidate Pool
        |
        v
[Stage 2: Select]
   |--> Merges Top 10 Candidates with Operational Data (Cost, Deposit, Capacity)
   |--> Expected Net Value Objective: V_i = p_i * Deposit_i - Cost_i
   |--> Constraints: Exactly 6 Customers, Total Cost <= 25, Total Capacity <= 22
   |--> QUBO & 10-Qubit Ising Hamiltonian Formulation
   |--> Quantum Optimization: QAOA (p=2 layers, COBYLA optimizer, AerSimulator)
   |--> Exact Classical Benchmark: Exhaustive Brute-Force (C(10,6) = 210 combos)
   |--> Optimality Gap: 0.3231 (QAOA 28.46 vs 28.78 Global Optimum)
   |--> Output: 6 Optimal Customer IDs (C0170, C0327, C0205, C0372, C0272, C0005)
        |
        v
[Stage 3: Simulate]
   |--> 6 Selected Customers with Stage 1 Conversion Probabilities
   |--> Amplitude Encoding: Ry(theta_i)|0> with theta_i = 2 * arcsin(sqrt(p_i))
   |--> 6-Qubit Quantum Circuit (AerSimulator, 10,000 shots)
   |--> Success Condition: Measuring >= 3 qubits reading 1 (Hamming weight >= 3)
   |--> NISQ Noise Modeling (Depolarizing + Readout Error) & Readout Mitigation
   |--> Analytical Benchmark: Exact Poisson Binomial Distribution (64 basis states)
   |--> Classical Benchmark: Monte Carlo Simulation (100,000 Bernoulli trials)
   |--> Statistical Audit: Shot-noise Z-score = 1.62 sigma (Statistically consistent)
```

### Executive Results Summary

* **Stage 1 Top 10 Candidates:** `C0170, C0134, C0208, C0327, C0205, C0053, C0372, C0338, C0272, C0005` (calibrated probabilities: 0.2239 to 0.3767).
* **Stage 2 Final 6 Selected Customers:** **`C0170, C0327, C0205, C0372, C0272, C0005`**.
* **Budget Consumed:** **10.0 / 25.0 units** (leaving 60% of budget in reserve).
* **Capacity Consumed:** **13.0 / 22.0 units** (well within branch capacity).
* **Expected Net Campaign Value ($Z$):** **\$28.46** (Classical Brute-Force Global Optimum: **\$28.78**; **Optimality Gap:** 0.3231, a 1.12% relative gap).
* **Stage 3 Exact Conversion Probability $P(\ge 3)$:** **18.6801%** (exact Poisson binomial reference).
* **Stage 3 Quantum Estimate (Ideal Noiseless):** **19.3100%** ($\Delta = 0.006299$, within $1.62\sigma$ shot noise).
* **Stage 3 Quantum Estimate (Noisy Mitigated):** **19.2745%** ($\Delta = 0.005944$).
* **Stage 3 Classical Monte Carlo (100k Trials):** **18.7700%** ($\Delta = 0.000899$).

---

## How We Built It

Vortex was built with **Python 3.14**, **Qiskit 2.6.2**, **Qiskit Aer 0.18.2**, **Scikit-Learn 1.9.1**, **SciPy 1.18.1**, **Pandas**, **NumPy**, and **Matplotlib**.

### 1. Stage 1: Mathematical Formulation & Quantum Kernel Machine
To adhere strictly to hackathon rules, all feature transformations (StandardScaler for 6 numerical attributes and OneHotEncoder for 9 categorical attributes, giving 49 processed features) were fitted **strictly on the 300 training customers** and only then applied to the test customers, so no test-set information reaches the models. The transformer is fitted once on the training set and the transformed matrix is then split into the cross-validation folds; no labels and no test data are used in the fit.

* **Classical Baseline:** A class-weighted Logistic Regression (L2 penalty). The final model is wrapped in Platt sigmoid calibration (`CalibratedClassifierCV(cv=5)`); the cross-validation benchmark below evaluates the class-weighted model before calibration.
* **Quantum Kernel Classifier (QSVC):** High-dimensional feature maps project classical data into a Hilbert space where nonlinear boundaries can become linearly separable. We projected the 49 preprocessed features down to 4 principal components using PCA, scaled them to $[0, \pi]$, and applied Qiskit's `ZZFeatureMap(feature_dimension=4, reps=2, entanglement='linear')`:

$$
|\phi(x)\rangle = U_{\Phi(x)} |0\rangle^{\otimes 4} = \prod_{d} \exp\left(i \sum_{j} x_j Z_j + \sum_{j < k} (\pi - x_j)(\pi - x_k) Z_j Z_k \right) H^{\otimes 4} |0\rangle^{\otimes 4}
$$

The quantum fidelity kernel matrix is evaluated via exact statevector overlaps:

$$
K_{ij} = |\langle \phi(x_i) | \phi(x_j) \rangle|^2
$$

We trained a Support Vector Classifier on $K$ and calibrated its decision values with Platt scaling.

* **Hybrid Ensembling:** We combined the calibrated quantum-kernel probabilities with the calibrated linear baseline using fixed weights ($w_{\text{quantum}} = 0.35$, $w_{\text{classical}} = 0.65$) to produce continuous subscription probabilities. The larger weight sits on the classical model because it is the stronger ranker (see the table below).

#### 5-Fold Stratified Cross-Validation Benchmark

| Metric | Classical Baseline | Quantum Kernel QSVC |
| :--- | :---: | :---: |
| **ROC-AUC** | 0.6485 | 0.4916 |
| **PR-AUC (Average Precision)** | 0.2553 | 0.1803 |
| **Precision@10** | 0.1800 | 0.0600 |
| **Recall@10** | 0.2571 | 0.0857 |
| **Brier Score (lower is better)** | 0.2026 | 0.1429 |
| **Log Loss** | 0.5957 | 0.6000 |

The classical baseline is the stronger ranker on this small 300-customer training set. The QSVC's ROC-AUC of 0.49 is at chance level, so its lower Brier score should not be read as better predictive skill.

### 2. Stage 2: Constrained QAOA Optimization & Classical Brute Force
With $N = 10$ candidates, the bank must select exactly $K = 6$ customers to maximize expected net value while satisfying total contact cost $\le 25$ and operational capacity $\le 22$.

* **QUBO Minimization Formulation:**
  With $V_i = p_i d_i - c_i$, penalty weights $P_k = 18.0$, $P_{\text{cost}} = 2.5$, $P_{\text{cap}} = 2.5$:

$$
\min_{x \in \{0, 1\}^{10}} H_{\text{QUBO}}(x) = -\sum_{i=0}^9 V_i x_i + P_k \left(\sum_{i=0}^9 x_i - 6\right)^2 + P_{\text{cost}} \left[\max\left(0, \sum_{i=0}^9 c_i x_i - 25\right)\right]^2 + P_{\text{cap}} \left[\max\left(0, \sum_{i=0}^9 h_i x_i - 22\right)\right]^2
$$

* **Ising Spin Mapping:**
  Using the change of variables $x_i = \frac{1 - Z_i}{2}$ where $Z_i \in \{+1, -1\}$ are Pauli-$Z$ operators:

$$
H_C = \sum_{i=0}^9 \eta_i Z_i + \sum_{i < j} J_{ij} Z_i Z_j + \text{offset}
$$

  The cardinality penalty maps exactly (giving $J_{ij} = P_k/2$). For the budget and capacity penalties the Hamiltonian uses linear surrogate terms in $\eta_i$; the exact hinge penalties are applied when each sampled bitstring is scored.

* **QAOA Circuit & Variational Optimization:**
  We implemented a 10-qubit, $p=2$ layer QAOA state preparation circuit:

$$
|\gamma, \beta\rangle = \prod_{l=1}^p \left( e^{-i \beta_l \sum_i X_i} e^{-i \gamma_l H_C} \right) |+\rangle^{\otimes 10}
$$

  The variational parameters $\vec{\gamma}, \vec{\beta}$ were optimized using SciPy's COBYLA over 150 iterations on `AerSimulator` (2,048 shots per evaluation), and the optimized circuit was then sampled with 10,000 shots.

* **Verification Against Classical Optimum:**
  We evaluated all $\binom{10}{6} = 210$ combinations by exhaustive classical search. From the QAOA samples we take the best feasible bitstring, which is a high-value portfolio:

$$
x^* = (1, 0, 0, 1, 1, 0, 1, 0, 1, 1) \implies \{\text{C0170, C0327, C0205, C0372, C0272, C0005}\}
$$

  Its expected net value is **\$28.46**, against the classical brute-force optimum of **\$28.78** (an **optimality gap of 0.3231**, or 1.12% relative), while satisfying both constraints (Budget: 10/25, Capacity: 13/22). The brute-force optimum differs by one customer (C0053 instead of C0005).

### 3. Stage 3: Amplitude-Encoded Quantum Risk Simulation
For the 6 chosen customers, we simulated the probability that at least 3 subscribe ($w(b) \ge 3$).

* **Quantum Amplitude Encoding:**
  Instead of expensive multi-qubit adder circuits, we initialized a 6-qubit register in $|0\rangle^{\otimes 6}$ and applied single-qubit $R_y(\theta_i)$ rotations with rotation angles $\theta_i = 2 \arcsin(\sqrt{p_i})$:

$$
R_y(\theta_i) |0\rangle = \cos(\theta_i/2)|0\rangle + \sin(\theta_i/2)|1\rangle = \sqrt{1 - p_i}|0\rangle + \sqrt{p_i}|1\rangle
$$

  Measuring qubit $i$ in the computational basis yields state $|1\rangle$ with exact probability $p_i$.

* **Transpilation Metrics:**
  * Logical & Physical Qubits: 6
  * Original & Transpiled Circuit Depth: 2 (1 layer of $R_y$ gates + 1 measurement layer)
  * Gate Counts: 6 single-qubit $R_y$ gates, 0 two-qubit gates, 0 SWAP gates

* **Simulation & Readout Error Mitigation:**
  We measured 10,000 shots on `AerSimulator`. In addition to ideal noiseless simulation, we constructed a synthetic NISQ noise model (single-qubit depolarizing error $\lambda = 0.001$ and asymmetric readout error $P(0|1)=0.02$, $P(1|0)=0.01$). A simple readout correction (rescaling the noisy estimate by $1/1.02$) reduced the noisy estimation bias from $+0.98\%$ to $+0.59\%$; full confusion-matrix inversion or M3 would be the hardware-grade alternative.

* **Analytical Benchmark:**
  We computed the exact analytical probability using the Poisson Binomial distribution summing over all 64 basis states:

$$
P_{\text{exact}}(\ge 3) = \sum_{b \in \{0, 1\}^6: \sum b_i \ge 3} \prod_{i=0}^5 p_i^{b_i} (1 - p_i)^{1 - b_i} = 18.6801\%
$$

  The ideal quantum simulation yielded **19.3100%**, differing by $0.006299$. With theoretical shot-noise standard deviation

$$
\sigma = \sqrt{\frac{p(1-p)}{S}} = 0.003898,
$$

  the error corresponds to a Z-score of **$1.62\sigma$**, consistent with quantum projection noise.

---

## Challenges We Ran Into

1. **Test Set Customer ID Alignment & Traceability:**
   In the challenge workbook, `Stage1_Test` was released with explicit `customer_id` tracking (`C0231, C0345, ...`), which cross-references `Stage2_Data` and `Stage1_Train`. We adapted our ingestion pipeline to automatically detect, validate, and bind these official IDs end-to-end across prediction, optimization, and quantum simulation without index loss.
2. **Cardinality and Multi-Constraint QUBO Balancing:**
   Mapping an exact equality constraint ($\sum x_i = 6$) alongside two inequality constraints ($\sum c_i x_i \le 25$ and $\sum h_i x_i \le 22$) to an Ising Hamiltonian is notoriously difficult: if penalty coefficients are too low, the solver returns invalid bitstrings; if too high, the problem Hamiltonian is dominated by penalties, obscuring the objective. We derived an exact expansion for the cardinality penalty:

$$
\left(\sum_{i=0}^9 x_i - 6\right)^2 = -11 \sum_{i=0}^9 x_i + 2 \sum_{i < j} x_i x_j + 36
$$

   We handled the budget and capacity penalties with linear surrogate terms in the Hamiltonian and enforced the exact limits when scoring and filtering sampled bitstrings.
3. **Bitstring Endianness in Qiskit:**
   Qiskit indexes classical bitstrings in reverse order ($q_{n-1} q_{n-2} \dots q_0$), whereas business arrays follow index order ($q_0 \dots q_{n-1}$). We implemented strict bit-reversal transformations in our decoders to avoid inverted customer mappings.

---

## Accomplishments That We're Proud Of

* **High-Quality Constrained Quantum Optimization:** Our QAOA formulation reached a **1.12% relative gap (0.3231 gap)** against the exhaustive classical optimum across all 210 subsets while satisfying both the budget and capacity constraints.
* **Full End-to-End Execution in Under 10 Seconds:** The entire pipeline (feature scaling, 5-fold CV, quantum kernel calculations, QAOA optimization, 10,000-shot Aer simulation, and chart rendering) executes in approximately 9 seconds on a standard computer.
* **100% Self-Contained, Pre-Rendered Jupyter Notebook:** [`vortex_pipeline.ipynb`](https://github.com/Susnata-Maiti/Atomiq-Hackathon-Vortex/blob/main/vortex_pipeline.ipynb) contains all 27 markdown and code cells with every metric, ASCII circuit diagram, and dual-panel visualization pre-rendered for immediate viewing.
* **Comprehensive Test Suite:** Our automated Pytest suite validates all schema constraints, budget limits, and quantum accuracy bounds with a 100% pass rate.

---

## What We Learned

* **Amplitude Encoding vs. Arithmetic Quantum Circuits:** Preparing independent Bernoulli probabilities directly via single-qubit rotations $R_y(2 \arcsin(\sqrt{p_i}))$ enables shallow, NISQ-friendly depth-2 circuits that avoid noisy multi-qubit adder gates.
* **Probability Calibration is Essential for QML:** Quantum kernel classifiers naturally output uncalibrated SVM margins. Applying Platt sigmoid calibration is crucial before probabilities can be fed into downstream financial objective functions.
* **Quantum-Classical Symbiosis:** Quantum algorithms work best embedded within a hybrid workflow, leveraging classical techniques for heavy data munging and using quantum circuits for combinatorial exploration and stochastic superposition sampling.

---

## What's Next for Vortex

* **Execution on Physical IBM Quantum QPUs:** Running the Stage 3 simulation circuit on IBM Quantum hardware (e.g., `ibm_brisbane` or `ibm_kyoto`) via Qiskit Runtime `SamplerV2` with Dynamical Decoupling (DD) and Twirled Readout Error Mitigation (TREX).
* **Subspace-Preserving XY Mixers:** Implementing a Dicke-state $|D^n_k\rangle$ initialization with Givens-rotation XY mixers in QAOA to restrict the quantum walk strictly to the Hamming weight subspace $\sum x_i = 6$, removing penalty tuning entirely.
* **Multi-Product Banking Portfolios:** Expanding Vortex to joint cross-sell campaigns (term deposits, credit cards, mortgages) where customer decisions are correlated via parameterized entangling gates ($R_{zz}$ or CNOTs).

---

## Built With

* `python`
* `qiskit`
* `qiskit-aer`
* `qaoa`
* `quantum-machine-learning`
* `quantum-computing`
* `quantum-circuits`
* `quantum-kernel`
* `scikit-learn`
* `scipy`
* `numpy`
* `pandas`
* `matplotlib`
* `openpyxl`
* `qubo`
* `combinatorial-optimization`
* `cross-validation`
* `monte-carlo-simulation`
* `poisson-binomial`
* `fintech`
* `financial-modeling`
* `jupyter-notebook`
* `pytest`
