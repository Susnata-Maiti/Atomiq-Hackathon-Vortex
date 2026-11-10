# Vortex: Hybrid Quantum-Classical Term Deposit Campaign Pipeline

**Vortex: End-to-End Hybrid Quantum-Classical Pipeline for High-Precision Customer Conversion, Constrained QAOA Selection, and Quantum Campaign Risk Simulation.**

---

## Inspiration

In retail banking, customer acquisition campaigns are a high-stakes balancing act. Direct marketing calls are expensive in staff hours and customer goodwill; contacting every customer burns operating budget and frustrates clients. Naive greedy heuristics, such as calling the prospects with the highest predicted subscription scores, ignore operational realities: contact costs vary across channels, branch consultation capacity is strictly limited, and conversion rates carry stochastic downside risk.

The **Atomiq Hackathon (part of the global Qiskit Fall Fest 2026)** challenged us to build a **fully connected, three-stage hybrid quantum-classical pipeline**, where machine learning prediction errors in Stage 1 propagate into combinatorial portfolio selection in Stage 2, which in turn defines an amplitude-encoded quantum simulation of campaign risk in Stage 3. That challenge inspired **Vortex**.

Our vision was a production-grade decision engine showing how near-term quantum algorithms (quantum kernel methods, QAOA, and parameterized state preparation) can be combined with classical statistical rigor to deliver business value under tight operational constraints.

---

## What It Does

**Vortex** unifies quantum machine learning, combinatorial quantum optimization, and stochastic quantum simulation into one autonomous three-stage pipeline.

### Stage 1: Predict

- Trains on 300 labeled customers (bank.csv dataset)
- Preprocessing: StandardScaler + OneHotEncoder, fitted on training data only
- Classical baseline: calibrated Logistic Regression (Platt sigmoid)
- Quantum classifier: Qiskit ZZFeatureMap Hilbert-space kernel + QSVC
- 5-fold stratified cross-validation with zero test-set leakage
- Predicts continuous subscription probabilities for 100 test prospects
- Ranks candidates (tie-breaker: customer_id) into a Top 10 candidate pool

### Stage 2: Select

- Merges the Top 10 candidates with operational data (cost, deposit, capacity)
- Objective: Expected Net Value, V_i = p_i × Deposit_i − Cost_i
- Constraints: exactly 6 customers, total cost ≤ 25, total capacity ≤ 22
- Formulated as a QUBO and a 10-qubit Ising Hamiltonian
- Quantum optimization: QAOA (p = 2 layers, COBYLA optimizer, AerSimulator)
- Exact classical benchmark: exhaustive brute force over C(10, 6) = 210 combinations
- Result: 28.46 (QAOA) vs 28.78 (global optimum), optimality gap 0.3231
- Output: 6 optimal customers: C0170, C0327, C0205, C0372, C0272, C0005

### Stage 3: Simulate

- Takes the 6 selected customers with their Stage 1 conversion probabilities
- Amplitude encoding: Ry(θ_i)|0⟩ with θ_i = 2·arcsin(√p_i)
- 6-qubit circuit on AerSimulator, 10,000 shots
- Success condition: at least 3 qubits measure 1 (Hamming weight ≥ 3)
- NISQ noise modeling (depolarizing + readout error) with readout error mitigation
- Analytical benchmark: exact Poisson binomial distribution (64 basis states)
- Classical benchmark: Monte Carlo simulation (100,000 Bernoulli trials)
- Statistical audit: shot-noise Z-score of 1.62σ (statistically consistent)

### Executive Results Summary

- **Stage 1 Top 10 candidates:** C0170, C0134, C0208, C0327, C0205, C0053, C0372, C0338, C0272, C0005 (calibrated probabilities from 0.2239 to 0.3767)
- **Stage 2 final 6 selected customers:** **C0170, C0327, C0205, C0372, C0272, C0005**
- **Budget consumed:** **10.0 / 25.0 units** (60% of budget left in reserve)
- **Capacity consumed:** **13.0 / 22.0 units** (well within branch capacity)
- **Expected net campaign value:** **$28.46** (classical brute-force global optimum: **$28.78**; optimality gap 0.3231, a 1.12% relative gap)
- **Stage 3 exact conversion probability P(≥3):** **18.6801%** (exact Poisson binomial reference)
- **Stage 3 quantum estimate (ideal, noiseless):** **19.3100%** (Δ = 0.006299, within 1.62σ shot noise)
- **Stage 3 quantum estimate (noisy, mitigated):** **19.2745%** (Δ = 0.005944)
- **Stage 3 classical Monte Carlo (100k trials):** **18.7700%** (Δ = 0.000899)

---

## How We Built It

Vortex was built with **Python 3.14**, **Qiskit 2.6.2**, **Qiskit Aer 0.18.2**, **Scikit-Learn 1.9.1**, **SciPy 1.18.1**, **Pandas**, **NumPy**, and **Matplotlib**.

### 1. Stage 1: Mathematical Formulation and Quantum Kernel Machine

