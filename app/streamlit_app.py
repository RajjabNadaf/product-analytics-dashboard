# ==============================
# 📊 ECOMMERCE ANALYTICS DASHBOARD
# ==============================

import streamlit as st
import pandas as pd
import plotly.express as px

# -----------------------------
# PAGE CONFIG
# -----------------------------
st.set_page_config(page_title="Ecommerce Analytics", layout="wide")

# -----------------------------
# LOAD DATA
# -----------------------------
df = pd.read_csv('data/events_sample.csv')
df['event_time'] = pd.to_datetime(df['event_time'])

# Clean data
df = df.dropna(subset=['event_time', 'user_id'])

# -----------------------------
# SIDEBAR FILTER
# -----------------------------
st.sidebar.title("🔎 Filters")

category = st.sidebar.selectbox(
    "Select Category",
    ["All"] + list(df['category_code'].dropna().unique())
)

if category != "All":
    df = df[df['category_code'] == category]

# -----------------------------
# TITLE
# -----------------------------
st.title("📊 Ecommerce Analytics Dashboard")

# =============================
# KPI SECTION
# =============================
total_users = df['user_id'].nunique()
total_events = len(df)
total_purchases = df[df['event_type'] == 'purchase']['user_id'].nunique()

col1, col2, col3 = st.columns(3)

col1.metric("👥 Users", f"{total_users:,}")
col2.metric("⚡ Events", f"{total_events:,}")
col3.metric("🛒 Purchases", f"{total_purchases:,}")

st.markdown("---")

# =============================
# FUNNEL ANALYSIS
# =============================
st.subheader("🔻 Conversion Funnel")

funnel = df.groupby('event_type')['user_id'].nunique().reset_index()

order = ['view', 'cart', 'purchase']
funnel['event_type'] = pd.Categorical(funnel['event_type'], categories=order, ordered=True)
funnel = funnel.sort_values('event_type')

fig = px.funnel(funnel, x='user_id', y='event_type', title="User Funnel")
st.plotly_chart(fig, use_container_width=True)

# Extract values safely
view = funnel.loc[funnel['event_type']=='view', 'user_id'].values[0]
cart = funnel.loc[funnel['event_type']=='cart', 'user_id'].values[0]
purchase = funnel.loc[funnel['event_type']=='purchase', 'user_id'].values[0]

# =============================
# CONVERSION METRICS
# =============================
col1, col2 = st.columns(2)

col1.metric("View → Cart", f"{(cart/view):.2%}")
col2.metric("Cart → Purchase", f"{(purchase/cart):.2%}")

# =============================
# DROP-OFF ANALYSIS
# =============================
st.subheader("⚠️ Drop-Off Analysis")

drop_off_view_cart = 1 - (cart / view)
drop_off_cart_purchase = 1 - (purchase / cart)

col1, col2 = st.columns(2)

col1.metric("Drop-off (View → Cart)", f"{drop_off_view_cart:.2%}")
col2.metric("Drop-off (Cart → Purchase)", f"{drop_off_cart_purchase:.2%}")

# =============================
# CONVERSION BAR
# =============================
st.subheader("📊 Conversion Comparison")

conversion_df = pd.DataFrame({
    'Stage': ['View → Cart', 'Cart → Purchase'],
    'Conversion': [cart/view, purchase/cart]
})

fig = px.bar(conversion_df, x='Stage', y='Conversion', text_auto=True)
st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# =============================
# CATEGORY ANALYSIS
# =============================
st.subheader("📦 Category Performance")

category_perf = df.groupby('category_code')['user_id'].nunique().sort_values(ascending=False).head(10)

fig = px.bar(
    category_perf,
    x=category_perf.values,
    y=category_perf.index,
    orientation='h',
    title="Top Categories by Users"
)

st.plotly_chart(fig, use_container_width=True)

# =============================
# TIME ANALYSIS
# =============================
st.subheader("⏰ Activity Over Time")

df['hour'] = df['event_time'].dt.hour
hourly = df.groupby('hour')['user_id'].count()

fig = px.line(
    x=hourly.index,
    y=hourly.values,
    labels={'x': 'Hour of Day', 'y': 'Events'},
    title="User Activity by Hour"
)

st.plotly_chart(fig, use_container_width=True)

st.markdown("---")

# =============================
# COHORT ANALYSIS (FIXED ✅)
# =============================
st.subheader("📅 Cohort Retention")

# Keep Period for calculation
df['month_period'] = df['event_time'].dt.to_period('M')

# First purchase month
df['cohort_period'] = df.groupby('user_id')['month_period'].transform('min')

# Calculate index using Period (correct way)
df['cohort_index'] = (df['month_period'] - df['cohort_period']).apply(lambda x: x.n)

# Convert to string ONLY for display
df['cohort'] = df['cohort_period'].astype(str)

cohort_data = df.groupby(['cohort', 'cohort_index'])['user_id'].nunique().reset_index()

cohort_pivot = cohort_data.pivot_table(
    index='cohort',
    columns='cohort_index',
    values='user_id'
)

cohort_retention = cohort_pivot.divide(cohort_pivot[0], axis=0)

# Convert for Plotly compatibility
cohort_retention.index = cohort_retention.index.astype(str)
cohort_retention.columns = cohort_retention.columns.astype(str)

fig = px.imshow(
    cohort_retention,
    text_auto=True,
    aspect="auto",
    title="Retention Heatmap"
)

st.plotly_chart(fig, use_container_width=True)

# =============================
# FOOTER
# =============================
st.markdown("---")

st.markdown("""
### 💡 Key Insights

- Significant drop observed from View → Cart stage
- Cart → Purchase conversion is relatively stronger
- Certain categories dominate engagement
- Peak activity observed during specific hours
- Retention drops after initial interaction → opportunity for improvement
""")