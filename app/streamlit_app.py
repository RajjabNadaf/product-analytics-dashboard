# =========================================
# FINAL PRODUCT ANALYTICS DASHBOARD
# =========================================

import streamlit as st
import pandas as pd
import plotly.express as px


st.set_page_config(page_title="Product Analytics", layout="wide")

PRIMARY = "#4F46E5"

SECONDARY = "#D1DBE8"

# =========================================
# HELPERS
# =========================================
def format_num(x):
    if x >= 1_000_000:
        return f"{x/1_000_000:.1f}M"
    elif x >= 1_000:
        return f"{x/1_000:.0f}K"
    return str(int(x))

def style(fig, title):
    fig.update_layout(
        title=dict(
            text=title,
            x=0.01,
            font=dict(size=20, color="black")  # 🔥 title fixed
        ),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(
            family="Arial",
            size=13,
            color="black"  # 🔥 global font fix
        ),
        xaxis=dict(
            title_font=dict(size=14, color="black"),
            tickfont=dict(size=12, color="black"),
            showgrid=True,
            gridcolor="#E5E7EB"
        ),
        yaxis=dict(
            title_font=dict(size=14, color="black"),
            tickfont=dict(size=12, color="black"),
            showgrid=True,
            gridcolor="#E5E7EB"
        ),
        margin=dict(l=40, r=40, t=60, b=40)
    )
    return fig

# =========================================
# LOAD DATA (FIXED TIMEZONE)
# =========================================
@st.cache_data
def load_data():
    df = pd.read_csv("data/events_sample.csv")
    df['event_time'] = pd.to_datetime(df['event_time']).dt.tz_localize(None)
    df['price'] = df['price'].fillna(0)
    return df

df = load_data()

# =========================================
# SIDEBAR FILTERS
# =========================================
st.sidebar.title("Filters")

category = st.sidebar.selectbox(
    "Category",
    ["All"] + sorted(df['category_code'].dropna().unique())
)


# APPLY FILTERS
if category != "All":
    df = df[df['category_code'] == category]


# =========================================
# NAVIGATION
# =========================================
page = st.sidebar.radio(
    "Navigation",
    ["Overview", "Behavior", "Revenue", "Retention", "Segmentation"]
)

# =========================================
# BASE METRICS
# =========================================
funnel = df.groupby("event_type")['user_id'].nunique()

view = funnel.get("view", 1)
cart = funnel.get("cart", 0)
purchase = funnel.get("purchase", 0)

# =========================================
# OVERVIEW
# =========================================
if page == "Overview":

    st.title("Overview")

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Total Users", df['user_id'].nunique())
    col2.metric("Total Events", len(df))
    col3.metric("Total Revenue", f"${df['price'].sum():,.0f}")
    col4.metric("Conversion Rate", f"{purchase/view:.2%}")

    st.markdown("---")

    funnel_df = pd.DataFrame({
        "Stage": ["View", "Cart", "Purchase"],
        "Users": [view, cart, purchase]
    })

    fig = px.funnel(funnel_df, x="Users", y="Stage")
    fig = style(fig, "User Conversion Funnel")

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 💡 Insights")
    st.write(f"""
    - Only **{cart/view:.1%}** users move from view → cart
    - Only **{purchase/view:.1%}** users convert to purchase
    - Major drop happens at discovery stage
    """)

# =========================================
# BEHAVIOR
# =========================================
elif page == "Behavior":

    st.title("User Behavior")

    events = df['event_type'].value_counts().sort_values()

    fig = px.bar(
        x=events.values,
        y=events.index,
        orientation='h',
        text=[format_num(x) for x in events.values],
        labels={"x": "Number of Events", "y": "Event Type"},
        color_discrete_sequence=[PRIMARY]
    )

    fig.update_traces(textposition="outside")
    fig = style(fig, "Event Distribution (Descending)")

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 💡 Insights")
    st.write("""
    - Majority of interactions are product views
    - Significant drop from cart to purchase
    - Funnel leakage indicates UX or pricing friction
    """)

# =========================================
# REVENUE
# =========================================
elif page == "Revenue":

    st.title("Revenue Analysis")

    revenue = df.groupby("category_code")['price'].sum()

    revenue = revenue.sort_values().tail(10)

    fig = px.bar(
        x=revenue.values,
        y=revenue.index,
        orientation='h',
        text=[format_num(x) for x in revenue.values],
        labels={"x": "Revenue ($)", "y": "Product Category"},
        color_discrete_sequence=[PRIMARY]
    )

    fig.update_traces(textposition="outside")
    fig = style(fig, "Top Revenue Generating Categories")

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 💡 Insights")
    st.write("""
    - Revenue is highly concentrated in top categories
    - Indicates dependency on few product segments
    - Opportunity to diversify revenue streams
    """)

# =========================================
# RETENTION
# =========================================
elif page == "Retention":

    st.title("Retention Analysis")

    df['month'] = df['event_time'].dt.to_period("M")
    df['cohort'] = df.groupby("user_id")['month'].transform("min")
    df['cohort_index'] = (df['month'] - df['cohort']).apply(lambda x: x.n)

    df['cohort'] = df['cohort'].astype(str)

    cohort = df.groupby(['cohort', 'cohort_index'])['user_id'].nunique().reset_index()

    pivot = cohort.pivot_table(index='cohort', columns='cohort_index', values='user_id')
    retention = pivot.divide(pivot[0], axis=0)

    fig = px.imshow(
        retention,
        text_auto=".0%",
        color_continuous_scale=["#EEF2FF", "#4F46E5", "#1E1B4B"],
        labels={
            "x": "Months Since First Visit",
            "y": "User Cohort",
            "color": "Retention Rate"
        }
    )

    fig = style(fig, "Cohort Retention Matrix")

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 💡 Insights")
    st.write("""
    - Sharp drop in retention after first month
    - Weak long-term engagement
    - Strong need for re-engagement strategies
    """)

# =========================================
# SEGMENTATION
# =========================================
elif page == "Segmentation":

    st.title("User Segmentation")

    snapshot = df['event_time'].max()

    rfm = df.groupby('user_id').agg({
        'event_time': lambda x: (snapshot - x.max()).days,
        'event_type': 'count',
        'price': 'sum'
    }).reset_index()

    rfm.columns = ['user_id', 'recency', 'frequency', 'monetary']

    rfm['r'] = pd.qcut(rfm['recency'].rank(method='first'), 4, labels=[4,3,2,1])
    rfm['f'] = pd.qcut(rfm['frequency'].rank(method='first'), 4, labels=[1,2,3,4])
    rfm['m'] = pd.qcut(rfm['monetary'].rank(method='first'), 4, labels=[1,2,3,4])

    rfm['score'] = rfm[['r','f','m']].astype(str).sum(axis=1)

    def segment(x):
        if x >= "444":
            return "High Value"
        elif x >= "344":
            return "Loyal"
        elif x >= "244":
            return "Potential"
        else:
            return "At Risk"

    rfm['segment'] = rfm['score'].apply(segment)

    seg = rfm['segment'].value_counts().sort_values()

    fig = px.bar(
        x=seg.values,
        y=seg.index,
        orientation='h',
        text=[format_num(x) for x in seg.values],
        labels={"x": "Number of Users", "y": "User Segment"},
        color_discrete_sequence=[PRIMARY]
    )

    fig.update_traces(textposition="outside")
    fig = style(fig, "User Segmentation Distribution")

    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### 💡 Insights")
    st.write("""
    - Large proportion of users are at-risk
    - Small high-value user base
    - Focus should be on retention and upselling
    """)