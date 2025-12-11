import pandas as pd
import matplotlib.pyplot as plt

data = {
    "Country": [
        "Angola", "Burundi", "Botswana", "DR of Congo", "Kenya", "Madagascar",
        "Mozambique", "Malawi", "Namibia", "Tanzania", "Uganda",
        "South Africa", "Zambia", "Zimbabwe"
    ],
    "Regional Early Refining 2040": [5, 15, 2, 35, 0, 6, 4, 7, 35, 27, 0, 1, 5, 2],
    "Regional Precursor 2040": [3, 15, 2, 35, 0, 6, 4, 7, 35, 20, 0, 1, 5, 2],
    "Country Early Refining 2040": [0, 0, 10, 31, 0, 0, 2, 6, 10, 6, 0, 0, 3, 1],
    "Country Precursor 2040": [0, 0, 0, 31, 0, 0, 1, 5, 6, 5, 0, 0, 2, 1]
}

df = pd.DataFrame(data)

# Example grouped bar plot
df.plot(
    x="Country",
    kind="bar",
    figsize=(12, 6),
    title="Percentage Change Relative to the Reference (2040)",
)
plt.ylabel("Percentage Change (%)")
plt.show()
