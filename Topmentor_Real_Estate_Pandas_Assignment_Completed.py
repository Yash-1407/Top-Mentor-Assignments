# TopMentor - High-Performance Real Estate Analytics with Pandas
# Completed solution for the 20-question Bengaluru real-estate assignment.
# Uses Pandas vectorized/groupby/transform/agg operations; no SQL or row-wise loops.

import pandas as pd
import numpy as np
import re

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 140)

df = pd.read_csv("Bengaluru_House_Data.csv")
print("Shape:", df.shape)
print(df.head())


# ============ 1. Range Token Problem ============
def parse_total_sqft(value):
    if pd.isna(value):
        return np.nan

    text = str(value).strip()
    # Explicitly reject known non-sq-ft units.
    if re.search(r"sq\.?\s*(meter|mtr)|perch|acre|cent|yard|sq\.?\s*yd", text, flags=re.I):
        return np.nan

    # Handle ranges such as "2100 - 2850".
    numbers = re.findall(r"\d+(?:\.\d+)?", text)
    if len(numbers) >= 2 and re.search(r"-|to", text, flags=re.I):
        return (float(numbers[0]) + float(numbers[1])) / 2

    # Preserve a clean numeric value.
    if re.fullmatch(r"\s*\d+(?:\.\d+)?\s*", text):
        return float(text)

    # Accept a numeric token when harmless text surrounds it.
    if len(numbers) == 1 and re.fullmatch(r"\s*\d+(?:\.\d+)?\s*(sq\.?\s*ft|sqft)?\s*", text, flags=re.I):
        return float(numbers[0])

    return np.nan

df["total_sqft"] = df["total_sqft"].apply(parse_total_sqft)
print(df["total_sqft"].head())

# ============ 2. Feature Extraction via Regex ============
df["bhk"] = pd.to_numeric(
    df["size"].astype("string").str.extract(r"(\d+(?:\.\d+)?)", expand=False),
    errors="coerce"
).astype("Int64")

df = df.dropna(subset=["size", "bhk"]).copy()
df["bhk"] = df["bhk"].astype(int)

print("Shape after size/BHK validation:", df.shape)
print(df[["size", "bhk"]].head())

# ============ 3. Data Integrity Filter ============
df["sqft_per_bhk"] = df["total_sqft"] / df["bhk"]
df = df.loc[df["sqft_per_bhk"].ge(300) | df["sqft_per_bhk"].isna()].copy()

print("Shape after size-outlier filtering:", df.shape)

# ============ 4. Anomalous Bathroom Detection ============
bath_anomalies = df.loc[df["bath"].gt(df["bhk"] + 2)].copy()
print("Anomalous bathroom rows:", len(bath_anomalies))
print(bath_anomalies.head())

df = df.loc[~df["bath"].gt(df["bhk"] + 2)].copy()

# ============ 5. High-Volume Market Metrics ============
df["price_per_sqft"] = (df["price"] * 100000) / df["total_sqft"]

location_metrics = (
    df.dropna(subset=["location", "price_per_sqft"])
      .groupby("location")
      .agg(listings=("price_per_sqft", "size"),
           mean_price_per_sqft=("price_per_sqft", "mean"))
      .query("listings >= 15")
      .sort_values("mean_price_per_sqft", ascending=False)
      .head(5)
)

print(location_metrics)

# ============ 6. Executive Cross-Tabulation Matrix ============
pivot_median_price = pd.pivot_table(
    df,
    index="area_type",
    columns="balcony",
    values="price",
    aggfunc="median",
    fill_value=0
)

print(pivot_median_price)

# ============ 7. Volatile Real Estate Ecosystems ============
volatility = (
    df.dropna(subset=["location", "price_per_sqft"])
      .groupby("location")
      .agg(listings=("price_per_sqft", "size"),
           price_per_sqft_std=("price_per_sqft", "std"))
      .query("listings >= 10")
      .sort_values("price_per_sqft_std", ascending=False)
      .head(3)
)

print(volatility)

# ============ 8. Micro-Market Dominance ============
top3_busiest_locations = df["location"].value_counts().head(3).index

society_counts = (
    df.loc[df["location"].isin(top3_busiest_locations) & df["society"].notna()]
      .groupby(["location", "society"])
      .size()
      .rename("listings")
      .reset_index()
)

top2_societies = (
    society_counts.assign(
        rank=lambda x: x.groupby("location")["listings"].rank(method="first", ascending=False)
    )
    .query("rank <= 2")
    .sort_values(["location", "listings"], ascending=[True, False])
)

print(top2_societies)

# ============ 9. Intra-Location Dense Ranking ============
df["location_price_rank"] = (
    df.groupby("location")["price_per_sqft"]
      .rank(method="dense", ascending=False)
)

print(df[["location", "price_per_sqft", "location_price_rank"]].head(10))

# ============ 10. Locality Average Delta ============
df["location_avg_price"] = df.groupby("location")["price"].transform("mean")
df["price_deviation_pct"] = (
    (df["price"] - df["location_avg_price"])
    .div(df["location_avg_price"])
    .mul(100)
)

print(df[["location", "price", "location_avg_price", "price_deviation_pct"]].head(10))

