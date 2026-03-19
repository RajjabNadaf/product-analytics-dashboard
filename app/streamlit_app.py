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

# -----------------------------
# SIDEBAR
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
# FUNNEL
# =============================
st.subheader("🔻 Conversion Funnel")

funnel = df.groupby('event_type')['user_id'].nunique().reset_index()

# Order stages manually
order = ['view', 'cart', 'purchase']
funnel['event_type'] = pd.Categorical(funnel['event_type'], categories=order, ordered=True)
funnel = funnel.sort_values('event_type')

fig = px.funnel(
    funnel,
    x='user_id',
    y='event_type',
    title="User Funnel"
)

st.plotly_chart(fig, use_container_width=True)

# =============================
# CONVERSION METRICS
# =============================
view = funnel.loc[funnel['event_type']=='view', 'user_id'].values[0]
cart = funnel.loc[funnel['event_type']=='cart', 'user_id'].values[0]
purchase = funnel.loc[funnel['event_type']=='purchase', 'user_id'].values[0]

col1, col2 = st.columns(2)

col1.metric("View → Cart", f"{(cart/view):.2%}")
col2.metric("Cart → Purchase", f"{(purchase/cart):.2%}")

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

# =============================
# FOOTER
# =============================
st.markdown("---")

st.markdown("""
### 💡 Insights
- Funnel shows strong drop from View → Cart
- High activity during peak hours
- Top categories dominate user engagement
""")