import pandas as pd

df = pd.read_csv("data/EAFC26-Men.csv")

print("Shape:", df.shape)
print()
print("Columns:")
print(df.columns.tolist())
