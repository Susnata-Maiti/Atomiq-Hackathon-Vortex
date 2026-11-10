# Vortex: Hybrid Quantum-Classical Term Deposit Campaign Pipeline
### Atomiq Hackathon (Qiskit Fall Fest 2026) Technical Report

> **Tagline:** *Vortex: End-to-End Hybrid Quantum-Classical Pipeline for High-Precision Customer Conversion, Constrained QAOA Selection, and Quantum Campaign Risk Simulation.*

---

## 1. Executive Summary & Challenge Solution

A commercial bank faces a strategic marketing optimization challenge: randomly calling customers or simply picking the highest-scoring leads is inefficient and ignores operational cost, staff capacity constraints, and downside risk.

**Vortex** delivers a three-stage connected hybrid quantum-classical pipeline:
1. **Stage 1 (Predict):** A hybrid classifier fusing a **Qiskit ZZFeatureMap Quantum Kernel Support Vector Classifier (QSVC)** with a **Calibrated Logistic Regression** baseline. Evaluated via **5-Fold Stratified Cross-Validation** on training data only to rank 100 test prospects and isolate the top 10 candidates.
2. **Stage 2 (Select):** A constrained binary optimization engine formulating a Quadratic Unconstrained Binary Optimization (**QUBO**) and Ising Hamiltonian solved with the **Quantum Approximate Optimization Algorithm (QAOA)** ($p=2$ layers) and benchmarked against an exact classical solver ($\binom{10}{6} = 210$ combinations). The best feasible QAOA sample has an **optimality gap of 0.3231** (1.12% relative gap): **\$28.46** expected net value versus the **\$28.78** classical global optimum, with budget and capacity limits satisfied.
3. **Stage 3 (Simulate):** A 6-qubit circuit using **amplitude encoding** ($R_y(\theta_i)$ rotations) to simulate the probability that at least 3 of the 6 selected customers subscribe. Validated against an **exact analytical Poisson Binomial calculation** ($2^6 = 64$ basis states) and a **100,000-trial classical Monte Carlo simulation**.

### Final Challenge Deliverables Summary

| Parameter | Vortex Value | Validation & Benchmark |
| :--- | :--- | :--- |
| **Stage 1 Top 10 Candidates** | `C0170, C0134, C0208, C0327, C0205, C0053, C0372, C0338, C0272, C0005` | Probabilities: 22.39% to 37.67% |
| **Stage 2 Final 6 Selected to Contact** | **`C0170, C0327, C0205, C0372, C0272, C0005`** | Feasible ($K=6$ from top 10) |
| **Total Campaign Budget Consumed** | **10.0 units** | $\le 25.0$ Budget Limit (**Feasible**) |
| **Total Operational Capacity Consumed** | **13.0 units** | $\le 22.0$ Capacity Limit (**Feasible**) |
| **Expected Net Campaign Value ($Z$)** | **\$28.46** | **Classical Global Optimum: \$28.78** |
| **Stage 2 Optimality Gap ($Z_{\text{opt}} - Z_{\text{QAOA}}$)** | **0.3231** (1.12% rel. gap) | Best feasible QAOA sample |
| **Stage 3 Exact Analytical Probability $P(\ge 3)$** | **18.6801%** | Poisson Binomial exact reference |
| **Stage 3 Quantum Estimate (Ideal Noiseless)** | **19.3100%** | $\Delta = 0.006299$ ($1.62\sigma$ shot noise) |
| **Stage 3 Quantum Estimate (Noisy Mitigated)** | **19.2745%** | $\Delta = 0.005944$ (simple readout rescaling) |
| **Stage 3 Monte Carlo Estimate (100k Trials)** | **18.7700%** | $\Delta = 0.000899$ |

---

## 2. Methodology & Technical Depth

