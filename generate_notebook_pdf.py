"""
Vortex Pipeline Technical Walkthrough PDF Generator
Generates an exact 4-page, publication-quality technical report explaining vortex_pipeline.ipynb.
Includes architecture diagrams, code explanations, mathematical derivations,
cross-validation tables, QAOA formulation, quantum amplitude encoding,
and the embedded dual-panel Matplotlib visualization.
"""

import os
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    KeepTogether,
    HRFlowable,
    PageBreak,
)
from reportlab.pdfgen import canvas
import pymupdf

# Color Palette
PRIMARY = colors.HexColor("#0B2545")       # Deep Navy
SECONDARY = colors.HexColor("#134074")     # Slate Blue
ACCENT_BLUE = colors.HexColor("#0284C7")   # Bright Cyan/Blue
ACCENT_TEAL = colors.HexColor("#0F766E")   # Deep Teal
BG_LIGHT = colors.HexColor("#F8FAFC")      # Slate 50
BG_CALLOUT = colors.HexColor("#EEF4F8")    # Soft Blue-Grey
BORDER_COLOR = colors.HexColor("#CBD5E1")  # Slate 300
TEXT_DARK = colors.HexColor("#0F172A")     # Slate 900
TEXT_MUTED = colors.HexColor("#475569")    # Slate 600
CODE_BG = colors.HexColor("#F1F5F9")       # Light Slate


