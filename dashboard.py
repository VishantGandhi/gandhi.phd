import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from collections import Counter
import os
import sys
import urllib.parse

from litrev.search import aggregate_search
from litrev.perspectives import list_perspectives, apply_perspectives, get_perspective
from litrev.report import detect_themes, generate_review_report, RESEARCH_THEMES
from litrev.export import get_bibtex_string, get_ris_string
from litrev.open_access import resolve_open_access

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from litrev.job_scraper import (
    update_job_db,
    load_jobs,
    save_jobs,
    update_job_status,
    update_job_pipeline,
    analyze_skills_and_gaps,
    score_job,
)
from litrev.resume_tailor import generate_pdf_resume
from litrev.cover_letter import generate_cover_letter

st.set_page_config(page_title="Vishant's Career & Research Portal", page_icon="🔬", layout="wide")

# ─── Authentication ───────────────────────────────────────────────────────────

def check_password():
    def password_entered():
        if st.session_state["username"] == "vgandhi" and st.session_state["password"] == "zengler2026":
            st.session_state["password_correct"] = True
            del st.session_state["password"]
        else:
            st.session_state["password_correct"] = False

    if "password_correct" not in st.session_state:
        st.title("🔒 Portal Login")
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=password_entered)
        return False
    elif not st.session_state["password_correct"]:
        st.title("🔒 Portal Login")
        st.text_input("Username", key="username")
        st.text_input("Password", type="password", key="password")
        st.button("Login", on_click=password_entered)
        st.error("😕 User not known or password incorrect")
        return False
    else:
        return True

if not check_password():
    st.stop()

# ─── Navigation ───────────────────────────────────────────────────────────────

st.sidebar.title("Navigation")
app_mode = st.sidebar.radio("Go to", ["Literature Review", "Job Finder & Pipeline"])
st.sidebar.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS FOR LITERATURE REVIEW
# ═══════════════════════════════════════════════════════════════════════════════

PERSPECTIVE_OPTIONS = {
    "shotgun_metagenomics": "🔬 WGS Metagenomics ('16S is for the weak')",
    "multi_omics": "🧬 Multi-Omics (Metatranscriptomics, MetaRibo-Seq, Metabolomics)",
    "synthetic_communities": "🧫 Synthetic Communities & SynComs (UroCom-style)",
    "urobiome": "💧 Urobiome & Urinary Tract Ecology",
    "anaerobic_microbiology": "🧪 Strict Anaerobic Culturomics",
    "clinical_translational": "🏥 Clinical Cohorts & Therapeutics",
    "mechanistic": "⚙️ Mechanistic & Causal Assays",
    "vaginal_microbiome": "🌸 Vaginal Microbiome & CSTs",
    "metabolic_modeling": "💻 Metabolic Modeling & GEMs",
}

def detect_methodology_and_model(paper):
    text = (paper.title + " " + paper.abstract).lower()
    
    methods = []
    if any(k in text for k in ["shotgun", "whole genome", "wgs", "metagenomic sequencing"]):
        methods.append("WGS Metagenomics")
    if any(k in text for k in ["16s rrna", "16s amplicon", "v3-v4", "v4 region"]):
        methods.append("16S Amplicon")
    if any(k in text for k in ["metatranscriptom", "rna-seq", "transcriptomics"]):
        methods.append("Metatranscriptomics")
    if any(k in text for k in ["ribo-seq", "ribosome profiling", "translatomics", "metaribo"]):
        methods.append("MetaRibo-Seq")
    if any(k in text for k in ["metabolom", "lc-ms", "mass spec", "nmr"]):
        methods.append("Metabolomics")
    if any(k in text for k in ["anaerobic", "culturomics", "isolation", "cultivation"]):
        methods.append("Anaerobic Cultivation")
    if not methods:
        methods.append("Observational / Bioinformatic")

    models = []
    if any(k in text for k in ["patient", "cohort", "clinical", "human", "women", "men", "donor"]):
        models.append("Human Clinical Cohort")
    if any(k in text for k in ["syncom", "synthetic community", "defined community", "consortium", "co-culture", "in vitro"]):
        models.append("In Vitro Defined Community")
    if any(k in text for k in ["mouse", "mice", "murine", "rat", "gnotobiotic"]):
        models.append("Murine / In Vivo Model")
    if any(k in text for k in ["computational", "in silico", "flux balance", "metabolic model"]):
        models.append("In Silico / Metabolic Model")
    if not models:
        models.append("General Biological System")

    return ", ".join(methods), ", ".join(models)

# ═══════════════════════════════════════════════════════════════════════════════
# 1. LITERATURE REVIEW (ZENGLER LAB SUITE)
# ═══════════════════════════════════════════════════════════════════════════════