```
                 VORTEX HYBRID QUANTUM-CLASSICAL ARCHITECTURE

 [Stage1_Train (300)]                               [Stage1_Test (100)]
         |                                                   |
         v                                                   v
 [Feature Preprocessing]                            [Feature Transform]
 (Scalers + Encoders fitted on Train only)                   |
         |                                                   |
         +--------------------------+                        |
         |                          |                        |
         v                          v                        |
 [Classical Baseline]      [Quantum Kernel QSVC]             |
 (Calibrated LogReg)       (ZZFeatureMap, 4 qubits)          |
         |                          |                        |
         +------------+-------------+                        |
                      |                                      |
                      v                                      v
         [5-Fold Stratified CV] ------------> [Test Probability Prediction]
         (ROC-AUC, PR-AUC, Brier)                            |
                                                             v
                                                  [Rank Descending / Top 10]
                                                             |
+------------------------------------------------------------+
|
v
[Stage 2: Constrained Customer Selection]
Candidates Pool (N=10) <--- Merged with Stage2_Data (Cost, Deposit, Capacity)
Objective: Maximize Expected Net Value V_i = p_i * Deposit_i - Cost_i
Subject to: K = 6, Budget <= 25, Capacity <= 22
         |
         +-------------------------------------+
         |                                     |
         v                                     v
 [QUBO / Ising Formulation]           [Exact Classical Solver]
 min H(x) = -sum(V_i x_i) + P_k (sum x_i - 6)^2  Brute-force over all 210 combos
 + P_budget + P_capacity              Global optimum: Z* = $28.78
         |                                     |
         v                                     |
 [QAOA Circuit (p=2 layers)]                   |
 (Parametric Rx, Rzz, COBYLA)                  |
         |                                     |
         +-----------------+-------------------+
                           |
                           v
                [Best feasible QAOA sample]
                Selected: C0170, C0327, C0205, C0372, C0272, C0005
                           |
+--------------------------+
|
v
[Stage 3: Campaign Outcome Quantum Simulation]
6 Selected Customers with Stage 1 Probabilities
Qubit Encoding: |psi> = tensor_{i=0..5} [cos(theta_i/2)|0> + sin(theta_i/2)|1>]
where theta_i = 2 * arcsin(sqrt(p_i))
         |
         +-----------------------------------+-----------------------------------+
         |                                   |                                   |
         v                                   v                                   v
 [AerSimulator (10,000 shots)]       [Poisson Binomial Exact]            [Monte Carlo (100k)]
 Counts with Hamming weight >= 3     sum_{w(b) >= 3} prod p_i^b (1-p_i)  100,000 Bernoulli draws
 P_quantum = 19.31%                  P_exact = 18.68%                    P_MC = 18.77%
 (Z-score = 1.62 sigma)
```

### Stage 1: Subscription Prediction
- **Preprocessing:** Continuous features (`age`, `balance`, `day`, `campaign`, `pdays`, `previous`) are standardized with `StandardScaler`. Categorical features (`job`, `marital`, `education`, `default`, `housing`, `loan`, `contact`, `month`, `poutcome`) are encoded with `OneHotEncoder(handle_unknown='ignore')`. The transformer is **fitted only on the 300 training customers** and then applied to the test set, producing 49 processed features. It is fitted once and the transformed training matrix is then split into the cross-validation folds (no labels or test data are used in the fit).
- **Classical Model:** Balanced-weight Logistic Regression. The final model is wrapped in Platt sigmoid calibration (`CalibratedClassifierCV`, `cv=5`) to give well-behaved probabilities between 0 and 1. The cross-validation table below evaluates the class-weighted model before calibration.
- **Quantum Model:** Quantum Kernel Classifier (QSVC). The 49 features are reduced to 4 principal components by PCA and scaled to $[0,\pi]$. A Qiskit `ZZFeatureMap(feature_dimension=4, reps=2, entanglement='linear')` embeds each sample $x \in \mathbb{R}^4$ into a 16-dimensional complex Hilbert space:

$$
|\phi(x)\rangle = U_{\Phi(x)} |0\rangle^{\otimes 4}
$$

The quantum fidelity kernel matrix is computed via exact statevector overlaps:

$$
K_{ij} = |\langle \phi(x_i) | \phi(x_j) \rangle|^2
$$

It is used in a Support Vector Classifier whose decision values are calibrated with Platt scaling.
- **5-Fold Stratified Cross-Validation (means over folds):**

| Metric | Classical Baseline | Quantum Kernel QSVC |
| :--- | :---: | :---: |
| ROC-AUC | 0.6485 | 0.4916 |
| PR-AUC | 0.2553 | 0.1803 |
| Precision@10 | 0.1800 | 0.0600 |
| Recall@10 | 0.2571 | 0.0857 |
| Brier Score | 0.2026 | 0.1429 |
| Log Loss | 0.5957 | 0.6000 |

  The classical baseline is the stronger ranker. The QSVC's ROC-AUC of 0.49 is at chance level, so its lower Brier score should not be read as better skill.
