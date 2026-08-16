#!/usr/bin/env python
# coding: utf-8

# In[1]:


# S1: LOAD THE NHANES 2017-2020 XPT FILES AND INSPECT THEIR CONTENTS

import pandas as pd
import os

# Folder containing the downloaded NHANES files
folder = r"C:\Users\cdelj\Downloads"

# File names
files = {
    "demo": "P_DEMO.xpt",
    "rx": "P_RXQ_RX.xpt",
    "diq": "P_DIQ.xpt",
    "mcq": "P_MCQ.xpt",
    "smq": "P_SMQ.xpt",
    "cdq": "P_CDQ.xpt",
    "bpq": "P_BPQ.xpt",
    "trigly": "P_TRIGLY.xpt"
}

# Load each file
data = {}

for name, filename in files.items():

    path = os.path.join(folder, filename)

    data[name] = pd.read_sas(
        path,
        format="xport"
    )

    print("\n" + "=" * 70)
    print(name.upper(), "-", filename)
    print("=" * 70)

    print("Shape:", data[name].shape)

    print("\nFirst 5 rows:")
    print(data[name].head())

    print("\nColumn names:")
    print(data[name].columns.tolist())


# In[3]:


# S2: INSPECT STATIN MEDICATIONS AND CANDIDATE VARIABLES

# A. Decode prescription drug names

rx = data["rx"].copy()

rx["RXDDRUG_text"] = rx["RXDDRUG"].apply(
    lambda x: x.decode("utf-8").strip()
    if isinstance(x, bytes)
    else str(x).strip()
)


# B. Find statin medications

statin_names = [
    "ATORVASTATIN",
    "ROSUVASTATIN",
    "SIMVASTATIN",
    "PRAVASTATIN",
    "LOVASTATIN",
    "FLUVASTATIN",
    "PITAVASTATIN"
]

statin_pattern = "|".join(statin_names)

statin_rows = rx[
    rx["RXDDRUG_text"]
    .str.upper()
    .str.contains(statin_pattern, na=False)
]

print("Number of statin medication records:", len(statin_rows))
print("Number of statin users:", statin_rows["SEQN"].nunique())

print("\nStatins found:")
print(statin_rows["RXDDRUG_text"].value_counts())

print("\nExample statin records:")
print(
    statin_rows[
        ["SEQN", "RXDDRUG_text", "RXDDAYS"]
    ].head(20)
)


# C. Inspect candidate variables

variables_to_check = {
    "Age": data["demo"]["RIDAGEYR"],
    "Sex": data["demo"]["RIAGENDR"],
    "Race": data["demo"]["RIDRETH3"],
    "Diabetes": data["diq"]["DIQ010"],
    "Ever_Smoked": data["smq"]["SMQ020"],
    "Current_Smoking": data["smq"]["SMQ040"],
    "Hypertension": data["bpq"]["BPQ020"],
    "High_Cholesterol": data["bpq"]["BPQ080"],
    "Coronary_Heart_Disease": data["mcq"]["MCQ160C"],
    "Angina": data["mcq"]["MCQ160D"],
    "Heart_Attack": data["mcq"]["MCQ160E"],
    "Stroke": data["mcq"]["MCQ160F"],
    "LDL": data["trigly"]["LBDLDL"]
}

for name, variable in variables_to_check.items():
    print("\n", name)
    print(variable.value_counts(dropna=False).sort_index())


# In[5]:


# S3: CREATE AND MERGE THE ANALYSIS VARIABLES

# A. Create demographic variables

demo = data["demo"][["SEQN", "RIDAGEYR", "RIAGENDR", "RIDRETH3"]].copy()

demo = demo.rename(columns={
    "RIDAGEYR": "Age",
    "RIAGENDR": "Sex",
    "RIDRETH3": "Race"
})


# B. Create Statin variable

# Get one row per participant who reported any statin
statin_users = (
    statin_rows[["SEQN"]]
    .drop_duplicates()
    .assign(Statin=1)
)


# C. Create binary clinical variables

diabetes = data["diq"][["SEQN", "DIQ010"]].copy()
diabetes["Diabetes"] = diabetes["DIQ010"].map({1: 1, 2: 0})

bpq = data["bpq"][["SEQN", "BPQ020", "BPQ080"]].copy()
bpq["Hypertension"] = bpq["BPQ020"].map({1: 1, 2: 0})
bpq["High_Cholesterol"] = bpq["BPQ080"].map({1: 1, 2: 0})

