from __future__ import annotations

import pandas as pd
import streamlit as st

from src.application import CsvLoadOptions, draft_replies, get_insights, infer_csv_options, load_reviews_from_csv, load_reviews_from_paste
from src.respond import response_style_preview
from src.types import BrandVoice


def run() -> None:
    st.set_page_config(page_title="demo2 — Reviews Analyzer", layout="wide")

    st.title("demo2 — Google Reviews Analyzer + Brand-Voice Replies")
    st.caption("Upload reviews, see what’s working/not, and draft safe, consistent responses.")

    with st.sidebar:
        st.subheader("Brand voice")
        business_name = st.text_input("Business name", value="Your Business")
        signoff_name = st.text_input("Sign-off name", value="Team")
        tone = st.selectbox(
            "Tone",
            ["Warm & professional", "Friendly & casual", "Premium & polished", "Short & direct"],
            index=0,
        )
        values = st.text_area("Values (1 line)", value="Helpful, respectful, solution-oriented", height=60)
        do_not_say = st.text_area(
            "Do-not-say (guardrail)",
            value="Don’t mention refunds publicly unless you intend to offer one.",
            height=60,
        )
        contact_line = st.text_input(
            "Contact line (optional, for negative/risk replies)",
            value="",
            placeholder="e.g. Call us at (555) 123-4567 or email support@yourbiz.com",
        )
        voice = BrandVoice(
            business_name=business_name,
            signoff_name=signoff_name,
            tone=tone,
            values=values,
            do_not_say=do_not_say,
            contact_line=contact_line,
        )
        with st.expander("Voice preview"):
            st.code(response_style_preview(voice))

    tab1, tab2, tab3 = st.tabs(["1) Load reviews", "2) Insights", "3) Reply drafts"])

    if "reviews" not in st.session_state:
        st.session_state["reviews"] = []
    reviews = st.session_state["reviews"]

    with tab1:
        st.subheader("Load reviews")
        source = st.radio("Source", ["Upload CSV", "Paste reviews"], horizontal=True)

        if source == "Upload CSV":
            up = st.file_uploader("Upload CSV", type=["csv"])
            if up is not None:
                df = pd.read_csv(up)
                st.write("Preview")
                st.dataframe(df.head(20), use_container_width=True)

                guess = infer_csv_options(df)
                c1, c2, c3, c4 = st.columns(4)
                with c1:
                    default_text = guess.get("text")
                    text_idx = list(df.columns).index(default_text) if default_text in df.columns else 0
                    text_col = st.selectbox("Text column", options=list(df.columns), index=text_idx)
                with c2:
                    default_rating = guess.get("rating")
                    rating_options = ["(none)"] + list(df.columns)
                    rating_idx = 0 if default_rating is None else (1 + list(df.columns).index(default_rating))
                    rating_col = st.selectbox("Rating column (optional)", options=rating_options, index=rating_idx)
                with c3:
                    default_date = guess.get("date")
                    date_options = ["(none)"] + list(df.columns)
                    date_idx = 0 if default_date is None else (1 + list(df.columns).index(default_date))
                    date_col = st.selectbox("Date column (optional)", options=date_options, index=date_idx)
                with c4:
                    default_author = guess.get("author")
                    author_options = ["(none)"] + list(df.columns)
                    author_idx = 0 if default_author is None else (1 + list(df.columns).index(default_author))
                    author_col = st.selectbox("Author column (optional)", options=author_options, index=author_idx)

                opts = CsvLoadOptions(
                    text_col=text_col,
                    rating_col=None if rating_col == "(none)" else rating_col,
                    date_col=None if date_col == "(none)" else date_col,
                    author_col=None if author_col == "(none)" else author_col,
                )
                reviews = load_reviews_from_csv(df, options=opts)
                st.session_state["reviews"] = reviews
                st.success(f"Loaded {len(reviews)} reviews.")
        else:
            pasted = st.text_area(
                "Paste reviews (one per line OR separate with blank lines)",
                height=220,
                placeholder="Great service and fast!\n\nWaited 45 minutes and nobody helped me.\n\nIt was ok, nothing special.",
            )
            reviews = load_reviews_from_paste(pasted)
            st.session_state["reviews"] = reviews
            if reviews:
                st.success(f"Loaded {len(reviews)} reviews from paste.")

    with tab2:
        st.subheader("Insights")
        if not reviews:
            st.info("Load reviews first.")
        else:
            a = get_insights(reviews)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total reviews", a.total)
            c2.metric("Positive", a.counts["positive"])
            c3.metric("Neutral", a.counts["neutral"])
            c4.metric("Negative", a.counts["negative"])

            if a.avg_rating is not None:
                st.metric("Average rating", f"{a.avg_rating:.2f}")

            cL, cR = st.columns(2)
            with cL:
                st.markdown("**What’s going well (themes)**")
                st.write(a.top_positive_themes or "Not enough data yet.")
                st.markdown("**Positive highlights (example reviews)**")
                for t in a.highlights_positive:
                    st.write(f"- {t}")
            with cR:
                st.markdown("**What’s not going well (themes)**")
                st.write(a.top_negative_themes or "Not enough data yet.")
                st.markdown("**Negative highlights (example reviews)**")
                for t in a.highlights_negative:
                    st.write(f"- {t}")

            st.markdown("**Reputation risk flags**")
            if a.risk_counts:
                st.json(a.risk_counts)
            else:
                st.write("No obvious risk keywords detected.")

            st.markdown("**Restaurant themes (keyword buckets)**")
            if a.theme_counts:
                st.json(a.theme_counts)
            else:
                st.write("No theme keywords detected yet.")

    with tab3:
        st.subheader("Reply drafts")
        if not reviews:
            st.info("Load reviews first.")
        else:
            n_reviews = len(reviews)
            if n_reviews <= 1:
                max_show = n_reviews
            else:
                max_show = st.slider(
                    "How many reviews to draft replies for",
                    min_value=1,
                    max_value=min(50, n_reviews),
                    value=min(15, n_reviews),
                )
            drafts = draft_replies(reviews, voice=voice, limit=max_show)
            for idx, (r, d) in enumerate(zip(reviews[:max_show], drafts), start=1):
                with st.expander(f"{idx}. {d.sentiment.upper()} — Draft reply", expanded=False):
                    st.markdown("**Review**")
                    st.write(r.text)
                    st.markdown("**Draft response**")
                    st.code(d.response)
                    if d.risk_flags:
                        st.markdown("**Risk flags**")
                        st.write(d.risk_flags)
                    with st.expander("Internal notes (not for posting)"):
                        for n in d.notes:
                            st.write(f"- {n}")