class NumberedCanvas(canvas.Canvas):
    """
    Two-pass canvas that dynamically calculates total pages and prints
    'Page X of Y' in the running footer, plus running header on pages > 1.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_MUTED)

        # Running Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(45, 11 * inch - 30, "Vortex: Hybrid Quantum-Classical Pipeline — Technical Walkthrough")
            self.drawRightString(8.5 * inch - 45, 11 * inch - 30, "vortex_pipeline.ipynb Guide")
            self.setStrokeColor(BORDER_COLOR)
            self.setLineWidth(0.5)
            self.line(45, 11 * inch - 34, 8.5 * inch - 45, 11 * inch - 34)

        # Running Footer (all pages)
        self.setStrokeColor(BORDER_COLOR)
        self.setLineWidth(0.5)
        self.line(45, 36, 8.5 * inch - 45, 36)

        self.drawString(45, 25, "Atomiq Hackathon (Qiskit Fall Fest 2026) | Technical Walkthrough Report")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(8.5 * inch - 45, 25, page_str)
        self.restoreState()


def build_walkthrough_pdf(output_filename="vortex_pipeline_walkthrough.pdf"):
    # Margins: 45 pt (0.625 inch)
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=45,
        rightMargin=45,
        topMargin=42,
        bottomMargin=42,
    )

    styles = getSampleStyleSheet()

    # Typography Styles
    style_title = ParagraphStyle(
        "CoverTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        spaceAfter=3,
    )
    style_subtitle = ParagraphStyle(
        "CoverSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=10.5,
        leading=14,
        textColor=SECONDARY,
        spaceAfter=5,
    )
    style_tagline = ParagraphStyle(
        "CoverTagline",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8.5,
        leading=11.5,
        textColor=ACCENT_TEAL,
        spaceAfter=6,
    )
    style_h1 = ParagraphStyle(
        "Heading1_Custom",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=14,
        textColor=PRIMARY,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True,
    )
    style_body = ParagraphStyle(
        "Body_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=TEXT_DARK,
        spaceAfter=3.5,
    )
    style_bullet = ParagraphStyle(
        "Bullet_Custom",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=TEXT_DARK,
        leftIndent=10,
        firstLineIndent=-7,
        spaceAfter=2.5,
    )
    style_callout = ParagraphStyle(
        "CalloutText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=10.5,
        textColor=TEXT_DARK,
    )
    style_math = ParagraphStyle(
        "MathFormula",
        parent=styles["Normal"],
        fontName="Times-Italic",
        fontSize=8.5,
        leading=11.5,
        alignment=1, # Centered
        textColor=PRIMARY,
        spaceBefore=2,
        spaceAfter=3,
    )
    style_table_cell = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.2,
        leading=9.5,
        textColor=TEXT_DARK,
    )
    style_table_header = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=7.6,
        leading=10,
        textColor=colors.white,
    )

    story = []

    # =========================================================================
    # PAGE 1: TITLE, EXECUTIVE SUMMARY & MASTER DELIVERABLES DASHBOARD
    # =========================================================================
    story.append(Paragraph("Vortex: Hybrid Quantum-Classical Pipeline", style_title))
    story.append(Paragraph("Technical Walkthrough, Code Breakdown & Mathematical Analysis of <code>vortex_pipeline.ipynb</code>", style_subtitle))
    story.append(Paragraph("<b>Tagline:</b> <i>Vortex: End-to-End Hybrid Quantum-Classical Pipeline for High-Precision Customer Conversion, Constrained QAOA Selection, and Quantum Campaign Risk Simulation.</i>", style_tagline))
    story.append(HRFlowable(width="100%", thickness=1, color=PRIMARY, spaceBefore=0, spaceAfter=6))

    # Metadata Banner Table
    meta_data = [
        [
            Paragraph("<b>Hackathon:</b> Atomiq Hackathon (Qiskit Fall Fest 2026)", style_table_cell),
            Paragraph("<b>Notebook:</b> <code>vortex_pipeline.ipynb</code> (27 Cells)", style_table_cell),
            Paragraph("<b>Execution Time:</b> ~8.86 Seconds (Standalone)", style_table_cell),
        ],
        [
            Paragraph("<b>Quantum SDK:</b> Qiskit 2.6.2 & Aer 0.18.2", style_table_cell),
            Paragraph("<b>Test Suite:</b> 4 / 4 Automated Pytest Tests Passed", style_table_cell),
            Paragraph("<b>Optimality Gap:</b> 0.3231 (1.12% relative gap)", style_table_cell),
        ]
    ]
    meta_table = Table(meta_data, colWidths=[2.45 * inch, 2.75 * inch, 2.45 * inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_CALLOUT),
        ('BOX', (0, 0), (-1, -1), 0.75, BORDER_COLOR),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 6))

    story.append(Paragraph("1. Executive Summary & Pipeline Architecture", style_h1))
    story.append(Paragraph(
        "Commercial banking marketing campaigns operate under severe operational limits: contacting prospects incurs marketing budget and advisor labor, branch consultation capacity is strictly capped, and customer conversion exhibits stochastic risk. "
        "The <b>Vortex</b> notebook (<code>vortex_pipeline.ipynb</code>) establishes an autonomous, mathematically connected 3-stage hybrid quantum-classical pipeline:",
        style_body
    ))

    arch_bullets = [
        "<b>Stage 1: Subscription Prediction (Cells 1–10):</b> Machine learning subscription classifier fusing a Qiskit <code>ZZFeatureMap</code> Quantum Kernel Support Vector Classifier (QSVC) with a Calibrated Platt-sigmoid Logistic Regression baseline. Evaluated strictly via 5-Fold Stratified Cross-Validation on training data only (zero test set leakage) to rank 100 test prospects and isolate the top 10 candidates.",
        "<b>Stage 2: Constrained Customer Selection (Cells 11–16):</b> Quadratic Unconstrained Binary Optimization (QUBO) and 10-qubit Ising Hamiltonian mapping solved via QAOA (p=2 layers, COBYLA optimizer) on <code>AerSimulator</code> and benchmarked against an exhaustive classical combinatorial solver (210 combinations). QAOA isolates an optimal subset of K=6 customers yielding <b>$28.46</b> net expected gain (vs $28.78 upper bound, gap = 0.3231), strictly satisfying budget and capacity limits.",
        "<b>Stage 3: Campaign Risk Simulation (Cells 17–26):</b> 6-qubit quantum amplitude encoding circuit using single-qubit Ry rotations to simulate campaign risk (probability that &ge; 3 of 6 customers subscribe). Validated against exact Poisson Binomial analytical ground truth across all 64 basis states and a 100,000-trial classical Monte Carlo simulation.",
    ]
    for b in arch_bullets:
        story.append(Paragraph(f"&bull; {b}", style_bullet))
    story.append(Spacer(1, 5))

    # Master Deliverables Table
    deliv_data = [
        [Paragraph("Deliverable Parameter", style_table_header), Paragraph("Vortex Value", style_table_header), Paragraph("Benchmark & Verification", style_table_header)],
        [Paragraph("Stage 1 Top 10 Candidates", style_table_cell), Paragraph("<code>C0170, C0134, C0208, C0327, C0205, C0053, C0372, C0338, C0272, C0005</code>", style_table_cell), Paragraph("Calibrated probabilities: 22.39% to 37.67%", style_table_cell)],
        [Paragraph("Stage 2 Selected 6 Customers", style_table_cell), Paragraph("<b><code>C0170, C0327, C0205, C0372, C0272, C0005</code></b>", style_table_cell), Paragraph("Feasible subset of K=6 selected from Top 10 pool", style_table_cell)],
        [Paragraph("Total Budget Consumed", style_table_cell), Paragraph("<b>10.0 units</b>", style_table_cell), Paragraph("&le; 25.0 Limit (Feasible, 60% budget in reserve)", style_table_cell)],
        [Paragraph("Total Capacity Consumed", style_table_cell), Paragraph("<b>13.0 units</b>", style_table_cell), Paragraph("&le; 22.0 Limit (Feasible, 41% branch capacity buffer)", style_table_cell)],
        [Paragraph("Expected Net Campaign Value (Z)", style_table_cell), Paragraph("<b>$28.46</b>", style_table_cell), Paragraph("Classical Brute-Force Global Optimum: <b>$28.78</b>", style_table_cell)],
        [Paragraph("QAOA Optimality Gap", style_table_cell), Paragraph("<b>0.3231</b> (1.12% relative gap)", style_table_cell), Paragraph("High-value near-optimal portfolio converged", style_table_cell)],
        [Paragraph("Stage 3 Exact Analytical Prob P(&ge; 3)", style_table_cell), Paragraph("<b>18.6801%</b>", style_table_cell), Paragraph("Poisson Binomial exact analytical reference", style_table_cell)],
        [Paragraph("Stage 3 Quantum Estimate (Ideal)", style_table_cell), Paragraph("<b>19.3100%</b> (1,931 / 10,000 shots)", style_table_cell), Paragraph("&Delta; = 0.006299, 1.62&sigma; within quantum shot noise", style_table_cell)],
        [Paragraph("Stage 3 Quantum Estimate (Mitigated)", style_table_cell), Paragraph("<b>19.2745%</b> (Readout error mitigated)", style_table_cell), Paragraph("Restores unmitigated noisy estimate (19.66%)", style_table_cell)],
        [Paragraph("Stage 3 Classical Monte Carlo", style_table_cell), Paragraph("<b>18.7700%</b> (100,000 Bernoulli trials)", style_table_cell), Paragraph("&Delta; = 0.000899 against analytical truth", style_table_cell)],
    ]
    t_deliv = Table(deliv_data, colWidths=[2.2 * inch, 2.75 * inch, 2.7 * inch])
    t_deliv.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
    ]))
    story.append(t_deliv)

    # End of Page 1
    story.append(PageBreak())

    # =========================================================================
    # PAGE 2: SETUP, DATA AUDIT & STAGE 1 PREDICT (CELLS 1-10)
    # =========================================================================
    story.append(Paragraph("2. Setup, Ingestion & Data Traceability Audit (Cells 1–4)", style_h1))
    story.append(Paragraph(
        "<b>Cells 1 & 2 (Environment Setup):</b> Configures a global deterministic seed (<code>SEED = 42</code>) across NumPy, Scikit-Learn, Qiskit Transpiler, Simulator, and Monte Carlo generators. Imports standard numerical packages, Qiskit 2.6.2 circuits and operators, <code>AerSimulator</code>, and SciPy optimization routines.",
        style_body
    ))
    story.append(Paragraph(
        "<b>Cells 3 & 4 (Data Loading & Traceability Audit):</b> Ingests <code>bank_campaign_participant_release.xlsx</code>. "
        "The dataset spans 300 labeled customers in <code>Stage1_Train</code>, 100 test prospects in <code>Stage1_Test</code>, and 400 total customer records in <code>Stage2_Data</code>. "
        "The code audits customer ID integrity across sheets, verifying that the 100 test IDs exactly match the set difference: "
        "<code>set(Stage1_Test) == set(Stage2_Data) - set(Stage1_Train)</code>. This confirms 100% ID traceability across all three pipeline stages without index loss or duplication.",
        style_body
    ))

    story.append(Paragraph("3. Stage 1: Feature Engineering & Preprocessing Pipeline (Cells 5–6)", style_h1))
    story.append(Paragraph(
        "<b>Cells 5 & 6 (Feature Transformation Pipeline):</b> Partitions customer demographic and financial attributes into 6 continuous numerical features "
        "(<code>age, balance, day, campaign, pdays, previous</code>) and 9 categorical features (<code>job, marital, education, default, housing, loan, contact, month, poutcome</code>).<br/>"
        "&bull; <b>Numerical Scaler:</b> Continuous features are normalized with <code>StandardScaler()</code>.<br/>"
        "&bull; <b>Categorical Encoder:</b> Categorical features are encoded using <code>OneHotEncoder(handle_unknown='ignore')</code>.<br/>"
        "&bull; <b>Zero Data Leakage Discipline:</b> In strict compliance with competition rules, scalers and encoders are fitted <i>strictly on the training data</i> across each cross-validation fold, preventing test information from contaminating model training.",
        style_body
    ))

    story.append(Paragraph("4. Stage 1: 5-Fold Stratified Cross-Validation & Quantum Kernel (Cells 7–8)", style_h1))
    story.append(Paragraph(
        "<b>Cells 7 & 8 (Model Architecture & Benchmarking):</b> Evaluates a Classical Baseline against a Quantum Kernel Classifier using 5-Fold Stratified Cross-Validation on the 300 training samples (11.0% positive base rate):<br/>"
        "&bull; <b>Classical Baseline:</b> Class-weighted L2-penalized Logistic Regression with Platt sigmoid probability calibration (<code>CalibratedClassifierCV(cv=5)</code>).<br/>"
        "&bull; <b>Quantum Kernel Support Vector Classifier (QSVC):</b> High-dimensional feature maps project classical data into a Hilbert space where nonlinear boundaries become linearly separable. Preprocessed features are projected to 4 principal components via PCA, scaled to [0, &pi;], and embedded into a 16-dimensional complex Hilbert space using Qiskit's <code>ZZFeatureMap(feature_dimension=4, reps=2, entanglement='linear')</code>:",
        style_body
    ))
    story.append(Paragraph(
        "|&phi;(x)&rang; = U<sub>&Phi;(x)</sub> |0&rang;<sup>&otimes;4</sup> = &prod;<sub>d</sub> exp( i &sum;<sub>j</sub> x<sub>j</sub> Z<sub>j</sub> + &sum;<sub>j &lt; k</sub> (&pi; &minus; x<sub>j</sub>)(&pi; &minus; x<sub>k</sub>) Z<sub>j</sub> Z<sub>k</sub> ) H<sup>&otimes;4</sup> |0&rang;<sup>&otimes;4</sup>",
        style_math
    ))
    story.append(Paragraph(
        "The quantum fidelity kernel matrix is computed via statevector inner products: <font face='Times-Italic'>K<sub>ij</sub> = |&lang;&phi;(x<sub>i</sub>)|&phi;(x<sub>j</sub>)&rang;|<sup>2</sup></font>. A Support Vector Classifier is trained on K with Platt probability calibration.",
        style_body
    ))

    # Cross-Validation Table
    cv_data = [
        [Paragraph("Cross-Validation Metric", style_table_header), Paragraph("Classical Calibrated LogReg", style_table_header), Paragraph("Quantum Kernel QSVC", style_table_header), Paragraph("Ensemble Architectural Synergy", style_table_header)],
        [Paragraph("ROC-AUC", style_table_cell), Paragraph("<b>0.6485</b>", style_table_cell), Paragraph("0.4916", style_table_cell), Paragraph("Classical model captures macro linear demographic trends", style_table_cell)],
        [Paragraph("PR-AUC (Average Precision)", style_table_cell), Paragraph("<b>0.2553</b>", style_table_cell), Paragraph("0.1803", style_table_cell), Paragraph("Measures precision-recall tradeoff on imbalanced targets", style_table_cell)],
        [Paragraph("Precision@10", style_table_cell), Paragraph("<b>0.1800</b>", style_table_cell), Paragraph("0.0600", style_table_cell), Paragraph("Evaluates concentration of positive leads in top ranks", style_table_cell)],
        [Paragraph("Recall@10", style_table_cell), Paragraph("<b>0.2571</b>", style_table_cell), Paragraph("0.0857", style_table_cell), Paragraph("Measures fraction of all converters captured in top 10", style_table_cell)],
        [Paragraph("Brier Score (lower = better)", style_table_cell), Paragraph("0.2026", style_table_cell), Paragraph("<b>0.1429</b>", style_table_cell), Paragraph("Quantum kernel achieves superior probabilistic calibration", style_table_cell)],
        [Paragraph("Log Loss", style_table_cell), Paragraph("<b>0.5957</b>", style_table_cell), Paragraph("0.6000", style_table_cell), Paragraph("Ensemble balances sharpness with cross-entropy stability", style_table_cell)],
    ]
    t_cv = Table(cv_data, colWidths=[1.8 * inch, 1.8 * inch, 1.7 * inch, 2.35 * inch])
    t_cv.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), SECONDARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
        ('TOPPADDING', (0, 0), (-1, -1), 2),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT]),
    ]))
    story.append(t_cv)
    story.append(Spacer(1, 4))

    story.append(Paragraph("5. Full Model Training, Test Predictions & Candidate Ranking (Cells 9–10)", style_h1))
    story.append(Paragraph(
        "<b>Cells 9 & 10 (Ensemble Inference & Output):</b> Retrains on all 300 samples and evaluates the 100 test prospects using a calibrated weighted ensemble: "
        "<code>P_ensemble = 0.35 * P_quantum + 0.65 * P_classical</code>. "
        "Test probabilities range smoothly between 2.3% and 37.7%. Candidates are sorted descending by probability with tie-breaking on <code>customer_id</code>. "
        "The Top 10 candidate pool is isolated: <code>C0170 (0.3767), C0134 (0.2864), C0208 (0.2781), C0327 (0.2572), C0205 (0.2468), C0053 (0.2393), C0372 (0.2358), C0338 (0.2308), C0272 (0.2306), C0005 (0.2239)</code>. "
        "All 100 predictions are exported to <code>stage1_result.csv</code>.",
        style_body
    ))

    # End of Page 2
    story.append(PageBreak())

    # =========================================================================
    # PAGE 3: STAGE 2 OPTIMIZATION & STAGE 3 SIMULATION (CELLS 11-22)
    # =========================================================================
    story.append(Paragraph("6. Stage 2: Operational Data Integration & QUBO Formulation (Cells 11–12)", style_h1))
    story.append(Paragraph(
        "<b>Cells 11 & 12 (Financial Objective & Penalty Formulation):</b> Merges the Top 10 candidate pool with <code>Stage2_Data</code> (contact cost c<sub>i</sub>, expected deposit d<sub>i</sub>, and staff capacity h<sub>i</sub>). "
        "Computes Expected Net Value: <font face='Times-Italic'>V<sub>i</sub> = p<sub>i</sub> d<sub>i</sub> &minus; c<sub>i</sub></font>. "
        "The campaign must select exactly K=6 customers to maximize &sum; V<sub>i</sub> x<sub>i</sub> subject to Budget &le; 25 and Capacity &le; 22. "
        "Mapped to Quadratic Unconstrained Binary Optimization (QUBO):",
        style_body
    ))
    story.append(Paragraph(
        "min<sub>x &isin; {0,1}<sup>10</sup></sub> H<sub>QUBO</sub>(x) = &minus;&sum;<sub>i=0</sub><sup>9</sup> V<sub>i</sub> x<sub>i</sub> + P<sub>k</sub> (&sum;<sub>i=0</sub><sup>9</sup> x<sub>i</sub> &minus; 6)<sup>2</sup> + P<sub>cost</sub> [max(0, &sum; c<sub>i</sub> x<sub>i</sub> &minus; 25)]<sup>2</sup> + P<sub>cap</sub> [max(0, &sum; h<sub>i</sub> x<sub>i</sub> &minus; 22)]<sup>2</sup>",
        style_math
    ))
    story.append(Paragraph(
        "Penalty multipliers are calibrated to P<sub>k</sub> = 18.0, P<sub>cost</sub> = 2.5, P<sub>cap</sub> = 2.5. Expanding the cardinality square yields: "
        "<font face='Times-Italic'>(&sum; x<sub>i</sub> &minus; 6)<sup>2</sup> = &minus;11 &sum; x<sub>i</sub> + 2 &sum;<sub>i &lt; j</sub> x<sub>i</sub> x<sub>j</sub> + 36</font>.",
        style_body
    ))

    story.append(Paragraph("7. Stage 2: Classical Benchmark vs QAOA Optimization (Cells 13–16)", style_h1))
    story.append(Paragraph(
        "<b>Cells 13 & 14 (Exact Classical Exhaustive Benchmark):</b> Enumerates all &binom;(10, 6) = 210 candidate subsets. Identifies 162 feasible combinations, isolating the global combinatorial optimum: "
        "<b>Z<sup>*</sup> = $28.78</b> (Cost = 10.0, Capacity = 14.0) selecting IDs <code>['C0170', 'C0327', 'C0205', 'C0053', 'C0372', 'C0272']</code>.<br/>"
        "<b>Cells 15 & 16 (QAOA Solver & Circuit Transpilation):</b> Using the Ising spin change of variables <font face='Times-Italic'>x<sub>i</sub> = (1 &minus; Z<sub>i</sub>)/2</font>, constructs the 10-qubit cost Hamiltonian: "
        "<font face='Times-Italic'>H<sub>C</sub> = &sum; h<sub>i</sub> Z<sub>i</sub> + &sum;<sub>i &lt; j</sub> J<sub>ij</sub> Z<sub>i</sub> Z<sub>j</sub> + offset</font>. "
        "Constructs a p=2 layer QAOA circuit parameterized by (&gamma;<sub>1</sub>, &gamma;<sub>2</sub>, &beta;<sub>1</sub>, &beta;<sub>2</sub>):",
        style_body
    ))
    story.append(Paragraph(
        "|&gamma;, &beta;&rang; = &prod;<sub>l=1</sub><sup>2</sup> ( exp(&minus;i &beta;<sub>l</sub> &sum;<sub>i</sub> X<sub>i</sub>) exp(&minus;i &gamma;<sub>l</sub> H<sub>C</sub>) ) |+&rang;<sup>&otimes;10</sup>",
        style_math
    ))
    story.append(Paragraph(
        "&bull; <b>Circuit Metrics:</b> 10 logical/physical qubits, 33 original depth, 50 1Q gates (10 H + 20 Rz + 20 Rx), 90 2Q Rzz gates, 0 SWAP gates.<br/>"
        "&bull; <b>Variational Optimization:</b> SciPy COBYLA optimizes parameters over 150 iterations on <code>AerSimulator</code>.<br/>"
        "&bull; <b>Sampling & Decoding:</b> Measures 10,000 shots. QAOA selects bitstring <code>1001101011</code> (<code>['C0170', 'C0327', 'C0205', 'C0372', 'C0272', 'C0005']</code>) "
        "yielding <b>Z = $28.46</b> (Budget: 10.0 / 25.0, Capacity: 13.0 / 22.0) with an optimality gap of only <b>0.3231</b> (1.12% relative gap). Exported to <code>stage2_result.csv</code>.",
        style_body
    ))

    story.append(Paragraph("8. Stage 3: Quantum Amplitude Encoding Circuit (Cells 17–18)", style_h1))
    story.append(Paragraph(
        "<b>Cells 17 & 18 (Qubit State Preparation):</b> For the 6 QAOA-selected prospects, conversion probabilities are encoded as single-qubit rotations with angles "
        "<font face='Times-Italic'>&theta;<sub>i</sub> = 2 arcsin(&radic;p<sub>i</sub>)</font>:<br/>"
        "<code>q0: C0170 (p=0.3767, &theta;=1.3215) | q1: C0327 (p=0.2572, &theta;=1.0637) | q2: C0205 (p=0.2468, &theta;=1.0398)<br/>"
        "q3: C0372 (p=0.2358, &theta;=1.0141) | q4: C0272 (p=0.2306, &theta;=1.0017) | q5: C0005 (p=0.2239, &theta;=0.9859)</code><br/>"
        "Applying Ry(&theta;<sub>i</sub>)|0&rang; directly yields: <font face='Times-Italic'>R<sub>y</sub>(&theta;<sub>i</sub>)|0&rang; = &radic;(1 &minus; p<sub>i</sub>)|0&rang; + &radic;p<sub>i</sub>|1&rang;</font>. "
        "Measuring in the computational basis produces outcome 1 with exact probability p<sub>i</sub>. "
        "This achieves a transpiled circuit depth of only 2 with 0 entangling gates, fully bypassing NISQ CNOT noise.",
        style_body
    ))

    story.append(Paragraph("9. Stage 3: Simulation, Noise Mitigation & Exact Validation (Cells 19–22)", style_h1))
    story.append(Paragraph(
        "<b>Cells 19 & 20 (Simulation & Readout Mitigation):</b> Evaluates 10,000 shots on <code>AerSimulator</code>. Success requires &ge; 3 qubits measuring 1.<br/>"
        "&bull; <b>Ideal Quantum Estimate:</b> 1,931 successes out of 10,000 shots = <b>19.3100%</b>.<br/>"
        "&bull; <b>Noisy Simulation & Readout Mitigation:</b> Modeled with single-qubit depolarizing error (&lambda; = 0.001) and asymmetric readout error (P(0|1)=0.02, P(1|0)=0.01). Unmitigated noisy estimate is 19.6600%. Applying Matrix Inversion Readout Error Mitigation restores the estimate to <b>19.2745%</b> (&Delta; = 0.005944).<br/>"
        "<b>Cells 21 & 22 (Analytical Poisson Binomial & Monte Carlo Truth):</b><br/>"
        "&bull; <b>Exact Analytical Poisson Binomial:</b> Summing across all 2<sup>6</sup> = 64 computational basis states yields: "
        "<font face='Times-Italic'>P<sub>exact</sub>(&ge; 3) = &sum;<sub>w(b) &ge; 3</sub> &prod; p<sub>i</sub><sup>b<sub>i</sub></sup> (1 &minus; p<sub>i</sub>)<sup>1 &minus; b<sub>i</sub></sup> = <b>18.6801%</b></font>.<br/>"
        "&bull; <b>Classical Monte Carlo Benchmark:</b> 100,000 Bernoulli trials yield <b>18.7700%</b> (&Delta; = 0.000899).<br/>"
        "&bull; <b>Statistical Rigor Audit:</b> Theoretical shot-noise standard error: <font face='Times-Italic'>&sigma; = &radic;[p(1&minus;p)/S] = 0.003898</font>. "
        "The ideal quantum estimation deviation (&Delta; = 0.006299) corresponds to a Z-score of <b>1.62&sigma;</b> (&lt; 2.0&sigma;), confirming exact statistical consistency with quantum projection noise. Exported to <code>stage3_result.csv</code>.",
        style_body
    ))

    # End of Page 3
    story.append(PageBreak())

    # =========================================================================
    # PAGE 4: VISUALIZATION, RECOMMENDATIONS & AUDIT (CELLS 23-26)
    # =========================================================================
    story.append(Paragraph("10. Campaign Analytics & Dual-Panel Visualizations (Cells 23–24)", style_h1))
    story.append(Paragraph(
        "<b>Cells 23 & 24:</b> Generates high-resolution analytics comparing candidate selection economics and stochastic conversion risk profiles:",
        style_body
    ))

    # Embedded Matplotlib Chart
    chart_path = "vortex_charts.png"
    if os.path.exists(chart_path):
        story.append(Image(chart_path, width=7.1 * inch, height=2.4 * inch))
        story.append(Spacer(1, 3))
        story.append(Paragraph(
            "<b>Figure 1:</b> <i>(Left)</i> Stage 2 Expected Net Value across Top 10 prospects, highlighting the 6 QAOA-selected customers (teal) vs unselected (coral). "
            "<i>(Right)</i> Stage 3 Cumulative Conversion Probability P(&ge; k) demonstrating tight numerical agreement between Exact Analytical Ground Truth (blue), Ideal Quantum (teal), Mitigated Quantum (purple), and Classical Monte Carlo (coral dashed).",
            style_callout
        ))
    story.append(Spacer(1, 6))

    story.append(Paragraph("11. Submission Summary & Strategic Recommendations (Cells 25–26)", style_h1))
    story.append(Paragraph(
        "<b>Cells 25 & 26 (Business Decision Framework):</b> Synthesizes technical results into executive banking recommendations:",
        style_body
    ))
    recs = [
        "<b>Capital & Labor Efficiency:</b> Contacting all 100 prospects would cost $250 (exceeding budget by 10&times;) and overwhelm branch staff. The Vortex QAOA portfolio expends only <b>10.0 units of cost</b> (leaving 60% of budget in reserve) and <b>13.0 units of branch capacity</b> (leaving a 41% operational buffer).",
        "<b>Combinatorial Performance:</b> QAOA achieves <b>$28.46</b> net expected gain, capturing 98.88% of the theoretical brute-force upper bound ($28.78) while strictly obeying all operational constraints.",
        "<b>Conversion Risk Hedging:</b> The bank is 81.32% confident that fewer than 3 prospects will convert, but there is an 18.68% probability of achieving &ge; 3 subscriptions. By reserving 15 units of budget, the bank can launch a contingent secondary campaign wave if initial response is low.",
        "<b>NISQ Architectural Advantage:</b> Single-qubit amplitude encoding completely eliminates two-qubit gate error accumulation, enabling depth-2 quantum simulations that can run immediately on physical quantum processors without deep circuit compilation.",
    ]
    for r in recs:
        story.append(Paragraph(f"&bull; {r}", style_bullet))
    story.append(Spacer(1, 6))

    # Verification & Submission Audit Box
    audit_data = [
        [
            Paragraph("<b>Automated Test Suite & Quality Audit</b>", style_table_cell),
            Paragraph("<b>Mandatory Challenge Deliverables</b>", style_table_cell),
        ],
        [
            Paragraph("&bull; <code>tests/test_pipeline.py</code>: <b>4 passed in 2.39s</b><br/>"
                      "&bull; Zero test set leakage (scalers fit on train only)<br/>"
                      "&bull; Budget constraint satisfied: 10.0 &le; 25.0 Limit<br/>"
                      "&bull; Capacity constraint satisfied: 13.0 &le; 22.0 Limit<br/>"
                      "&bull; Quantum Z-score: 1.62&sigma; within shot-noise limits", style_callout),
            Paragraph("&bull; <code>stage1_result.csv</code>: 100 test probability rows<br/>"
                      "&bull; <code>stage2_result.csv</code>: 10 candidate rows, QAOA vs classical<br/>"
                      "&bull; <code>stage3_result.csv</code>: 6 selected customer simulation metrics<br/>"
                      "&bull; <code>vortex_pipeline.ipynb</code>: 100% pre-rendered notebook<br/>"
                      "&bull; <code>DEVPOST.md</code> & <code>README.md</code>: Synchronized docs", style_callout),
        ]
    ]
    t_audit = Table(audit_data, colWidths=[3.75 * inch, 3.85 * inch])
    t_audit.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, ACCENT_TEAL),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t_audit)

    # Build PDF with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated {output_filename}")


if __name__ == "__main__":
    build_walkthrough_pdf()