smoking = data["smq"][["SEQN", "SMQ020"]].copy()
smoking["Ever_Smoked"] = smoking["SMQ020"].map({1: 1, 2: 0})

mcq = data["mcq"][
    ["SEQN", "MCQ160C", "MCQ160D", "MCQ160E", "MCQ160F"]
].copy()

mcq["Coronary_Heart_Disease"] = mcq["MCQ160C"].map({1: 1, 2: 0})
mcq["Angina"] = mcq["MCQ160D"].map({1: 1, 2: 0})
mcq["Heart_Attack"] = mcq["MCQ160E"].map({1: 1, 2: 0})
mcq["Stroke"] = mcq["MCQ160F"].map({1: 1, 2: 0})


# D. Create LDL and LDL_Controlled variables

ldl = data["trigly"][["SEQN", "LBDLDL"]].copy()

ldl = ldl.rename(columns={
    "LBDLDL": "LDL"
})

ldl["LDL_Controlled"] = (ldl["LDL"] < 100).astype(int)

# Keep LDL_Controlled missing when LDL itself is missing
ldl.loc[ldl["LDL"].isna(), "LDL_Controlled"] = pd.NA


# E. Merge files by SEQN

df = demo.merge(statin_users, on="SEQN", how="left")
df = df.merge(diabetes[["SEQN", "Diabetes"]], on="SEQN", how="left")
df = df.merge(
    bpq[["SEQN", "Hypertension", "High_Cholesterol"]],
    on="SEQN",
    how="left"
)
df = df.merge(smoking[["SEQN", "Ever_Smoked"]], on="SEQN", how="left")
df = df.merge(
    mcq[
        [
            "SEQN",
            "Coronary_Heart_Disease",
            "Angina",
            "Heart_Attack",
            "Stroke"
        ]
    ],
    on="SEQN",
    how="left"
)
df = df.merge(ldl, on="SEQN", how="left")

# No statin record = not currently identified as a statin user
df["Statin"] = df["Statin"].fillna(0).astype(int)


# F. Inspect merged dataset

print("Shape:", df.shape)

print("\nFirst 10 rows:")
print(df.head(10))

print("\nStatin:")
print(df["Statin"].value_counts(dropna=False))

print("\nLDL Controlled:")
print(df["LDL_Controlled"].value_counts(dropna=False))

print("\nMissing values:")
print(df.isna().sum())


# In[7]:


# S4: CREATE ADULT ANALYSIS DATASET AND CHECK SAMPLE SIZE

# A. Restrict to adults age 20 or older

df_adult = df[df["Age"] >= 20].copy()


# B. Check adult sample

print("Adults age 20+:", len(df_adult))

print("\nStatin use:")
print(df_adult["Statin"].value_counts())

print("\nLDL Controlled:")
print(df_adult["LDL_Controlled"].value_counts(dropna=False))


# C. Check complete cases for LASSO predictors

predictors = [
    "Age",
    "Sex",
    "Race",
    "Diabetes",
    "Hypertension",
    "High_Cholesterol",
    "Ever_Smoked",
    "Coronary_Heart_Disease",
    "Angina",
    "Heart_Attack",
    "Stroke"
]

lasso1_check = df_adult.dropna(
    subset=predictors + ["Statin"]
)

lasso2_check = df_adult.dropna(
    subset=predictors + ["Statin", "LDL_Controlled"]
)

print("\nComplete cases available for LASSO 1:")
print(len(lasso1_check))

print("\nStatin distribution in LASSO 1:")
print(lasso1_check["Statin"].value_counts())

print("\nComplete cases available for LASSO 2:")
print(len(lasso2_check))

print("\nLDL Controlled distribution in LASSO 2:")
print(lasso2_check["LDL_Controlled"].value_counts())


# In[9]:


# S5: PREPARE VARIABLES FOR THE TWO LASSO MODELS

# A. Create LASSO 1 dataset

lasso1 = lasso1_check[
    predictors + ["Statin"]
].copy()


# B. Create LASSO 2 dataset

lasso2 = lasso2_check[
    predictors + ["Statin", "LDL_Controlled"]
].copy()


# C. Convert Race to categorical dummy variables

lasso1 = pd.get_dummies(
    lasso1,
    columns=["Race"],
    prefix="Race",
    drop_first=True,
    dtype=int
)

lasso2 = pd.get_dummies(
    lasso2,
    columns=["Race"],
    prefix="Race",
    drop_first=True,
    dtype=int
)