if app_mode == "Literature Review":
    st.title("📚 LitRev: Zengler Lab Literature Intelligence Platform")
    st.caption("Deep biomedical literature synthesis across PubMed, OpenAlex, and Semantic Scholar with customized methodological perspectives, open-access resolution, and BibTeX/Zotero exports.")

    # ── Sidebar Search & Perspective Settings ──
    st.sidebar.header("🔍 Search Parameters")
    lit_query = st.sidebar.text_input("Query / Biological System:", value="colonization resistance urinary microbiome synthetic community")
    
    col_s1, col_s2 = st.sidebar.columns(2)
    with col_s1:
        lit_max_results = st.slider("Max Papers", 10, 60, 30, step=5)
    with col_s2:
        lit_years = st.slider("Past Years", 1, 10, 5)

    st.sidebar.markdown("---")
    st.sidebar.header("🔬 Zengler Lab Perspectives")
    st.sidebar.caption("Weight and filter papers based on lab methodologies:")

    default_perspectives = ["shotgun_metagenomics", "urobiome", "synthetic_communities"]
    selected_perspective_keys = st.sidebar.multiselect(
        "Active Perspectives:",
        options=list(PERSPECTIVE_OPTIONS.keys()),
        default=default_perspectives,
        format_func=lambda k: PERSPECTIVE_OPTIONS[k]
    )

    run_search = st.sidebar.button("🚀 Run Deep Literature Search", type="primary", use_container_width=True)

    if run_search:
        with st.spinner("Querying PubMed, OpenAlex, Semantic Scholar & evaluating perspectives..."):
            try:
                results = aggregate_search(lit_query, max_results=lit_max_results, years=lit_years)
                if selected_perspective_keys:
                    apply_perspectives(results.papers, selected_perspective_keys)
                    results.papers.sort(key=lambda p: getattr(p, "perspective_score", 0.0), reverse=True)
                
                # Cache in session state
                st.session_state["lit_results"] = results
                st.session_state["lit_query"] = lit_query
                st.session_state["lit_perspectives"] = selected_perspective_keys
                st.session_state["lit_report"] = None  # reset report on new search
                st.success(f"Found {len(results.papers)} papers!")
            except Exception as e:
                st.error(f"Search failed: {e}")

    # If results exist in session state
    if "lit_results" in st.session_state and st.session_state["lit_results"]:
        results = st.session_state["lit_results"]
        papers = results.papers

        # Re-apply perspectives if user modified selection after search
        if selected_perspective_keys != st.session_state.get("lit_perspectives"):
            apply_perspectives(papers, selected_perspective_keys)
            papers.sort(key=lambda p: getattr(p, "perspective_score", 0.0), reverse=True)
            st.session_state["lit_perspectives"] = selected_perspective_keys

        # ── Top Metrics Bar ──
        m_c1, m_c2, m_c3, m_c4 = st.columns(4)
        high_fit_count = sum(1 for p in papers if getattr(p, "perspective_score", 0.0) >= 40)
        review_count = sum(1 for p in papers if getattr(p, "is_review", False))
        with m_c1:
            st.metric("Total Papers Found", len(papers))
        with m_c2:
            st.metric("🎯 High Lab Fit (≥40)", high_fit_count)
        with m_c3:
            st.metric("🔬 Primary Research", len(papers) - review_count)
        with m_c4:
            st.metric("📖 Reviews / Overviews", review_count)

        # ── Global Action Bar: BibTeX, RIS, Synthesis Report ──
        st.markdown("---")
        act_c1, act_c2, act_c3 = st.columns([1.5, 1.2, 1.2])
        
        with act_c1:
            if st.button("📝 Generate Full Review Synthesis Report", type="primary", use_container_width=True):
                with st.spinner("Synthesizing themes, consensus findings, and methodology matrices..."):
                    report_md = generate_review_report(results, perspectives=selected_perspective_keys)
                    st.session_state["lit_report"] = report_md
                    st.success("Executive synthesis report ready in the '📑 Synthesis Report' tab!")

        with act_c2:
            bibtex_content = get_bibtex_string(papers)
            st.download_button(
                label="⬇️ Export BibTeX (.bib)",
                data=bibtex_content,
                file_name=f"litrev_{datetime.now().strftime('%Y%m%d')}.bib",
                mime="text/plain",
                use_container_width=True
            )

        with act_c3:
            ris_content = get_ris_string(papers)
            st.download_button(
                label="⬇️ Export Zotero / RIS (.ris)",
                data=ris_content,
                file_name=f"litrev_{datetime.now().strftime('%Y%m%d')}.ris",
                mime="application/x-research-info-systems",
                use_container_width=True
            )

        # ── 4 Main Tabs: Curated Papers, Visual Analytics, Comparison Matrix, Report ──
        tab_papers, tab_viz, tab_compare, tab_report = st.tabs([
            f"📄 Curated Papers ({len(papers)})",
            "📊 Methodology & Analytics Visualizer",
            "⚖️ Paper Comparison Matrix",
            "📑 Executive Synthesis Report",
        ])

        # ── TAB 1: Curated Papers List ──
        with tab_papers:
            # Sub-filters within results
            f_col1, f_col2, f_col3 = st.columns([2, 1.5, 1.5])
            with f_col1:
                search_filter = st.text_input("Filter within results (author, title, keyword):", "")
            with f_col2:
                sort_lit = st.selectbox("Sort papers by:", [
                    "🎯 Lab Perspective Fit (High to Low)",
                    "📅 Year (Newest First)",
                    "⭐ Citations (High to Low)",
                    "🔤 Title (A to Z)"
                ])
            with f_col3:
                theme_dict = detect_themes(papers)
                theme_filter = st.selectbox("Filter by Theme:", ["All Themes"] + list(theme_dict.keys()))

            displayed_papers = papers
            if theme_filter != "All Themes":
                displayed_papers = theme_dict.get(theme_filter, [])

            if search_filter:
                kw = search_filter.lower().strip()
                displayed_papers = [
                    p for p in displayed_papers
                    if kw in p.title.lower()
                    or kw in p.display_authors.lower()
                    or kw in p.journal.lower()
                    or kw in p.searchable_text
                ]

            if sort_lit == "🎯 Lab Perspective Fit (High to Low)":
                displayed_papers.sort(key=lambda p: getattr(p, "perspective_score", 0.0), reverse=True)
            elif sort_lit == "📅 Year (Newest First)":
                displayed_papers.sort(key=lambda p: getattr(p, "year", 0), reverse=True)
            elif sort_lit == "⭐ Citations (High to Low)":
                displayed_papers.sort(key=lambda p: getattr(p, "citation_count", 0), reverse=True)
            elif sort_lit == "🔤 Title (A to Z)":
                displayed_papers.sort(key=lambda p: p.title.lower())

            st.caption(f"Showing {len(displayed_papers)} papers:")

            for idx, p in enumerate(displayed_papers):
                with st.container():
                    st.markdown("---")
                    p_score = getattr(p, "perspective_score", 0.0)
                    
                    # Score badge
                    if p_score >= 50:
                        score_badge = f"<span style='background-color:#dcfce7; color:#166534; padding:3px 8px; border-radius:12px; font-weight:bold;'>🟢 {p_score:.0f} Lab Fit</span>"
                    elif p_score >= 20:
                        score_badge = f"<span style='background-color:#fef9c3; color:#854d0e; padding:3px 8px; border-radius:12px; font-weight:bold;'>🟡 {p_score:.0f} Lab Fit</span>"
                    else:
                        score_badge = f"<span style='background-color:#f1f5f9; color:#475569; padding:3px 8px; border-radius:12px;'>⚪ {p_score:.0f} Score</span>"

                    type_tag = "📖 Review" if p.is_review else "🔬 Research Article"
                    
                    st.markdown(f"#### {p.title} &nbsp; {score_badge}", unsafe_allow_html=True)
                    st.markdown(f"**Authors:** {p.display_authors} &nbsp;•&nbsp; 🏛️ *{p.journal}* ({p.year}) &nbsp;•&nbsp; ⭐ **{p.citation_count} Citations** &nbsp;•&nbsp; `{type_tag}`")

                    # Boost tags & Themes
                    flags = getattr(p, "perspective_flags", [])
                    boost_tags = " ".join([f"<span style='background-color:#dbeafe; color:#1e40af; font-size:11px; padding:2px 6px; border-radius:6px; margin-right:4px;'>{f.replace('boost:', '✓ ')}</span>" for f in flags if 'boost:' in f][:5])
                    theme_tags = " ".join([f"<span style='background-color:#f3e8ff; color:#6b21a8; font-size:11px; padding:2px 6px; border-radius:6px; margin-right:4px;'>🏷️ {t}</span>" for t in getattr(p, "matched_themes", [])[:3]])
                    
                    if boost_tags or theme_tags:
                        st.markdown(f"<div style='margin-bottom:6px;'>{boost_tags} {theme_tags}</div>", unsafe_allow_html=True)

                    # Abstract
                    if p.abstract:
                        with st.expander("📄 View Abstract & Study Summary"):
                            st.write(p.abstract)

                    # Action Buttons: Open Access PDF, UCSD Full Text, DOI
                    oa_info = resolve_open_access(p.doi, p.pmid)
                    
                    b1, b2, b3, b4 = st.columns([1.5, 1.5, 1.2, 1.2])
                    with b1:
                        if oa_info.get("pdf_url"):
                            st.link_button("🔓 Download Free OA PDF", oa_info["pdf_url"], use_container_width=True)
                        elif oa_info.get("landing_url"):
                            st.link_button("🔓 Open Access Page", oa_info["landing_url"], use_container_width=True)
                        else:
                            st.caption("🔒 Paywalled (Use UCSD Proxy)")

                    with b2:
                        st.link_button("🏛️ UCSD Library Full Text", p.ucsd_link, use_container_width=True)

                    with b3:
                        if p.link:
                            st.link_button("🔗 Publisher / DOI", p.link, use_container_width=True)

                    with b4:
                        with st.popover("📋 Citation"):
                            st.code(get_bibtex_string([p]), language="latex")

        # ── TAB 2: Visual Analytics ──
        with tab_viz:
            st.subheader("📊 Research Trends & Methodological Shifts")
            
            # 1. Methodology Evolution Over Time
            records = []
            for p in papers:
                method, model = detect_methodology_and_model(p)
                primary_method = method.split(",")[0]
                records.append({
                    "Year": p.year if p.year else 2020,
                    "Methodology": primary_method,
                    "Journal": p.journal if p.journal else "Other",
                    "Citations": p.citation_count,
                    "Count": 1
                })
            df_analytics = pd.DataFrame(records)

            viz_col1, viz_col2 = st.columns(2)
            with viz_col1:
                if not df_analytics.empty:
                    df_year = df_analytics.groupby(["Year", "Methodology"]).size().reset_index(name="Papers")
                    fig_method = px.bar(
                        df_year,
                        x="Year",
                        y="Papers",
                        color="Methodology",
                        title="📈 Methodological Shifts Over Time",
                        barmode="stack",
                        color_discrete_sequence=px.colors.qualitative.Prism
                    )
                    st.plotly_chart(fig_method, use_container_width=True)

            with viz_col2:
                # Top Journals
                if not df_analytics.empty:
                    top_journals = df_analytics["Journal"].value_counts().head(8).reset_index()
                    top_journals.columns = ["Journal", "Papers"]
                    fig_jour = px.bar(
                        top_journals,
                        x="Papers",
                        y="Journal",
                        orientation="h",
                        title="🏛️ Top Publishing Venues",
                        color="Papers",
                        color_continuous_scale="Blues"
                    )
                    fig_jour.update_layout(yaxis=dict(autorange="reversed"))
                    st.plotly_chart(fig_jour, use_container_width=True)

            # Theme distribution pie chart
            all_themes = []
            for p in papers:
                all_themes.extend(getattr(p, "matched_themes", []))
            if all_themes:
                theme_counts = pd.DataFrame(Counter(all_themes).items(), columns=["Theme", "Count"]).sort_values("Count", ascending=False).head(8)
                fig_theme = px.pie(
                    theme_counts,
                    values="Count",
                    names="Theme",
                    title="🏷️ Conceptual Themes Distribution",
                    hole=0.4,
                    color_discrete_sequence=px.colors.qualitative.Safe
                )
                st.plotly_chart(fig_theme, use_container_width=True)

        # ── TAB 3: Interactive Paper Comparison Matrix ──
        with tab_compare:
            st.subheader("⚖️ Side-by-Side Study Comparison Matrix")
            st.markdown("Select 2 to 4 studies to compare their methodology, experimental models, perspective alignment, and key conclusions.")

            paper_titles = [f"{p.title[:65]}... ({p.year})" for p in papers]
            default_selection = paper_titles[:2] if len(paper_titles) >= 2 else paper_titles
            
            selected_titles = st.multiselect(
                "Choose papers to compare:",
                options=paper_titles,
                default=default_selection,
                max_selections=4
            )

            if len(selected_titles) < 2:
                st.info("Please select at least 2 papers to compare.")
            else:
                compared_papers = [p for i, p in enumerate(papers) if paper_titles[i] in selected_titles]
                
                comp_data = []
                for p in compared_papers:
                    methods, models = detect_methodology_and_model(p)
                    comp_data.append({
                        "Metric": "Title",
                        p.display_authors: p.title
                    })

                # Transposed comparison table
                matrix_rows = [
                    ("Year", lambda p: str(p.year)),
                    ("Journal", lambda p: p.journal),
                    ("Citations", lambda p: str(p.citation_count)),
                    ("Type", lambda p: "Review" if p.is_review else "Research Article"),
                    ("Lab Fit Score", lambda p: f"{getattr(p, 'perspective_score', 0):.0f}"),
                    ("Methodology / Omics", lambda p: detect_methodology_and_model(p)[0]),
                    ("Experimental Model", lambda p: detect_methodology_and_model(p)[1]),
                    ("Matched Themes", lambda p: ", ".join(getattr(p, "matched_themes", [])[:3])),
                    ("Key Abstract Takeaway", lambda p: (p.abstract[:220] + "...") if p.abstract else "No abstract provided."),
                ]

                matrix_df = pd.DataFrame({
                    f"{p.display_authors} ({p.year})": [func(p) for _, func in matrix_rows]
                    for p in compared_papers
                }, index=[label for label, _ in matrix_rows])

                st.table(matrix_df)

        # ── TAB 4: Executive Synthesis Report ──
        with tab_report:
            st.subheader("📑 Automated Review Synthesis Report")
            
            report_text = st.session_state.get("lit_report")
            if not report_text:
                st.info("👆 Click **'Generate Full Review Synthesis Report'** in the top action bar to compile your structured review draft.")
            else:
                rep_c1, rep_c2 = st.columns([3, 1])
                with rep_c2:
                    st.download_button(
                        label="⬇️ Download Full Review (.md)",
                        data=report_text,
                        file_name=f"LitRev_Synthesis_{datetime.now().strftime('%Y%m%d')}.md",
                        mime="text/markdown",
                        use_container_width=True
                    )
                st.markdown(report_text)

    else:
        st.info("👈 Enter your query in the sidebar and click **'Run Deep Literature Search'** to begin.")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. JOB FINDER & APPLICATION PIPELINE