# ============ 11. Macro Market Quartile Binning ============
valid_pps = df["price_per_sqft"].notna()
df["price_tier"] = pd.NA

# Rank first prevents duplicate-edge values from collapsing qcut bins.
ranked_pps = df.loc[valid_pps, "price_per_sqft"].rank(method="first")
df.loc[valid_pps, "price_tier"] = pd.qcut(
    ranked_pps,
    q=4,
    labels=["Budget", "Standard", "Premium", "Luxury"]
)

print(df[["price_per_sqft", "price_tier"]].head(10))
print(df["price_tier"].value_counts(dropna=False))

# ============ 12. Rolling 3-Property Micro-Trend ============
whitefield = (
    df.loc[df["location"].astype("string").str.strip().str.casefold().eq("whitefield")]
      .sort_values("total_sqft")
      .copy()
)

whitefield["rolling_3_property_avg_price"] = (
    whitefield["price"].rolling(window=3, min_periods=1).mean()
)

print(whitefield[["location", "total_sqft", "price", "rolling_3_property_avg_price"]])

# ============ 13. Cumulative Portfolio Capitalization ============
sarjapur = (
    df.loc[df["location"].astype("string").str.strip().str.casefold().eq("sarjapur road")]
      .sort_values(["bhk", "price"], ascending=[True, True])
      .copy()
)

sarjapur["cumulative_price"] = sarjapur["price"].cumsum()

print(sarjapur[["location", "bhk", "price", "cumulative_price"]])

# ============ 14. Peer Price Delta Analysis ============
peer = (
    df.sort_values(["location", "total_sqft"], ascending=[True, False])
      .copy()
)

peer["next_largest_sqft_price"] = peer.groupby("location")["price"].shift(-1)
peer["price_delta_to_next_larger"] = peer["price"] - peer["next_largest_sqft_price"]

print(peer[[
    "location", "total_sqft", "price",
    "next_largest_sqft_price", "price_delta_to_next_larger"
]].head(15))

# ============ 15. Price Inversion Anomalies ============
bhk_means = (
    df.loc[df["bhk"].isin([2, 3])]
      .groupby(["location", "bhk"])["price"]
      .mean()
      .unstack()
      .rename(columns={2: "mean_2bhk_price", 3: "mean_3bhk_price"})
)

price_inversions = bhk_means.loc[
    bhk_means["mean_2bhk_price"].gt(bhk_means["mean_3bhk_price"])
    & bhk_means["mean_2bhk_price"].notna()
    & bhk_means["mean_3bhk_price"].notna()
].sort_values("mean_2bhk_price", ascending=False)

print(price_inversions)

# ============ 16. Structural Distribution Footprint ============
bhk_distribution = pd.crosstab(
    df["area_type"],
    df["bhk"],
    normalize="index"
).mul(100)

print(bhk_distribution.round(2))

# ============ 17. Dynamic Structural Tagging ============
highest_price_society = (
    df.loc[df["price"].notna() & df["society"].notna()]
      .sort_values(["location", "price"], ascending=[True, False])
      .drop_duplicates("location")
      .set_index("location")["society"]
)

df["highest_paid_society_in_location"] = df["location"].map(highest_price_society)

print(df[[
    "location", "price", "society", "highest_paid_society_in_location"
]].head(15))

# ============ 18. The Bookends Architecture ============
availability_counts = (
    df.dropna(subset=["location", "availability"])
      .groupby(["location", "availability"])
      .size()
      .rename("listing_count")
      .reset_index()
)

least_available = (
    availability_counts.sort_values(
        ["location", "listing_count", "availability"],
        ascending=[True, True, True]
    )
    .drop_duplicates("location")
    .rename(columns={"availability": "least_available_type",
                     "listing_count": "least_available_count"})
)

most_available = (
    availability_counts.sort_values(
        ["location", "listing_count", "availability"],
        ascending=[True, False, True]
    )
    .drop_duplicates("location")
    .rename(columns={"availability": "most_available_type",
                     "listing_count": "most_available_count"})
)

bookends = least_available.merge(
    most_available,
    on="location",
    how="outer"
).sort_values("location")

print(bookends)

# ============ 19. Missingness Thresholding ============
missing_pct = df.isna().mean().mul(100).sort_values(ascending=False)
print("Missing percentage by column:")
print(missing_pct.to_frame("missing_pct"))

columns_to_drop = missing_pct[missing_pct.gt(35)].index.tolist()
df_clean = df.drop(columns=columns_to_drop).copy()

print("Columns dropped (>35% missing):", columns_to_drop)
print("Final analytical shape:", df_clean.shape)

# ============ 20. Executive Master Summary ============
def dominant_area_type(series):
    mode = series.dropna().mode()
    return mode.iloc[0] if not mode.empty else np.nan

master_summary = (
    df_clean.groupby("location")
    .agg(
        Total_Listings=("location", "size"),
        Total_Revenue_Capacity=("price", "sum"),
        Mean_BHK=("bhk", "mean"),
        Median_Price_per_Sqft=("price_per_sqft", "median"),
        dominant_area_type=("area_type", dominant_area_type)
    )
    .sort_values("Total_Listings", ascending=False)
)

print(master_summary)