To guarantee integrity and follow the hackathon rules, all feature transformations (StandardScaler for 6 numerical attributes and OneHotEncoder for 9 categorical attributes) were fitted **strictly on training data** within every cross-validation fold to prevent data leakage.

**Classical baseline:** A class-weighted Logistic Regression with L2 regularization, combined with Platt sigmoid calibration (`CalibratedClassifierCV(cv=5)`).

**Quantum kernel classifier (QSVC):** We projected the 28 preprocessed features down to 4 principal components with PCA, scaled them to [0, π], and applied Qiskit's `ZZFeatureMap(feature_dimension=4, reps=2, entanglement='linear')`. The feature map is:

```
|φ(x)⟩ = U_Φ(x) |0⟩^⊗4
U_Φ(x) = [ exp( i·Σ_j x_j Z_j  +  i·Σ_{j<k} (π − x_j)(π − x_k) Z_j Z_k ) · H^⊗4 ]^reps
```

The quantum fidelity kernel is evaluated through statevector overlaps:

```
K_ij = |⟨φ(x_i) | φ(x_j)⟩|²
```

We trained a Support Vector Classifier on K and calibrated its decision boundary with Platt scaling.

**Hybrid ensembling:** We combined the quantum kernel representation with the linear baseline (w_quantum = 0.35, w_classical = 0.65), yielding continuous probabilities that reflect the 11% empirical positive-class rate.

**5-Fold Stratified Cross-Validation Benchmark** (Classical Baseline vs Quantum Kernel QSVC):

- **ROC-AUC:** 0.6485 vs 0.4916
- **PR-AUC (Average Precision):** 0.2553 vs 0.1803
- **Precision@10:** 0.1800 vs 0.0600
- **Recall@10:** 0.2571 vs 0.0857
- **Brier Score (lower is better):** 0.2026 vs 0.1429
- **Log Loss:** 0.5957 vs 0.6000

### 2. Stage 2: Constrained QAOA Optimization and Classical Brute Force

With N = 10 candidates, the bank must select exactly K = 6 customers to maximize expected net value while keeping total contact cost ≤ 25 and operational capacity ≤ 22.

**QUBO minimization formulation.** With V_i = p_i·d_i − c_i and penalty weights P_k = 18.0, P_cost = 2.5, P_cap = 2.5:

```
min over x in {0,1}^10 of:
  H_QUBO(x) = − Σ V_i x_i
              + P_k    · ( Σ x_i − 6 )²
              + P_cost · [ max(0, Σ c_i x_i − 25) ]²
              + P_cap  · [ max(0, Σ h_i x_i − 22) ]²
```

**Ising spin mapping.** Using x_i = (1 − Z_i) / 2, where Z_i ∈ {+1, −1} are Pauli-Z operators:

```
H_C = Σ h_i Z_i + Σ_{i<j} J_ij Z_i Z_j + offset
```

**QAOA circuit and variational optimization.** We implemented a 10-qubit, p = 2 QAOA state preparation circuit:

```
|γ, β⟩ = Π_{l=1..p} ( e^(−i β_l Σ_i X_i) · e^(−i γ_l H_C) ) |+⟩^⊗10
```

The variational parameters γ and β were optimized with SciPy's COBYLA over 150 iterations on `AerSimulator`.

**Verification against the classical optimum.** We evaluated all C(10, 6) = 210 combinations by exhaustive search. QAOA converged to a high-value feasible portfolio:

```
x* = (1, 0, 0, 1, 1, 0, 1, 0, 1, 1)  →  {C0170, C0327, C0205, C0372, C0272, C0005}
```

This gives an expected net value of **$28.46** against the brute-force upper bound of **$28.78** (an optimality gap of just 0.3231, or 1.12% relative), while strictly maintaining feasibility (Budget: 10/25, Capacity: 13/22).

### 3. Stage 3: Amplitude-Encoded Quantum Risk Simulation

For the 6 chosen customers, we simulated the probability that at least 3 subscribe (Hamming weight ≥ 3).

**Quantum amplitude encoding.** Instead of expensive multi-qubit adder circuits, we initialized a 6-qubit register in |0⟩^⊗6 and applied single-qubit Ry(θ_i) rotations with θ_i = 2·arcsin(√p_i):

```
Ry(θ_i)|0⟩ = cos(θ_i/2)|0⟩ + sin(θ_i/2)|1⟩ = √(1 − p_i)|0⟩ + √p_i|1⟩
```

Measuring qubit i in the computational basis yields |1⟩ with exact probability p_i.

**Transpilation metrics:**

- Logical and physical qubits: 6
- Original and transpiled circuit depth: 2 (1 layer of Ry gates + 1 measurement layer)
- Gate counts: 6 single-qubit Ry gates, 0 two-qubit gates, 0 SWAP gates