# ═══════════════════════════════════════════════════════════════════════════════

elif app_mode == "Job Finder & Pipeline":
    st.title("💼 Bioengineering & Venture Capital Career Engine")
    st.caption("Custom multi-source search engine, skill gap analysis, alumni networking, 1-click tailored application documents, and full pipeline tracker.")

    all_jobs = load_jobs()

    # ── Sidebar Controls ──
    st.sidebar.header("🔍 Filters & Search")
    all_types = sorted(set(j.job_type for j in all_jobs)) if all_jobs else ["Science", "Venture"]
    filter_type = st.sidebar.multiselect("Category", all_types, default=all_types)
    filter_location = st.sidebar.text_input("📍 Location Filter (e.g. San Diego, Bay Area, NYC)", "")
    filter_search = st.sidebar.text_input("🔎 Keyword (e.g. microbiome, diligence, equity)", "")
    filter_min_score = st.sidebar.slider("🎯 Min Match Score", 0, 100, 40)
    filter_disclosed_only = st.sidebar.checkbox("💵 Only show roles with disclosed salary", value=False)

    st.sidebar.markdown("---")
    st.sidebar.header("↕️ Sorting")
    sort_by = st.sidebar.selectbox("Sort feed by", [
        "🎯 Match Score (High to Low)",
        "💰 Compensation (High to Low)",
        "📅 Date Posted (Newest First)",
        "📍 Location (A to Z)",
        "🏢 Company Name (A to Z)",
        "🏷️ Job Title (A to Z)"
    ])

    st.sidebar.markdown("---")
    st.sidebar.caption("🌐 **Integrated Sources:** LinkedIn Live Engine, DOCjobs, Greenhouse (Ginkgo, Flagship, a16z, Twist, Beam, Seres, Blueprint)")

    # ── Top Action & Metrics Bar ──
    col_act, col_m1, col_m2, col_m3, col_m4 = st.columns([2, 1.2, 1.2, 1.2, 1.2])
    with col_act:
        if st.button("🚀 Refresh / Fetch New Opportunities", type="primary", use_container_width=True):
            with st.spinner("Searching LinkedIn, DOCjobs, and Greenhouse across open roles..."):
                jobs = update_job_db()
                st.success(f"✅ Synced! Found {len(jobs)} active opportunities.")
                st.rerun()

    pipeline_counts = {
        "New": sum(1 for j in all_jobs if j.status == "New"),
        "Starred": sum(1 for j in all_jobs if j.status == "Starred"),
        "Applied": sum(1 for j in all_jobs if j.status in ["Applied", "Screening", "Interview"]),
        "Offer": sum(1 for j in all_jobs if j.status == "Offer"),
    }

    with col_m1:
        st.metric("New Roles", pipeline_counts["New"])
    with col_m2:
        st.metric("⭐ Starred", pipeline_counts["Starred"])
    with col_m3:
        st.metric("⏳ In Pipeline", pipeline_counts["Applied"])
    with col_m4:
        st.metric("🏆 Offers", pipeline_counts["Offer"])

    if not all_jobs:
        st.info("👆 Click **Refresh / Fetch New Opportunities** to populate your live database.")
        st.stop()

    # ── Master Tabs ──
    tab_feed, tab_starred, tab_pipeline, tab_archive = st.tabs([
        f"📋 Opportunity Feed ({pipeline_counts['New']})",
        f"⭐ Starred ({pipeline_counts['Starred']})",
        f"📊 Application Pipeline ({pipeline_counts['Applied'] + pipeline_counts['Offer']})",
        f"📁 Archive ({sum(1 for j in all_jobs if j.status == 'Archived')})",
    ])

    # ── Filter Logic for Feed ──
    def apply_filters_and_sort(job_list):
        filtered = job_list
        if filter_type:
            filtered = [j for j in filtered if j.job_type in filter_type]
        if filter_location:
            loc_term = filter_location.lower().strip()
            filtered = [j for j in filtered if loc_term in j.location.lower()]
        if filter_search:
            kw = filter_search.lower().strip()
            filtered = [
                j for j in filtered
                if kw in j.title.lower()
                or kw in j.company.lower()
                or kw in j.location.lower()
                or kw in j.role_description.lower()
                or kw in j.qualifications.lower()
            ]
        filtered = [j for j in filtered if j.match_score >= filter_min_score]
        if filter_disclosed_only:
            filtered = [j for j in filtered if j.compensation != "Undisclosed by Employer"]

        if sort_by == "🎯 Match Score (High to Low)":
            filtered.sort(key=lambda x: x.match_score, reverse=True)
        elif sort_by == "💰 Compensation (High to Low)":
            filtered.sort(key=lambda x: x.comp_numeric, reverse=True)
        elif sort_by == "📅 Date Posted (Newest First)":
            filtered.sort(key=lambda x: str(x.date_posted or ""), reverse=True)
        elif sort_by == "📍 Location (A to Z)":
            filtered.sort(key=lambda x: x.location.lower())
        elif sort_by == "🏢 Company Name (A to Z)":
            filtered.sort(key=lambda x: x.company.lower())
        elif sort_by == "🏷️ Job Title (A to Z)":
            filtered.sort(key=lambda x: x.title.lower())
        return filtered

    # ── Job Card Renderer ──
    def render_job_card(job, tab_key):
        with st.container():
            st.markdown("---")
            
            # Header Row
            c_info, c_action = st.columns([3.8, 2.2])
            
            with c_info:
                # Match score badge
                if job.match_score >= 80:
                    badge_style = "background-color:#dcfce7; color:#166534;"
                    badge_icon = "🟢"
                elif job.match_score >= 60:
                    badge_style = "background-color:#fef9c3; color:#854d0e;"
                    badge_icon = "🟡"
                else:
                    badge_style = "background-color:#fee2e2; color:#991b1b;"
                    badge_icon = "🔴"
                
                score_html = f"<span style='{badge_style} padding:3px 8px; border-radius:12px; font-weight:bold;'>{badge_icon} {job.match_score}% Match</span>"
                st.markdown(f"### {job.title} &nbsp; {score_html}", unsafe_allow_html=True)
                
                comp_badge = f"<span style='color:#166534; font-weight:600;'>💰 {job.compensation}</span>" if job.compensation != "Undisclosed by Employer" else "<span style='color:#64748b;'>💰 Undisclosed by Employer</span>"
                st.markdown(f"**🏢 {job.company}** &nbsp;•&nbsp; 📍 **{job.location}** &nbsp;•&nbsp; {comp_badge} &nbsp;•&nbsp; 📅 **{job.date_posted or 'Recent'}** &nbsp;•&nbsp; 🏷️ `{job.job_type}`", unsafe_allow_html=True)

            with c_action:
                b_col1, b_col2 = st.columns(2)
                with b_col1:
                    st.link_button("🔗 Apply on Source", job.link, use_container_width=True)
                with b_col2:
                    stage_options = ["New", "Starred", "Applied", "Screening", "Interview", "Offer", "Archived"]
                    current_idx = stage_options.index(job.status) if job.status in stage_options else 0
                    new_stage = st.selectbox(
                        "Move Stage:",
                        stage_options,
                        index=current_idx,
                        key=f"stage_sel_{tab_key}_{job.id}",
                        label_visibility="collapsed"
                    )
                    if new_stage != job.status:
                        update_job_status(job.id, new_stage)
                        st.rerun()

            # ── 3-Column Structured Description ──
            col_co, col_ro, col_qu = st.columns(3)
            with col_co:
                st.markdown("**🏢 Who the Company Is:**")
                st.info(job.company_overview if job.company_overview else f"{job.company} is an active biotechnology / life sciences innovator.")
            with col_ro:
                st.markdown("**🎯 What the Position Is:**")
                st.warning(job.role_description if job.role_description else f"Key {job.title} role driving strategic project milestones.")
            with col_qu:
                st.markdown("**🎓 Qualifications Required:**")
                st.success(job.qualifications if job.qualifications else "Advanced degree (PhD/MS) in Bioengineering, Molecular Biology, Bioinformatics, or VC diligence.")

            # ── Skill Radar & Gap Analysis ──
            matched_skills, gap_skills = analyze_skills_and_gaps(job)
            
            radar_col1, radar_col2 = st.columns(2)
            with radar_col1:
                matched_badges = " ".join([f"<span style='background-color:#dbeafe; color:#1e40af; padding:2px 7px; border-radius:8px; font-size:12px; margin-right:4px; font-weight:600;'>✓ {s}</span>" for s in matched_skills])
                st.markdown(f"**🎯 Your Matched Strengths:** {matched_badges}", unsafe_allow_html=True)
            with radar_col2:
                gap_badges = " ".join([f"<span style='background-color:#ffedd5; color:#9a3412; padding:2px 7px; border-radius:8px; font-size:12px; margin-right:4px; font-weight:600;'>⚠️ {s}</span>" for s in gap_skills])
                st.markdown(f"**💡 Keywords to Emphasize:** {gap_badges}", unsafe_allow_html=True)

            # ── Warm Referral Finder ──
            encoded_company = urllib.parse.quote_plus(job.company)
            ucsd_link = f"https://www.linkedin.com/search/results/people/?keywords={encoded_company}%20UCSD"
            nucleate_link = f"https://www.linkedin.com/search/results/people/?keywords={encoded_company}%20Nucleate"
            general_li_link = f"https://www.linkedin.com/search/results/people/?keywords={encoded_company}"

            st.markdown(
                f"<div style='margin-top:6px; margin-bottom:8px; font-size:13px; color:#475569;'>"
                f"🤝 <b>Warm Referral Finder:</b> &nbsp; "
                f"<a href='{ucsd_link}' target='_blank' style='color:#0284c7; text-decoration:underline; font-weight:600; margin-right:12px;'>🎓 Search UCSD Alumni at {job.company}</a> "
                f"<a href='{nucleate_link}' target='_blank' style='color:#7c3aed; text-decoration:underline; font-weight:600; margin-right:12px;'>🧬 Search Nucleate Network</a> "
                f"<a href='{general_li_link}' target='_blank' style='color:#475569; text-decoration:underline;'>👥 All Employees</a>"
                f"</div>",
                unsafe_allow_html=True
            )

            # ── Tailored Resume & Cover Letter Actions ──
            doc_c1, doc_c2 = st.columns(2)
            with doc_c1:
                if st.button("✨ Tailor 1-Page Resume (PDF)", key=f"btn_res_{tab_key}_{job.id}", use_container_width=True):
                    with st.spinner("Generating tailored 1-page Word & PDF resume..."):
                        try:
                            pdf_path = generate_pdf_resume(job)
                            st.session_state[f"pdf_res_{job.id}"] = pdf_path
                        except Exception as e:
                            st.error(f"Error creating resume: {e}")

                if f"pdf_res_{job.id}" in st.session_state:
                    res_path = st.session_state[f"pdf_res_{job.id}"]
                    if os.path.exists(res_path):
                        with open(res_path, "rb") as f:
                            st.download_button(
                                label="⬇️ Download Tailored Resume (PDF)",
                                data=f,
                                file_name=os.path.basename(res_path),
                                mime="application/pdf",
                                key=f"down_res_{tab_key}_{job.id}",
                                use_container_width=True
                            )

            with doc_c2:
                if st.button("📝 Tailor Cover Letter (PDF)", key=f"btn_cl_{tab_key}_{job.id}", use_container_width=True):
                    with st.spinner(f"Drafting tailored cover letter for {job.company}..."):
                        try:
                            cl_path = generate_cover_letter(job)
                            st.session_state[f"pdf_cl_{job.id}"] = cl_path
                        except Exception as e:
                            st.error(f"Error creating cover letter: {e}")

                if f"pdf_cl_{job.id}" in st.session_state:
                    cl_path = st.session_state[f"pdf_cl_{job.id}"]
                    if os.path.exists(cl_path):
                        with open(cl_path, "rb") as f:
                            st.download_button(
                                label="⬇️ Download Cover Letter (PDF)",
                                data=f,
                                file_name=os.path.basename(cl_path),
                                mime="application/pdf",
                                key=f"down_cl_{tab_key}_{job.id}",
                                use_container_width=True
                            )

    # ── TAB 1: Opportunity Feed ──
    with tab_feed:
        feed_jobs = apply_filters_and_sort([j for j in all_jobs if j.status == "New"])
        if not feed_jobs:
            st.info("No new opportunities match your current filters.")
        else:
            st.caption(f"Showing {len(feed_jobs)} opportunities:")
            for j in feed_jobs:
                render_job_card(j, "feed")

    # ── TAB 2: Starred Roles ──
    with tab_starred:
        starred_jobs = apply_filters_and_sort([j for j in all_jobs if j.status == "Starred"])
        if not starred_jobs:
            st.info("You haven't starred any opportunities yet!")
        else:
            st.caption(f"Showing {len(starred_jobs)} starred roles:")
            for j in starred_jobs:
                render_job_card(j, "star")

    # ── TAB 3: Application Pipeline Kanban Board ──
    with tab_pipeline:
        st.subheader("📊 Active Application Kanban Tracker")
        st.markdown("Track applications through each hiring stage, log interview notes, record referral contacts, and access tailored documents.")

        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        
        stages = [
            ("Applied", "📝 Applied", col_p1),
            ("Screening", "📞 Recruiter Screen", col_p2),
            ("Interview", "🎯 Technical / On-site", col_p3),
            ("Offer", "🏆 Offer Received", col_p4),
        ]

        for stage_key, stage_title, col in stages:
            with col:
                st.markdown(f"#### {stage_title}")
                stage_jobs = [j for j in all_jobs if j.status == stage_key]
                st.caption(f"{len(stage_jobs)} roles")
                st.markdown("---")
                
                if not stage_jobs:
                    st.markdown("<div style='color:#94a3b8; font-size:13px; font-style:italic;'>No applications in this stage.</div>", unsafe_allow_html=True)
                
                for j in stage_jobs:
                    with st.expander(f"{j.company} — {j.title[:25]}...", expanded=True):
                        st.markdown(f"**{j.title}**")
                        st.markdown(f"📍 {j.location} | 💰 {j.compensation}")
                        
                        ref_val = st.text_input("🤝 Referral / Contact:", value=j.referral_contact, key=f"ref_{j.id}")
                        if ref_val != j.referral_contact:
                            update_job_pipeline(j.id, referral_contact=ref_val)

                        int_val = st.text_input("📅 Next Interview Date:", value=j.interview_date, key=f"int_{j.id}", placeholder="e.g. Sept 18, 2:00 PM PST")
                        if int_val != j.interview_date:
                            update_job_pipeline(j.id, interview_date=int_val)

                        notes_val = st.text_area("📝 Notes & Follow-ups:", value=j.application_notes, key=f"notes_{j.id}", placeholder="Log questions, recruiter feedback...")
                        if notes_val != j.application_notes:
                            update_job_pipeline(j.id, application_notes=notes_val)

                        st.markdown("**Move Stage:**")
                        next_opts = ["Applied", "Screening", "Interview", "Offer", "Archived"]
                        current_pos = next_opts.index(j.status) if j.status in next_opts else 0
                        chosen_stage = st.selectbox("Stage", next_opts, index=current_pos, key=f"pipe_move_{j.id}", label_visibility="collapsed")
                        if chosen_stage != j.status:
                            update_job_status(j.id, chosen_stage)
                            st.rerun()

                        st.markdown("---")
                        cl_c1, cl_c2 = st.columns(2)
                        with cl_c1:
                            if st.button("📄 Resume", key=f"p_res_{j.id}", use_container_width=True):
                                p_res = generate_pdf_resume(j)
                                st.session_state[f"p_dl_res_{j.id}"] = p_res
                            if f"p_dl_res_{j.id}" in st.session_state:
                                p_res_f = st.session_state[f"p_dl_res_{j.id}"]
                                if os.path.exists(p_res_f):
                                    with open(p_res_f, "rb") as f:
                                        st.download_button("⬇️ Resume PDF", f, file_name=os.path.basename(p_res_f), key=f"p_d1_{j.id}", use_container_width=True)

                        with cl_c2:
                            if st.button("✉️ Cover Letter", key=f"p_cl_{j.id}", use_container_width=True):
                                p_cl = generate_cover_letter(j)
                                st.session_state[f"p_dl_cl_{j.id}"] = p_cl
                            if f"p_dl_cl_{j.id}" in st.session_state:
                                p_cl_f = st.session_state[f"p_dl_cl_{j.id}"]
                                if os.path.exists(p_cl_f):
                                    with open(p_cl_f, "rb") as f:
                                        st.download_button("⬇️ Cover Letter PDF", f, file_name=os.path.basename(p_cl_f), key=f"p_d2_{j.id}", use_container_width=True)

    # ── TAB 4: Archive ──
    with tab_archive:
        archived_jobs = [j for j in all_jobs if j.status == "Archived"]
        if not archived_jobs:
            st.info("No archived applications.")
        else:
            st.caption(f"{len(archived_jobs)} archived roles:")
            for j in archived_jobs:
                render_job_card(j, "arch")