# D. Display variables and sample sizes

print("LASSO 1 shape:", lasso1.shape)
print("\nLASSO 1 variables:")
print(lasso1.columns.tolist())

print("\nLASSO 2 shape:", lasso2.shape)
print("\nLASSO 2 variables:")
print(lasso2.columns.tolist())

print("\nFirst 5 rows of LASSO 1:")
print(lasso1.head())

print("\nFirst 5 rows of LASSO 2:")
print(lasso2.head())


# In[11]:


# S6: RUN LASSO 1 TO IDENTIFY PARENTS OF STATIN USE

# A. Import packages

import numpy as np
import pandas as pd

from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import log_loss


# B. Define response and predictors

X1 = lasso1.drop(columns=["Statin"])
y1 = lasso1["Statin"].astype(int)

feature_names1 = X1.columns.tolist()


# C. Standardize predictors

scaler1 = StandardScaler()

X1_scaled = scaler1.fit_transform(X1)


# D. Create lambda grid and cross-validation

lambdas = np.logspace(-4, 2, 50)

cv = StratifiedKFold(
    n_splits=5,
    shuffle=True,
    random_state=42
)

mean_losses = []
se_losses = []

for lam in lambdas:

    fold_losses = []

    for train_idx, test_idx in cv.split(X1_scaled, y1):

        model = LogisticRegression(
            penalty="l1",
            solver="liblinear",
            C=1 / lam,
            max_iter=2000
        )

        model.fit(
            X1_scaled[train_idx],
            y1.iloc[train_idx]
        )

        probs = model.predict_proba(
            X1_scaled[test_idx]
        )[:, 1]

        fold_losses.append(
            log_loss(y1.iloc[test_idx], probs)
        )

    mean_losses.append(np.mean(fold_losses))
    se_losses.append(
        np.std(fold_losses, ddof=1) / np.sqrt(cv.get_n_splits())
    )


# E. Find lambda.min and lambda.1se

mean_losses = np.array(mean_losses)
se_losses = np.array(se_losses)

min_index = np.argmin(mean_losses)

lambda_min = lambdas[min_index]

threshold = (
    mean_losses[min_index]
    + se_losses[min_index]
)

eligible = np.where(
    mean_losses <= threshold
)[0]

lambda_1se = lambdas[eligible[-1]]

print("lambda.min:", lambda_min)
print("lambda.1se:", lambda_1se)


# F. Fit final model at lambda.1se

lasso1_model = LogisticRegression(
    penalty="l1",
    solver="liblinear",
    C=1 / lambda_1se,
    max_iter=2000
)

lasso1_model.fit(
    X1_scaled,
    y1
)


# G. Display coefficients and selected parents

results1 = pd.DataFrame({
    "Variable": feature_names1,
    "Coefficient": lasso1_model.coef_[0]
})

results1["Selected"] = (
    results1["Coefficient"] != 0
)

results1 = results1.sort_values(
    "Coefficient",
    key=abs,
    ascending=False
)

print("\nLASSO 1 coefficients at lambda.1se:")
print(results1.to_string(index=False))

print("\nSelected parents of Statin:")
print(
    results1.loc[
        results1["Selected"],
        ["Variable", "Coefficient"]
    ].to_string(index=False)
)


# In[13]:


# S7: RUN LASSO 2 TO IDENTIFY PARENTS OF LDL CONTROL

# A. Define response and predictors

X2 = lasso2.drop(columns=["LDL_Controlled"])
y2 = lasso2["LDL_Controlled"].astype(int)

feature_names2 = X2.columns.tolist()


# B. Standardize predictors

scaler2 = StandardScaler()

X2_scaled = scaler2.fit_transform(X2)


# C. Run cross-validation

mean_losses2 = []
se_losses2 = []

for lam in lambdas:

    fold_losses = []

    for train_idx, test_idx in cv.split(X2_scaled, y2):

        model = LogisticRegression(
            penalty="l1",
            solver="liblinear",
            C=1 / lam,
            max_iter=2000
        )

        model.fit(
            X2_scaled[train_idx],
            y2.iloc[train_idx]
        )

        probs = model.predict_proba(
            X2_scaled[test_idx]
        )[:, 1]

        fold_losses.append(
            log_loss(y2.iloc[test_idx], probs)
        )

    mean_losses2.append(np.mean(fold_losses))
    se_losses2.append(
        np.std(fold_losses, ddof=1) / np.sqrt(cv.get_n_splits())
    )