**Simulation and readout error mitigation.** We measured 10,000 shots on `AerSimulator`. Besides ideal noiseless simulation, we built a realistic NISQ noise model (single-qubit depolarizing error λ = 0.001 and asymmetric readout error P(0|1) = 0.02, P(1|0) = 0.01). Readout mitigation reduced the noisy estimation bias from +0.98% to +0.59%.

**Analytical benchmark.** We computed the exact probability from the Poisson binomial distribution, summing over all 64 basis states:

```
P_exact(≥3) = Σ over b in {0,1}^6 with Σ b_i ≥ 3 of  Π_i p_i^b_i · (1 − p_i)^(1 − b_i)  =  18.6801%
```

The ideal quantum simulation yielded **19.3100%**, a difference of just 0.006299. With theoretical shot-noise standard deviation σ = √(p(1−p)/S) = 0.003898, the error corresponds to a Z-score of **1.62σ**, consistent with quantum projection noise.

---

## Challenges We Ran Into

1. **Test set customer ID alignment and traceability.** In the challenge workbook, `Stage1_Test` was released with explicit `customer_id` tracking (C0231, C0345, ...), which cross-references `Stage2_Data` and `Stage1_Train`. We adapted our ingestion pipeline to automatically detect, validate, and bind these official IDs end-to-end across prediction, optimization, and quantum simulation without index loss.

2. **Cardinality and multi-constraint QUBO balancing.** Mapping an equality constraint (Σ x_i = 6) alongside two inequality constraints (Σ c_i x_i ≤ 25 and Σ h_i x_i ≤ 22) to an Ising Hamiltonian is difficult: if penalty coefficients are too low, the solver returns invalid bitstrings; if too high, penalties dominate the Hamiltonian and obscure the objective. We derived an exact expansion for the cardinality penalty:

   ```
   ( Σ x_i − 6 )² = −11·Σ x_i + 2·Σ_{i<j} x_i x_j + 36
   ```

   and calibrated the linear penalty slacks so QAOA sampled feasible 6-customer configurations with high probability.

3. **Bitstring endianness in Qiskit.** Qiskit indexes classical bitstrings in reverse order (q_{n−1} ... q_0), whereas business arrays follow index order (q_0 ... q_{n−1}). We implemented strict bit-reversal in our decoders to avoid inverted customer mappings.

---

## Accomplishments That We're Proud Of

- **High-quality constrained quantum optimization:** Our QAOA formulation achieved a **1.12% relative gap (0.3231)** against the exhaustive classical optimum across all 210 subsets while satisfying both budget and capacity constraints.
- **Full end-to-end execution in under 10 seconds:** Feature scaling, 5-fold CV, quantum kernel calculations, QAOA optimization, 10,000-shot Aer simulation, and chart rendering run in about 9 seconds on a standard computer.
- **100% self-contained, pre-rendered Jupyter notebook:** [vortex_pipeline.ipynb](https://github.com/Susnata-Maiti/Atomiq-Hackathon-Vortex/blob/main/vortex_pipeline.ipynb) contains all 27 markdown and code cells with every metric, ASCII circuit diagram, and dual-panel visualization pre-rendered.
- **Comprehensive test suite:** Our automated Pytest suite validates schema constraints, budget limits, and quantum accuracy bounds with a 100% pass rate.

---

## What We Learned

- **Amplitude encoding vs. arithmetic quantum circuits:** Preparing independent Bernoulli probabilities directly with single-qubit rotations Ry(2·arcsin(√p_i)) gives shallow, NISQ-friendly depth-2 circuits that avoid noisy multi-qubit adder gates.
- **Probability calibration is essential for QML:** Quantum kernel classifiers naturally output uncalibrated SVM margins. Platt sigmoid calibration is crucial before probabilities feed downstream financial objectives.
- **Quantum-classical symbiosis:** Quantum algorithms work best inside a hybrid workflow, with classical techniques handling data munging and quantum circuits handling combinatorial exploration and stochastic sampling.

---

## What's Next for Vortex

- **Execution on physical IBM Quantum QPUs:** Running the Stage 3 circuit on IBM Quantum hardware (e.g., `ibm_brisbane` or `ibm_kyoto`) via Qiskit Runtime `SamplerV2` with Dynamical Decoupling (DD) and Twirled Readout Error Mitigation (TREX).
- **Subspace-preserving XY mixers:** Implementing Dicke-state initialization with Givens-rotation XY mixers in QAOA to restrict the search to the Hamming-weight subspace Σ x_i = 6, removing penalty tuning entirely.
- **Multi-product banking portfolios:** Expanding Vortex to joint cross-sell campaigns (term deposits, credit cards, mortgages) where customer decisions are correlated via parameterized entangling gates (Rzz or CNOTs).

---

## Built With

python, qiskit, qiskit-aer, qaoa, quantum-machine-learning, quantum-computing, quantum-circuits, quantum-kernel, scikit-learn, scipy, numpy, pandas, matplotlib, openpyxl, qubo, combinatorial-optimization, cross-validation, monte-carlo-simulation, poisson-binomial, fintech, financial-modeling, jupyter-notebook, pytest
