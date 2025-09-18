import os
import rioxarray
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import seaborn as sns
import matplotlib.pyplot as plt

# -----------------------------
# Settings
folder = r"C:\Ocean\Work\Projects\2025\Mangroves\Data\0_Workflow\areas_of_interest"
id_tile = "N09E104" #"N00E117", N09E104, #S06E110

# -----------------------------
# Create results folder
results_folder = os.path.join(folder, f"Results_{id_tile}")
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
def convert_his(value):
    return 1 if value <= 2019 else 0

def convert_rec(value):
    return 2 if value >= 2007 else 0

df["HIS"] = df["HIS"].apply(convert_his)
df["REC"] = df["REC"].apply(convert_rec)

# Create HIS_REC column
df["HIS_REC"] = df["HIS"] + df["REC"]
df.drop(columns=['ACC', 'HIS', 'REC'], inplace=True)

# -----------------------------
# Sample 5000 rows per class
sample0 = df[df["HIS_REC"] == 0].sample(n=5000, random_state=42)
sample1 = df[df["HIS_REC"] == 1].sample(n=5000, random_state=42)
sample2 = df[df["HIS_REC"] == 2].sample(n=5000, random_state=42)
df_sampled = pd.concat([sample0, sample1, sample2], ignore_index=True)

# Save sampled DataFrame
df_sampled.to_csv(os.path.join(results_folder, "df_sampled.csv"), index=False)

# -----------------------------
# Correlation matrix
correlation_matrix = df_sampled.corr()
correlation_matrix.to_csv(os.path.join(results_folder, "correlation_matrix.csv"))

# Visualize correlation and save as image
plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, fmt=".2f", cmap="coolwarm")
plt.title("Correlation matrix")
plt.tight_layout()
plt.savefig(os.path.join(results_folder, "correlation_matrix.png"))
plt.show()

# -----------------------------
# Prepare data for ML
X_ml = df_sampled.drop(columns=["HIS_REC"])
y_ml = df_sampled["HIS_REC"]

X_train, X_test, y_train, y_test = train_test_split(
    X_ml, y_ml, test_size=0.3, random_state=42, stratify=y_ml
)

# -----------------------------
# Random Forest Classifier
rf = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
rf.fit(X_train, y_train)
y_pred = rf.predict(X_test)

# -----------------------------
# Evaluate model
cm = confusion_matrix(y_test, y_pred)
report = classification_report(y_test, y_pred)
importances = pd.Series(rf.feature_importances_, index=X_ml.columns).sort_values(ascending=False)

# Save evaluation results
with open(os.path.join(results_folder, "model_results.txt"), "w") as f:
    f.write("Confusion Matrix:\n")
    f.write(np.array2string(cm))
    f.write("\n\nClassification Report:\n")
    f.write(report)
    f.write("\n\nFeature Importances:\n")
    f.write(importances.to_string())

print("Results saved in:", results_folder)