- **Ensemble Inference:** A fixed-weight blend ($w_{\text{quantum}} = 0.35$, $w_{\text{classical}} = 0.65$), clipped to $[0.001, 0.999]$, gives the final probabilities. The larger weight is on the stronger classical model.

### Stage 2: Constrained Customer Selection
- **Operational Data:** The top 10 candidates are merged with `Stage2_Data` to compute Expected Net Value $V_i = p_i \cdot \text{deposit}_i - \text{cost}_i$.
- **QUBO Formulation:**

$$
\min_{x \in \{0, 1\}^{10}} H(x) = -\sum_{i=0}^9 V_i x_i + P_k \left(\sum_{i=0}^9 x_i - 6\right)^2 + P_{\text{cost}} \max\left(0, \sum c_i x_i - 25\right)^2 + P_{\text{cap}} \max\left(0, \sum h_i x_i - 22\right)^2
$$

  with $P_k = 18$, $P_{\text{cost}} = P_{\text{cap}} = 2.5$.
- **Ising Mapping:**
  Using $x_i = \frac{1 - Z_i}{2}$ where $Z_i \in \{+1, -1\}$:

$$
H_C = \sum_{i} \eta_i Z_i + \sum_{i < j} J_{ij} Z_i Z_j + \text{const}
$$

  The cardinality penalty maps exactly ($J_{ij} = P_k/2$). The budget and capacity penalties enter the Hamiltonian as linear surrogate terms; the exact hinge penalties are applied when each sampled bitstring is scored.
