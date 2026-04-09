import streamlit as st
import pandas as pd
from PIL import Image

import streamlit as st
import pandas as pd
from PIL import Image


# SIMPLE LOGIN GATE
def check_login():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if st.session_state.authenticated:
        return True

    st.set_page_config(layout="wide")

    col1, col2, col3 = st.columns([1, 1.2, 1])

    with col2:
        st.markdown("## Login")
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login")

        if submitted:
            valid_username = st.secrets["auth"]["username"]
            valid_password = st.secrets["auth"]["password"]

            if username == valid_username and password == valid_password:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("Invalid username or password")

    return False


if not check_login():
    st.stop()

st.set_page_config(layout="wide")

st.markdown("""
<style>
@font-face {
    font-family: 'Breymont';
    src: url('/app/static/Breymont-Bold.ttf') format('truetype');
    font-weight: 700;
    font-style: normal;
}

.breymont-title {
    font-family: 'Breymont', sans-serif !important;
    text-align: center;
    font-weight: 300;
    font-size: 2.2rem;
}
</style>
""", unsafe_allow_html=True)


# sidebar
st.sidebar.markdown("## 🔎 Filters")

# --- Load main dataset ---
data = pd.read_csv("influencer_dataset_test.csv")
data.columns = data.columns.str.strip()
data["Name"] = data["Name"].fillna("").str.strip().str.lower()
data["Platforms"] = data["Platforms"].fillna("")

# Forward-fill Name
data["Name"] = data["Name"].replace("", pd.NA)
data["Name"] = data["Name"].ffill()

# --- Load category ---
categories = pd.read_csv("influencer_category.tsv", sep="\t")
categories.columns = categories.columns.str.strip()
categories["Name"] = categories["Name"].fillna("").str.strip().str.lower()

category_columns = [col for col in categories.columns if col != "Name"]

category_long = categories.melt(
    id_vars=["Name"],
    value_vars=category_columns,
    var_name="Category",
    value_name="Value"
)

category_long = category_long[
    category_long["Value"].astype(str).str.lower().isin(["yes", "1", "true", "x"])
]

category_long = category_long[["Name", "Category"]]

data = data.merge(category_long, on="Name", how="left")

# --- Followers conversion ---
def convert_followers(x):
    x = str(x).lower().replace(",", "").strip()
    if "k" in x:
        return float(x.replace("k", "")) * 1000
    try:
        return float(x)
    except:
        return 0

data["Follower count"] = data["Follower count"].apply(convert_followers)

# sidebarfilters
use_follower_filter = st.sidebar.checkbox("Activate follower filter")

if use_follower_filter:
    min_f = int(data["Follower count"].min())
    max_f = int(data["Follower count"].max())

    follower_range = st.sidebar.slider(
        "Follower range",
        min_value=min_f,
        max_value=max_f,
        value=(min_f, max_f)
    )

#platform filter
platform_list = []
for val in data["Platforms"].dropna():
    val = str(val)
    if "IG" in val:
        platform_list.append("IG")
    if "TTK" in val:
        platform_list.append("TTK")
    if "FB" in val:
        platform_list.append("FB")

platform_list = sorted(list(set(platform_list)))
selected_platform = st.sidebar.selectbox("Platform", ["None"] + platform_list)

# Category filter
category_list = sorted(category_long["Category"].unique().tolist())
selected_category = st.sidebar.selectbox("Category", ["None"] + category_list)

# main centered content
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # Logo
    with col2:
        
        logo = Image.open("logo_underdogs.png")
        col_logo_left, col_logo_center, col_logo_right = st.columns([1, 2, 1])
    with col_logo_center:
        st.image(logo, width=180)

    # Title
    st.markdown(
    """
    <h1 class="breymont-title">
        Underdogs Influencer Finder
    </h1>
    """,
    unsafe_allow_html=True
)

    # Search
    all_names = sorted(data["Name"].dropna().unique())
    search_input = st.text_input("Search influencer by name").lower().strip()

    # Suggestions
    if search_input:
        matching_names = [name for name in all_names if search_input in name]
        if matching_names:
            st.markdown("**Suggestions:**")
            for m in matching_names[:8]:
                st.markdown(f"- {m}")

search = search_input

# logic
if not search and not use_follower_filter and selected_platform == "None" and selected_category == "None":
    
    c1, c2, c3 = st.columns([1, 2, 1])

    with c2:
        st.markdown(
            """
            <div style="
                text-align: center;
                padding: 12px;
                border-radius: 10px;
                background-color: #e8f4fd;
                color: #0b5394;
                font-size: 14px;
                width: 100%;
            ">
            Please search or use filters from the left panel
            </div>
            """,
            unsafe_allow_html=True
        )

else:
    filtered = data.copy()

    # Apply follower filter
    if use_follower_filter:
        filtered = filtered[
            (filtered["Follower count"] >= follower_range[0]) &
            (filtered["Follower count"] <= follower_range[1])
        ]

    # Platform filter
    if selected_platform != "None":
        filtered = filtered[
            filtered["Platforms"].str.contains(selected_platform, na=False)
        ]

    # Category filter
    if selected_category != "None":
        filtered = filtered[
            filtered["Category"] == selected_category
        ]

    # Search filter
    if search:
        filtered = filtered[
            filtered["Name"].str.contains(search, na=False)
        ]

    # results
    if not filtered.empty:

        # Platform-specific ranking
        if selected_platform != "None":
            ranking = (
                filtered[filtered["Platforms"].str.contains(selected_platform, na=False)]
                .groupby("Name")["Follower count"]
                .max()
                .sort_values(ascending=False)
            )
        else:
            ranking = (
                filtered.groupby("Name")["Follower count"]
                .max()
                .sort_values(ascending=False)
            )

        # Apply ranking
        filtered["Name"] = pd.Categorical(
            filtered["Name"],
            categories=ranking.index,
            ordered=True
        )

        filtered = filtered.sort_values("Name")
        grouped = filtered.groupby("Name", sort=False)

        # Display results (FULL WIDTH BELOW)
        st.markdown("---")

        for name, group in grouped:
            st.markdown(f"## {name}")

            # Platforms summary
            platform_info = []
            for _, row in group.iterrows():
                platform = row.get("Platforms", "")
                followers = row.get("Follower count", 0)

                followers = int(followers) if pd.notna(followers) else 0

                if platform:
                    platform_info.append(f"{platform} {followers} Followers")

            platform_info = list(set(platform_info))

            # Contacts
            phone_col = next((col for col in group.columns if "phone" in col.lower()), None)
            email_col = next((col for col in group.columns if "mail" in col.lower()), None)

            phone = next((x for x in group[phone_col] if x), "N/A") if phone_col else "N/A"
            email = next((x for x in group[email_col] if x), "N/A") if email_col else "N/A"

            st.markdown("**Platforms & Reach:**")
            for p in platform_info:
                st.markdown(f"- {p}")

            st.markdown(f"📞 **Phone:** {phone}")
            st.markdown(f"📧 **Email:** {email}")

            display_group = group.drop(columns=["Name", "Category"], errors="ignore")
            display_group = display_group.drop_duplicates()
            display_group = display_group.loc[:, (display_group != "").any(axis=0)]

            if "Follower count" in display_group.columns:
                display_group = display_group.sort_values(by="Follower count", ascending=False)

            st.dataframe(display_group, use_container_width=True)
            st.markdown("---")

    else:
        st.warning("No influencers found")