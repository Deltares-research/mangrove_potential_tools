import os
import rioxarray
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from pygam import LogisticGAM, s
import matplotlib.pyplot as plt


# -----------------------------
# Settings
folder = r"C:\Ocean\Work\Projects\2025\Mangroves\Data\0_Workflow\areas_of_interest"
id_tile = "N09E104" #"N00E117", N09E104, #S06E110

# -----------------------------
# Create results folder
results_folder = os.path.join(folder, f"Results_GAM_{id_tile}")
os.makedirs(results_folder, exist_ok=True)

# -----------------------------
# Find feature rasters
feature_rasters = []
for f in os.listdir(folder):
    if f.lower().endswith(".tif") and len(f.split("_")) > 1:
        second_elem = f.split("_")[1]
        if f.startswith("GMW"):
            continue
        if second_elem != id_tile:
            continue
        if f.startswith("R25") and not f.endswith("_2020.tif"):
            continue
        feature_rasters.append(os.path.join(folder, f))

print(f"Found {len(feature_rasters)} raster(s)")

# -----------------------------
# Load feature rasters
feature_arrays = []
feature_names = []

for f in feature_rasters:
    da = rioxarray.open_rasterio(f, masked=True)
    feature_arrays.append(da.values.flatten())
    feature_names.append(os.path.basename(f)[:3])

# Stack features as columns
X = np.vstack(feature_arrays).T

# -----------------------------
# Combine into DataFrame
df = pd.DataFrame(X, columns=feature_names)

df.fillna(0, inplace=True)
tmp = df.drop(columns=["GTS"], errors="ignore")
df["total"] = tmp.sum(axis=1)
df = df[df["total"] != 0]
df.drop(columns=['R25', 'total'], inplace=True)
df = df[~((df["HIS"] == 0) & (df["REC"] == 0))]

# -----------------------------
# Convert HIS and REC

def convert_rec(value):
    return 1 if value >= 2007 else 0

df["REC"] = df["REC"].apply(convert_rec)

# Create HIS_REC column
df["HIS_REC"] = df["REC"]
df.drop(columns=['ACC', 'HIS', 'REC'], inplace=True)

# -----------------------------
# Sample 5000 rows per class
sample0 = df[df["HIS_REC"] == 0].sample(n=5000, random_state=42)
sample1 = df[df["HIS_REC"] == 1].sample(n=5000, random_state=42)
df_sampled = pd.concat([sample0, sample1], ignore_index=True)

# Save sampled DataFrame
df_sampled.to_csv(os.path.join(results_folder, "df_sampled.csv"), index=False)

# -----------------------------
# Prepare data for ML
X_ml = df_sampled.drop(columns=["HIS_REC"])
y_ml = df_sampled["HIS_REC"]

X_train, X_test, y_train, y_test = train_test_split(
    X_ml, y_ml, test_size=0.3, random_state=42, stratify=y_ml
)

# Fit GAM model with smooth terms for each predictor
gam = LogisticGAM(s(0) + s(1) + s(2)).fit(X_train, y_train)
 
# Build s(0) + s(1) + ... + s(n)
terms = s(0)
for i in range(1, X_train.shape[1]):
    terms += s(i)

gam = LogisticGAM(terms).fit(X_train, y_train)

# Save summary
with open(os.path.join(results_folder, "gam_summary.txt"), "w") as f:
    f.write(str(gam.summary()))

# -----------------------------
# Evaluate predictions
y_prob = gam.predict_proba(X_test)
y_pred = (y_prob >= 0.5).astype(int)

cm = confusion_matrix(y_test, y_pred)
report = classification_report(y_test, y_pred)

with open(os.path.join(results_folder, "gam_results.txt"), "w") as f:
    f.write("Confusion Matrix:\n")
    f.write(np.array2string(cm))
    f.write("\n\nClassification Report:\n")
    f.write(report)

# -----------------------------
# Partial dependence plots for ALL predictors
n_features = X_train.shape[1]
n_cols = min(3, n_features)
n_rows = int(np.ceil(n_features / n_cols))

fig, axs = plt.subplots(n_rows, n_cols, figsize=(5*n_cols, 4*n_rows))
axs = np.atleast_1d(axs).ravel()

for i in range(n_features):
    ax = axs[i]
    XX = gam.generate_X_grid(term=i)
    pdep, conf = gam.partial_dependence(term=i, width=0.95)

    # conf is (n_points, 2)
    if conf.ndim == 2 and conf.shape[1] == 2:
        lower, upper = conf[:, 0], conf[:, 1]
    else:
        # fallback: no confidence interval
        lower, upper = pdep, pdep

    ax.plot(XX[:, i], pdep)
    ax.fill_between(XX[:, i], lower, upper, alpha=0.3)
    title = feature_cols[i] if i < len(feature_cols) else f"Feature {i}"
    ax.set_title(title)
    ax.set_xlabel(title)
    ax.set_ylabel("Log-odds (partial)")

# Hide any unused subplots
for j in range(n_features, len(axs)):
    axs[j].axis("off")

plt.tight_layout()
plt.savefig(os.path.join(results_folder, "gam_partial_dependence.png"))
plt.close()

print("GAM modeling complete. Results saved in:", results_folder)