- **QAOA Circuit:** $p=2$ alternating layers of the problem unitary $e^{-i \gamma H_C}$ and the mixer $e^{-i \beta H_M}$ ($H_M = \sum X_i$), optimized with COBYLA (150 iterations, 2,048 shots per evaluation).
- **Decoding & Classical Benchmark:** The optimized circuit is sampled with 10,000 shots on `AerSimulator`. Each bitstring is decoded (reversing Qiskit's bit order) and scored, and the best *feasible* bitstring is reported. It is compared with brute-force enumeration of all $\binom{10}{6} = 210$ combinations:
  - QAOA selects: `['C0170', 'C0327', 'C0205', 'C0372', 'C0272', 'C0005']` ($Z = \$28.46$).
  - Classical brute-force optimum: `['C0170', 'C0327', 'C0205', 'C0053', 'C0372', 'C0272']` ($Z^* = \$28.78$).
  - Optimality gap: **0.3231** (1.12% relative gap). The two portfolios differ by one customer.
  - Budget: 10.0 / 25.0 units. Capacity: 13.0 / 22.0 units.

### Stage 3: Campaign Outcome Quantum Simulation
- **Quantum Register:** 6 qubits initialized in $|0\rangle^{\otimes 6}$.
- **Amplitude Encoding:** Qubit $i$ is rotated by $R_y(\theta_i)$ with $\theta_i = 2 \arcsin(\sqrt{p_i})$:

$$
R_y(\theta_i)|0\rangle = \cos(\theta_i/2)|0\rangle + \sin(\theta_i/2)|1\rangle = \sqrt{1 - p_i}|0\rangle + \sqrt{p_i}|1\rangle
$$

Measuring qubit $i$ in the computational basis yields 1 with exact probability $p_i$.
- **Circuit Transpilation Metrics:**
  - Logical Qubits: 6
  - Physical Qubits: 6
  - Original Circuit Depth: 2 ($R_y$ layer + measurement layer)
  - Transpiled Circuit Depth: 2
  - Single-Qubit Gates: 6 ($R_y$)
  - Two-Qubit Gates: 0
  - SWAP Gates: 0
- **Noise Model:** Single-qubit depolarizing error of $0.001$ on $R_y$ and asymmetric readout error ($P(1|0)=0.01$, $P(0|1)=0.02$). The mitigation applied is a simple rescaling of the noisy estimate by $1/1.02$.
- **Simulation Results:**
  - **Exact Poisson Binomial:** $P_{\text{exact}}(\ge 3) = 0.186801$ (18.68%)
  - **Noiseless Quantum Estimate (10k shots):** $P_{\text{quantum}} = 0.193100$ (19.31%), $\Delta = 0.006299$
  - **Noisy Quantum Estimate (Unmitigated):** $0.196600$, $\Delta = 0.009799$
  - **Noisy Quantum Estimate (Mitigated):** $0.192745$, $\Delta = 0.005944$
  - **Classical Monte Carlo (100k trials):** $P_{\text{MC}} = 0.187700$, $\Delta = 0.000899$
  - **Theoretical Shot Noise Standard Error:** $\sigma = \sqrt{\frac{p(1-p)}{S}} = \sqrt{\frac{0.1868 \cdot 0.8132}{10000}} = 0.003898$
  - **Statistical Consistency:** Quantum Z-score = $1.62\sigma$ ($< 2.0\sigma$), consistent with quantum projection noise.

---

## 3. Reproducibility & Execution Guide

### Environment & Recorded Seeds
- **Python Version:** 3.14.5
- **Qiskit Version:** 2.6.2
- **Qiskit Aer Version:** 0.18.2
- **Scikit-Learn Version:** 1.9.1
- **Recorded Seeds:**
  - Data Split Seed: `42`
  - Model Seed: `42`
  - Optimizer Seed: `42`
  - Simulator Seed: `42`
  - Transpiler Seed: `42`
  - Monte Carlo Seed: `42`

### Run End-to-End Pipeline
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run master pipeline (executes Stage 1, Stage 2, Stage 3 and outputs CSV files)
python run_pipeline.py

# 3. Run validation test suite
python -m pytest tests/test_pipeline.py
```

### Result Files Generated (Root-Level Deliverables)
All required deliverables are generated directly at the top level of the repository under both standard and competition-specified filenames:
1. **Stage 1 Predictions:** [`stage1_predictions.csv`](stage1_predictions.csv) and [`stage1_result.csv`](stage1_result.csv) (100 rows: `customer_id`, `predicted_probability`, `rank`, `top_10`), plus [`stage1_predictions.json`](stage1_predictions.json).
2. **Stage 2 Selection:** [`stage2_selection.csv`](stage2_selection.csv) and [`stage2_result.csv`](stage2_result.csv) (10 rows: top 10 candidates with inputs, selection flags, budget/capacity usage, QAOA objective, classical optimum, gap), plus [`stage2_selection.json`](stage2_selection.json).
3. **Stage 3 Simulation:** [`stage3_simulation.csv`](stage3_simulation.csv) and [`stage3_result.csv`](stage3_result.csv) (6 rows: selected IDs, qubit mapping, probabilities, angles, counts, quantum estimate, exact analytical probability, Monte Carlo probability, errors), plus [`stage3_simulation.json`](stage3_simulation.json).

### License
This project is open-source under the [MIT License](LICENSE).

---

## 4. Limitations & Business Recommendations

### Technical Limitations
1. **Quantum kernel performance:** In cross-validation the QSVC does not beat the classical baseline (ROC-AUC 0.49 versus 0.65), and the 0.35/0.65 ensemble weights are fixed rather than tuned. The training set has only 300 customers, so cross-validation estimates are noisy.
2. **Feature compression:** Compressing 49 preprocessed features to 4 principal components to match current NISQ qubit budgets loses finer-grained signal. Larger error-suppressed devices would allow fuller feature encodings.
3. **Simulation, not hardware:** QAOA and the Stage 3 circuit run on a classical simulator. Stage 3 qubits are independent, so the circuit reproduces a distribution that also has a closed form; it is a validated sampling template rather than a source of speed-up.
4. **Readout mitigation:** On physical hardware, asymmetric readout errors bias the success probability. This notebook uses a simple rescaling; production use would apply confusion-matrix inversion or M3.

### Strategic Business Recommendations
1. **Targeted deployment:** The Vortex Stage 2 portfolio uses 10.0 of 25 budget units and 13.0 of 22 capacity units, leaving 60% of the budget in reserve, for an expected net gain of **\$28.46** (classical optimum \$28.78). Contacting the six highest-probability customers instead (C0170, C0134, C0208, C0327, C0205, C0053) has an expected net value of only \$24.11, so ranking by probability alone leaves value on the table.
2. **Conversion risk hedging:** Under the model's independence assumption there is an **81.32%** chance that fewer than 3 of the 6 contacted customers convert, and an **18.68%** chance of 3 or more. The unused 15 budget units could fund a follow-up wave if early conversion tracking shows underperformance.
