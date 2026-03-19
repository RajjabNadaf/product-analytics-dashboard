# Import required libraries
import streamlit as st
import pandas as pd


# -----------------------------
# PAGE CONFIG (Optional but good practice)
# -----------------------------
st.set_page_config(page_title="Product Analytics", layout="wide")


# -----------------------------
# LOAD DATA
# -----------------------------
# Reads dataset from your data folder
# If path error comes, try 'data/events.csv'
df = pd.read_csv(r'data/events_sample.csv')

# Convert event_time to datetime (important for time-based analysis later)
df['event_time'] = pd.to_datetime(df['event_time'])


# -----------------------------
# SIDEBAR FILTERS
# -----------------------------
st.sidebar.header("🔎 Filters")

# Create dropdown with "All" + unique categories
category = st.sidebar.selectbox(
    "Select Category",
    options=["All"] + list(df['category_code'].dropna().unique())
)

# Apply filter
if category != "All":
    filtered_df = df[df['category_code'] == category]
else:
    filtered_df = df.copy()


# -----------------------------
# TITLE
# -----------------------------
st.title("📊 Product Analytics Dashboard")

# Show selected category
st.subheader(f"Selected Category: {category}")


# =============================
# 🔻 FUNNEL ANALYSIS
# =============================
st.header("Funnel Analysis")

# Group by event type and count unique users
funnel = filtered_df.groupby('event_type')['user_id'].nunique()

# Display raw funnel data
st.write("Users per stage:")
st.write(funnel)


# -----------------------------
# CONVERSION CALCULATIONS
# -----------------------------
# Safe extraction using .get() to avoid errors if key missing
view_to_cart = funnel.get('cart', 0) / funnel.get('view', 1)
cart_to_purchase = funnel.get('purchase', 0) / funnel.get('cart', 1)


# -----------------------------
# DISPLAY KPI METRICS
# -----------------------------
# Create 2 columns for better UI
col1, col2 = st.columns(2)

# Show conversion rates
col1.metric("View → Cart", f"{view_to_cart:.2%}")
col2.metric("Cart → Purchase", f"{cart_to_purchase:.2%}")


# -----------------------------
# FUNNEL CHART
# -----------------------------
st.bar_chart(funnel)


# =============================
# 🔻 CATEGORY LEVEL ANALYSIS
# =============================
st.header("Category-Level Analysis")

# Create pivot table
# Rows = category
# Columns = event type
# Values = unique users
category_funnel = df.pivot_table(
    index='category_code',
    columns='event_type',
    values='user_id',
    aggfunc='nunique'
).fillna(0)


# -----------------------------
# CONVERSION CALCULATIONS
# -----------------------------
category_funnel['view_to_cart'] = category_funnel['cart'] / category_funnel['view']
category_funnel['cart_to_purchase'] = category_funnel['purchase'] / category_funnel['cart']

# Replace infinite values (divide by zero cases)
category_funnel = category_funnel.replace([float('inf')], 0)


# -----------------------------
# SHOW DATA TABLE
# -----------------------------
st.subheader("Category Conversion Table")
st.dataframe(category_funnel.head(10))


# -----------------------------
# TOP CATEGORIES CHART
# -----------------------------
st.subheader("Top Categories by Conversion")

# Sort categories by best conversion
top_categories = category_funnel.sort_values(
    'cart_to_purchase', ascending=False
).head(10)

# Show chart
st.bar_chart(top_categories['cart_to_purchase'])


# =============================
# 🔻 FOOTER / INSIGHTS
# =============================
st.markdown("---")

st.markdown("""
### 💡 Key Insights

- Funnel shows where users drop off (View → Cart → Purchase)
- High cart abandonment may indicate UX or pricing issues
- Some categories convert significantly better than others
- Filters allow deep-dive into specific product segments
""")