import pandas as pd
import numpy as np


RAW_INFO_FILE = "Influencer Database - Influencer info-2.csv"
RAW_CATEGORY_FILE = "Influencer Database - Categories.tsv"

OUTPUT_INFO_FILE = "influencer_dataset_test.csv"
OUTPUT_CATEGORY_FILE = "influencer_category.tsv"


def clean_text(series):
    return (
        series.astype(str)
        .str.replace("\u200e", "", regex=False)   # remove hidden left-to-right mark
        .str.replace("\xa0", " ", regex=False)    # remove non-breaking space
        .str.strip()
        .replace({"nan": "", "None": ""})
    )


def transform_influencer_info():
    raw = pd.read_csv(RAW_INFO_FILE, dtype=str).fillna("")

    # Row 2 contains the actual usable headers for columns B onward.
    # Row 3 onward contains the data blocks.
    data = raw.iloc[3:].copy()

    data = data.rename(columns={
        raw.columns[0]: "col_a",
        raw.columns[1]: "Platforms",
        raw.columns[2]: "Follower count",
        raw.columns[3]: "Tier",
        raw.columns[4]: "Brand Collabs",
        raw.columns[5]: "Previously worked with",
        raw.columns[6]: "Phone number",
        raw.columns[7]: "Mail",
        raw.columns[8]: "Media kit",
        raw.columns[9]: "Price",
        raw.columns[10]: "extra"
    })

    data = data[[
        "col_a",
        "Platforms",
        "Follower count",
        "Tier",
        "Brand Collabs",
        "Previously worked with",
        "Phone number",
        "Mail",
        "Media kit",
        "Price",
        "extra"
    ]].copy()

    for col in data.columns:
        data[col] = clean_text(data[col])

    # Influencer names are the rows where column A starts with @
    data["Name_marker"] = data["col_a"].where(data["col_a"].str.startswith("@"), "")

    # Keep only rows that belong to influencer records
    # (name rows, platform rows, or pricing/media-kit rows)
    keep_mask = (
        (data["Name_marker"] != "") |
        (data["Platforms"] != "") |
        (data["Media kit"] != "") |
        (data["Price"] != "")
    )
    data = data[keep_mask].copy()

    # Forward-fill the current influencer internally
    data["CurrentName"] = data["Name_marker"].replace("", np.nan).ffill().fillna("")

    # Remove the pure "name only" rows, because in your target format
    # the influencer name should sit on the first actual data row
    pure_name_only_mask = (
        (data["Name_marker"] != "") &
        (data["Platforms"] == "") &
        (data["Follower count"] == "") &
        (data["Tier"] == "") &
        (data["Brand Collabs"] == "") &
        (data["Previously worked with"] == "") &
        (data["Phone number"] == "") &
        (data["Mail"] == "") &
        (data["Media kit"] == "") &
        (data["Price"] == "")
    )
    data = data[~pure_name_only_mask].copy()

    # Put Name only on the first row of each influencer block,
    # leave following rows blank to match your current local test structure
    data["Name"] = np.where(
        data["CurrentName"] != data["CurrentName"].shift(1),
        data["CurrentName"],
        ""
    )

    # Remove pricing subheaders from the raw export
    data["Media kit"] = data["Media kit"].replace({"Item": ""})
    data["Price"] = data["Price"].replace({"Price": ""})

    final_info = data[[
        "Name",
        "Platforms",
        "Follower count",
        "Tier",
        "Brand Collabs",
        "Previously worked with",
        "Phone number",
        "Mail",
        "Media kit",
        "Price"
    ]].copy()

    final_info.to_csv(OUTPUT_INFO_FILE, index=False)
    print(f"Saved: {OUTPUT_INFO_FILE} ({len(final_info)} rows)")


def transform_categories():
    raw = pd.read_csv(RAW_CATEGORY_FILE, sep="\t", dtype=str).fillna("")

    # Row 2 has real headers, row 3 onward has data
    data = raw.iloc[3:].copy()

    data = data.rename(columns={
        raw.columns[0]: "col_a",
        raw.columns[1]: "Name",
        raw.columns[2]: "Lifestyle",
        raw.columns[3]: "Fashion & beauty",
        raw.columns[4]: "Food",
        raw.columns[5]: "Fitness & Wellness",
        raw.columns[6]: "Travel",
        raw.columns[7]: "Family",
        raw.columns[8]: "Entertainment",
        raw.columns[9]: "Education/Corporate",
        raw.columns[10]: "MC/Animator"
    })

    for col in data.columns:
        data[col] = clean_text(data[col])

    # Keep only actual influencer rows
    data = data[data["Name"].str.startswith("@")].copy()

    final_categories = data[[
        "Name",
        "Lifestyle",
        "Fashion & beauty",
        "Food",
        "Fitness & Wellness",
        "Travel",
        "Family",
        "Entertainment",
        "Education/Corporate",
        "MC/Animator"
    ]].copy()

    final_categories.to_csv(OUTPUT_CATEGORY_FILE, sep="\t", index=False)
    print(f"Saved: {OUTPUT_CATEGORY_FILE} ({len(final_categories)} rows)")


if __name__ == "__main__":
    transform_influencer_info()
    transform_categories()
    print("Done.")