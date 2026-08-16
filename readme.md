**About the Project**

This project uses National Health and Nutrition Examination Survey (NHANES) 2017–2020 data to examine population-level relationships among baseline characteristics, statin use, and low-density lipoprotein (LDL) cholesterol control. LASSO regression is used to identify potential parents of statin use and LDL control and to construct a directed acyclic graph (DAG) representing the selected relationships.

**Dataset**

Eight NHANES datasets were combined using the participant identifier SEQN:

P_DEMO.xpt — Demographics
P_RXQ_RX.xpt — Prescription Medications
P_DIQ.xpt — Diabetes Questionnaire
P_MCQ.xpt — Medical Conditions Questionnaire
P_SMQ.xpt — Smoking Questionnaire
P_CDQ.xpt — Cardiovascular Health Questionnaire
P_BPQ.xpt — Blood Pressure & Cholesterol Questionnaire
P_TRIGLY.xpt — Triglycerides and LDL Cholesterol Laboratory Data

The analysis was limited to adults aged 20 years or older.

**Variables**

The primary exposure was statin use, coded as a binary variable based on reported use of atorvastatin, simvastatin, pravastatin, rosuvastatin, lovastatin, pitavastatin, or fluvastatin.

The outcome was LDL control, based on the laboratory-measured LDL value (LBDLDL):

Controlled LDL: <100 mg/dL
Uncontrolled LDL: ≥100 mg/dL

Baseline characteristics included age, sex, race/ethnicity, diabetes, hypertension, high cholesterol, smoking history, coronary heart disease, angina, heart attack, and stroke.

**How it Works — Two LASSO Models**
Model	Response	Candidate Predictors
LASSO 1	Statin use	Baseline characteristics
LASSO 2	LDL control	Baseline characteristics + statin use

Both logistic LASSO models used the 1-standard-error (1-SE) penalty for variable selection.

**LASSO 1 — Parents of Statin Use**

The first LASSO included 8,815 complete cases and selected eight potential parents of statin use:

Age
High cholesterol
Diabetes
Hypertension
Coronary heart disease
Heart attack
Sex
Stroke

Age (β = 0.978) and high cholesterol (β = 0.851) had the largest positive coefficients.

**LASSO 2 — Parents of LDL Control**

The second LASSO included 3,713 complete cases and selected the following potential parents of LDL control:

Statin use
High cholesterol
Age
Diabetes
Coronary heart disease
Race
Stroke
Smoking history

Statin use had the largest positive coefficient (β = 0.736), while high cholesterol had the largest negative coefficient (β = −0.373).

**Directed Acyclic Graph (DAG)**

The variables selected by the two LASSO models were used to construct a directed acyclic graph (DAG) in Python. Race dummy variables from the regression were represented as a single conceptual Race node in the DAG.

A key relationship identified by the analysis was:

Statin use directly related to LDL control

The DAG represents population-level statistical relationships and should not be interpreted as establishing causal effects.

**Key Features**
Combines multiple NHANES datasets using SEQN
Identifies multiple individual statin medications
Creates binary statin-use and LDL-control variables
Restricts analysis to adults aged ≥20 years
Uses logistic LASSO regression for variable selection
Applies the 1-standard-error rule
Identifies potential parents of statin use and LDL control
Generates a DAG using LASSO-selected variables

**Limitations**
NHANES uses a cross-sectional design, limiting the ability to establish temporal or causal relationships between statin use and LDL control. NHANES is designed primarily for national population estimates rather than state-, local-, or individual patient-level conclusions. Some variables, including medication use, smoking history, and medical history, also rely at least partly on participant reporting.

**Tech Stack**
Python 3.12.3 — analysis
pandas / numpy — data preparation
scikit-learn — logistic LASSO regression and standardization
NetworkX — DAG construction
matplotlib — DAG visualization

**Author**
Charles Carr, George Mason Univeristy