# D. Find lambda.min and lambda.1se

mean_losses2 = np.array(mean_losses2)
se_losses2 = np.array(se_losses2)

min_index2 = np.argmin(mean_losses2)

lambda_min2 = lambdas[min_index2]

threshold2 = (
    mean_losses2[min_index2]
    + se_losses2[min_index2]
)

eligible2 = np.where(
    mean_losses2 <= threshold2
)[0]

lambda_1se2 = lambdas[eligible2[-1]]

print("lambda.min:", lambda_min2)
print("lambda.1se:", lambda_1se2)


# E. Fit final model at lambda.1se

lasso2_model = LogisticRegression(
    penalty="l1",
    solver="liblinear",
    C=1 / lambda_1se2,
    max_iter=2000
)

lasso2_model.fit(
    X2_scaled,
    y2
)


# F. Display coefficients and selected parents

results2 = pd.DataFrame({
    "Variable": feature_names2,
    "Coefficient": lasso2_model.coef_[0]
})

results2["Selected"] = (
    results2["Coefficient"] != 0
)

results2 = results2.sort_values(
    "Coefficient",
    key=abs,
    ascending=False
)

print("\nLASSO 2 coefficients at lambda.1se:")
print(results2.to_string(index=False))

print("\nSelected parents of LDL_Controlled:")
print(
    results2.loc[
        results2["Selected"],
        ["Variable", "Coefficient"]
    ].to_string(index=False)
)


# In[15]:


# S8: PRINT CLEAN SELECTED-PARENT TABLES

# A. Clean LASSO 1 selected parents

parents_statin = (
    results1.loc[
        results1["Selected"],
        ["Variable", "Coefficient"]
    ]
    .copy()
)

parents_statin["Response"] = "Statin"

parents_statin = parents_statin[
    ["Response", "Variable", "Coefficient"]
]


# B. Clean LASSO 2 selected parents

parents_ldl = (
    results2.loc[
        results2["Selected"],
        ["Variable", "Coefficient"]
    ]
    .copy()
)

# Combine race dummy variables into one conceptual Race node
race_rows = parents_ldl[
    parents_ldl["Variable"].str.startswith("Race_")
]

parents_ldl = parents_ldl[
    ~parents_ldl["Variable"].str.startswith("Race_")
].copy()

if len(race_rows) > 0:
    race_row = pd.DataFrame({
        "Variable": ["Race"],
        "Coefficient": [race_rows["Coefficient"].abs().max()]
    })

    parents_ldl = pd.concat(
        [parents_ldl, race_row],
        ignore_index=True
    )

parents_ldl["Response"] = "LDL_Controlled"

parents_ldl = parents_ldl[
    ["Response", "Variable", "Coefficient"]
]


# C. Print both tables

print("PARENTS OF STATIN")
print("=" * 50)
print(parents_statin.to_string(index=False))

print("\nPARENTS OF LDL_CONTROLLED")
print("=" * 50)
print(parents_ldl.to_string(index=False))


# In[17]:


# S9: DRAW THE DAG IN PYTHON

# A. Import packages

import networkx as nx
import matplotlib.pyplot as plt


# B. Create directed graph

G = nx.DiGraph()


# C. Add arrows into Statin

statin_parents = parents_statin["Variable"].tolist()

for parent in statin_parents:
    G.add_edge(parent, "Statin")


# D. Add arrows into LDL_Controlled

ldl_parents = parents_ldl["Variable"].tolist()

for parent in ldl_parents:
    G.add_edge(parent, "LDL_Controlled")


# E. Set node positions

pos = {
    "Age": (0, 4),
    "Sex": (1, 4),
    "Race": (2, 4),
    "Diabetes": (3, 4),
    "Hypertension": (4, 4),

    "High_Cholesterol": (0.5, 3),
    "Coronary_Heart_Disease": (2, 3),
    "Heart_Attack": (3.5, 3),
    "Stroke": (4.5, 3),
    "Ever_Smoked": (5.5, 3),

    "Statin": (2.5, 1.8),
    "LDL_Controlled": (2.5, 0)
}


# F. Draw DAG

plt.figure(figsize=(14, 9))

nx.draw(
    G,
    pos,
    with_labels=True,
    node_size=2800,
    font_size=9,
    arrows=True,
    arrowsize=20
)

plt.title(
    "DAG: LASSO-Selected Parents of Statin Use and LDL Control"
)

plt.show()


# In[ ]:




