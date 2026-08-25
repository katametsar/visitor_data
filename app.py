from pathlib import Path
import base64
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
from dash import Dash, dcc, html, Input, Output

# ============================================================
# 1. FAILID
# ============================================================
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "dashboard_data"
RAW_DIR = BASE_DIR / "data_raw"

SESSIONS_FILE = DATA_DIR / "sessions_dashboard.parquet"
EXHIBIT_DAILY_FILE = DATA_DIR / "exhibit_daily.parquet"
EXHIBIT_LANGUAGE_FILE = DATA_DIR / "exhibit_language_daily.parquet"
EXHIBIT_ACTION_FILE = DATA_DIR / "exhibit_action_daily.parquet"
CONTEXT_FILE = DATA_DIR / "daily_context_final.parquet"
TICKET_SALES_FILE = DATA_DIR / "ticket_sales_daily.parquet"
SCHOOL_HOLIDAYS_FILE = DATA_DIR / "school_holidays_daily.parquet"
WEATHER_FILE = DATA_DIR / "weather_daily.parquet"
MUSEUM_EVENTS_FILE = DATA_DIR / "museum_events_daily.parquet"
COORDINATES_FILE = RAW_DIR / "coordinates_fixed.csv"
DEVICE_FILE = RAW_DIR / "Device_id.xlsx"
MAP_FILE = RAW_DIR / "museum_map.png"

# ============================================================
# 2. EESTIKEELSED NIMED JA STIIL
# ============================================================
LABELS = {
    "date": "Kuupäev",
    "month_date": "Kuupäev",
    "week_date": "Nädal",
    "visits": "Digitaalseid sessioone",
    "digital_sessions": "Digitaalseid sessioone",
    "tickets_sold": "Müüdud pileteid",
    "usage_rate": "Digikasutuse määr (%)",
    "ticket_language": "Piletikeel",
    "language": "Piletikeel",
    "median_duration": "Mediaankestus (min)",
    "median_exhibits": "Mediaan eksponaate",
    "median_events": "Mediaan tegevusi",
    "mean_events": "Keskmine tegevuste arv",
    "duration_minutes": "Digikasutuse kestus (min)",
    "hour": "Kell",
    "weekday": "Nädalapäev",
    "value": "Väärtus",
    "temperature": "Keskmine temperatuur (°C)",
    "temp_mean_c": "Keskmine temperatuur (°C)",
    "rain_mean_mm": "Keskmine sademete hulk (mm)",
    "event_type": "Sündmuse tüüp",
    "sessions": "Digitaalseid sessioone",
    "period": "Periood",
}

WEEKDAY_ORDER = ["E", "T", "K", "N", "R", "L", "P"]

CARD_STYLE = {
    "background": "white",
    "border": "1px solid #e7e9ee",
    "borderRadius": "16px",
    "padding": "20px",
    "boxShadow": "0 2px 10px rgba(16,24,40,0.04)",
}

# ============================================================
# 3. ABIFUNKTSIOONID
# ============================================================
def read_optional(path):
    return pd.read_parquet(path) if path.exists() else pd.DataFrame()


def ensure_date(df, col="date"):
    df = df.copy()
    if not df.empty and col in df.columns:
        df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def filter_dates(df, start_date=None, end_date=None):
    if df.empty or "date" not in df.columns:
        return df.copy()
    out = df.copy()
    if start_date:
        start = pd.to_datetime(start_date, errors="coerce")
        if pd.notna(start):
            out = out[out["date"] >= start]
    if end_date:
        end = pd.to_datetime(end_date, errors="coerce")
        if pd.notna(end):
            out = out[out["date"] <= end]
    return out.copy()


def fmt_int(x):
    return "–" if pd.isna(x) else f"{int(round(x)):,}".replace(",", " ")


def fmt_num(x, digits=1):
    return "–" if pd.isna(x) else f"{x:.{digits}f}".replace(".", ",")


def style_fig(fig, title=None):
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="white",
        plot_bgcolor="white",
        font=dict(family="Arial, sans-serif", color="#344054"),
        margin=dict(l=55, r=30, t=68, b=55),
        hoverlabel=dict(bgcolor="white", font_size=13),
        legend_title_text="",
    )
    if title:
        fig.update_layout(title=dict(text=title, x=0.02, xanchor="left", font=dict(size=18)))
    fig.update_xaxes(showgrid=False, linecolor="#e4e7ec", zeroline=False)
    fig.update_yaxes(gridcolor="#f0f2f5", linecolor="#e4e7ec", zeroline=False)
    return fig


def empty_fig(message):
    fig = go.Figure()
    fig.add_annotation(text=message, x=.5, y=.5, xref="paper", yref="paper", showarrow=False)
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    fig.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=40, b=20))
    return fig


def graph_card(graph_id, height=430):
    return html.Div(
        dcc.Graph(id=graph_id, config={"displaylogo": False, "responsive": True}, style={"height": f"{height}px"}),
        style={**CARD_STYLE, "padding": "8px"},
    )


def kpi_card(title, value_id, note=None):
    ch = [
        html.Div(title, style={"fontSize": "13px", "fontWeight": "600", "color": "#667085", "marginBottom": "8px"}),
        html.Div(id=value_id, style={"fontSize": "29px", "fontWeight": "700", "color": "#18202a"}),
    ]
    if note:
        ch.append(html.Div(note, style={"fontSize": "11px", "color": "#98a2b3", "marginTop": "7px"}))
    return html.Div(ch, style=CARD_STYLE)


def add_gap_breaks(df, date_col, value_cols, max_gap_days=1):
    """Lisab NaN-reaga katkestuse, kui järjestikuste andmepäevade vahe on suurem kui max_gap_days."""
    if df.empty:
        return df.copy()
    d = df.sort_values(date_col).copy()
    rows = []
    prev = None
    for _, row in d.iterrows():
        cur = row[date_col]
        if prev is not None and (cur - prev).days > max_gap_days:
            gap = {c: np.nan for c in d.columns}
            gap[date_col] = prev + pd.Timedelta(days=1)
            rows.append(gap)
        rows.append(row.to_dict())
        prev = cur
    return pd.DataFrame(rows)


def filter_sessions(start_date=None, end_date=None, langs=None):
    out = filter_dates(sessions, start_date, end_date)
    if langs:
        out = out[out["ticket_language"].isin(langs)]
    return out.copy()


def map_data(start_date, end_date, languages=None, metric="unique_sessions", action="ALL"):
    # 0/1 tegevuse filter kasutab eraldi agregeeritud tabelit.
    if action != "ALL":
        if exhibit_action.empty:
            return pd.DataFrame(), "Tegevuste 0/1 tabel puudub. Käivita scripts/13_prepare_action_data.py."
        df = filter_dates(exhibit_action, start_date, end_date)
        df = df[df["action_code"].astype(str) == str(action)]
        if languages:
            lang_col = "ticket_language" if "ticket_language" in df.columns else None
            if lang_col:
                df = df[df[lang_col].isin(languages)]
    elif languages:
        df = filter_dates(exhibit_language, start_date, end_date)
        if not df.empty:
            lang_col = "language" if "language" in df.columns else "ticket_language"
            df = df[df[lang_col].isin(languages)]
    else:
        df = filter_dates(exhibit_daily, start_date, end_date)

    if df.empty:
        return pd.DataFrame(), None

    value_col = metric if metric in df.columns else ("event_count" if "event_count" in df.columns else None)
    if value_col is None:
        return pd.DataFrame(), "Valitud mõõdikut tabelis ei ole."

    grouped = df.groupby("t_code", as_index=False)[value_col].sum().rename(columns={value_col: "value"})
    grouped["t_code"] = grouped["t_code"].astype(str).str.strip()
    out = grouped.merge(exhibit_lookup, on="t_code", how="left").merge(coordinates, on="t_code", how="inner")
    return out, None


def make_museum_map(start_date, end_date, languages=None, metric="unique_sessions", action="ALL", title=None):
    df, message = map_data(start_date, end_date, languages, metric, action)
    if message:
        return empty_fig(message)
    if df.empty:
        return empty_fig("Selle valiku kohta näitusekaardi andmeid ei ole.")

    sizes = np.sqrt(df["value"].clip(lower=0))
    df["marker_size"] = 9 if sizes.max() == 0 else 9 + 35 * sizes / sizes.max()

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["x"], y=df["y"], mode="markers",
        customdata=np.stack([df["exhibit_name"], df["t_code"], df["value"]], axis=-1),
        marker=dict(
            size=df["marker_size"], color=df["value"], colorscale="YlOrRd", opacity=.74,
            showscale=True,
            colorbar=dict(title="Sessioone" if metric == "unique_sessions" else "Sündmusi"),
            line=dict(width=.5, color="white"),
        ),
        hovertemplate=(
            "<b>%{customdata[0]}</b>"
            "<br>T-kood: %{customdata[1]}"
            + ("<br>Unikaalseid digisessioone: %{customdata[2]:,.0f}" if metric == "unique_sessions" else "<br>Logisündmusi: %{customdata[2]:,.0f}")
            + "<extra></extra>"
        ),
    ))

    if MAP_URI:
        fig.add_layout_image(dict(
            source=MAP_URI, xref="x", yref="y", x=0, y=0,
            xanchor="left", yanchor="top", sizex=MAP_WIDTH, sizey=MAP_HEIGHT,
            sizing="stretch", opacity=1, layer="below",
        ))

    fig.update_xaxes(range=[0, MAP_WIDTH], visible=False, fixedrange=False)
    fig.update_yaxes(range=[MAP_HEIGHT, 0], visible=False, scaleanchor="x", scaleratio=1, fixedrange=False)
    fig.update_layout(
        template="plotly_white", title=dict(text=title or "Näituse kasutus", x=.02),
        margin=dict(l=5, r=10, t=55, b=5), paper_bgcolor="white", plot_bgcolor="white",
        dragmode="pan",
    )
    return fig

# ============================================================
# 4. ANDMETE LAADIMINE
# ============================================================
print("Loen dashboardi andmeid...")
sessions = ensure_date(pd.read_parquet(SESSIONS_FILE))
for src, dst in {
    "ticket_language_dashboard": "ticket_language",
    "duration_min_dashboard": "duration_minutes",
    "places_count_dashboard": "unique_t_codes",
    "event_count_dashboard": "event_count",
}.items():
    if dst not in sessions.columns and src in sessions.columns:
        sessions[dst] = sessions[src]

sessions["ticket_language"] = sessions.get("ticket_language", "Teadmata").fillna("Teadmata").astype(str)
sessions["duration_minutes"] = pd.to_numeric(sessions.get("duration_minutes"), errors="coerce")
sessions["unique_t_codes"] = pd.to_numeric(sessions.get("unique_t_codes"), errors="coerce")
sessions["event_count"] = pd.to_numeric(sessions.get("event_count"), errors="coerce")
sessions["start_hour"] = pd.to_numeric(sessions.get("start_hour"), errors="coerce")
sessions["weekday_num"] = sessions["date"].dt.dayofweek
sessions["weekday"] = sessions["weekday_num"].map({0:"E",1:"T",2:"K",3:"N",4:"R",5:"L",6:"P"})

exhibit_daily = ensure_date(read_optional(EXHIBIT_DAILY_FILE))
exhibit_language = ensure_date(read_optional(EXHIBIT_LANGUAGE_FILE))
exhibit_action = ensure_date(read_optional(EXHIBIT_ACTION_FILE))
context = ensure_date(read_optional(CONTEXT_FILE))
ticket_sales = ensure_date(read_optional(TICKET_SALES_FILE))
school_holidays = ensure_date(read_optional(SCHOOL_HOLIDAYS_FILE))
weather_daily = ensure_date(read_optional(WEATHER_FILE))
museum_events_daily = ensure_date(read_optional(MUSEUM_EVENTS_FILE))

# Koordinaadid
coordinates = pd.read_csv(COORDINATES_FILE, dtype={"code":"string"}).rename(columns={"code":"t_code"})
coordinates["t_code"] = coordinates["t_code"].astype(str).str.strip()
coordinates["x"] = pd.to_numeric(coordinates["x"], errors="coerce")
coordinates["y"] = pd.to_numeric(coordinates["y"], errors="coerce")
coordinates = coordinates.dropna(subset=["t_code", "x", "y"])[["t_code","x","y"]].drop_duplicates("t_code")

# Eksponaadi nimed: esmalt juba agregeeritud topic, fallback Device_id.xlsx.
name_parts = []
for source in [exhibit_daily, exhibit_language, exhibit_action]:
    if not source.empty and "topic" in source.columns:
        name_parts.append(source.loc[source["topic"].notna(), ["t_code","topic"]])

if name_parts:
    exhibit_lookup = pd.concat(name_parts, ignore_index=True).drop_duplicates("t_code").rename(columns={"topic":"exhibit_name"})
else:
    exhibit_lookup = pd.DataFrame(columns=["t_code","exhibit_name"])

if DEVICE_FILE.exists():
    try:
        dev = pd.read_excel(DEVICE_FILE, sheet_name="kõik logid")
        dev["t_code"] = dev["Name"].astype("string").str.extract(r"(T\d+(?:\.\d+)+)", expand=False)
        dev_names = (
            dev.loc[dev["t_code"].notna() & dev["Topic"].notna(), ["t_code","Topic"]]
            .drop_duplicates("t_code")
            .rename(columns={"Topic":"device_name"})
        )
        exhibit_lookup = exhibit_lookup.merge(dev_names, on="t_code", how="outer")
        exhibit_lookup["exhibit_name"] = exhibit_lookup["exhibit_name"].fillna(exhibit_lookup["device_name"])
        exhibit_lookup = exhibit_lookup[["t_code","exhibit_name"]]
    except Exception as exc:
        print("Device_id.xlsx nimede lugemise hoiatus:", exc)

exhibit_lookup["exhibit_name"] = exhibit_lookup.get("exhibit_name", pd.Series(dtype=str)).fillna(exhibit_lookup.get("t_code")).astype(str)
exhibit_lookup = exhibit_lookup.drop_duplicates("t_code")

# Kaart base64
MAP_URI = None
MAP_WIDTH, MAP_HEIGHT = 11812, 6300
if MAP_FILE.exists():
    im = Image.open(MAP_FILE)
    MAP_WIDTH, MAP_HEIGHT = im.size
    encoded = base64.b64encode(MAP_FILE.read_bytes()).decode("ascii")
    MAP_URI = f"data:image/png;base64,{encoded}"

min_date = sessions["date"].min().date()
max_date = sessions["date"].max().date()
languages = sorted([x for x in sessions["ticket_language"].dropna().unique() if x != "Teadmata"])
lang_options = [{"label": x, "value": x} for x in languages]

# ============================================================
# TÄIELIK PÄEVAKONTEKST
# ============================================================
# Aeg ja kontekst ei toetu enam ainult päevadele, kus oli logisessioon.
# Loome täieliku kalendri ning ühendame iga allika eraldi.
context_full = pd.DataFrame({
    "date": pd.date_range(pd.Timestamp(min_date), pd.Timestamp(max_date), freq="D")
})

# Piletimüük
if not ticket_sales.empty:
    ts = ticket_sales.copy()
    keep = [c for c in ["date", "tickets_sold", "ticket_transactions", "paid_sum"] if c in ts.columns]
    ts = ts[keep].drop_duplicates("date")
    context_full = context_full.merge(ts, on="date", how="left")

# Ilm
if not weather_daily.empty:
    w = weather_daily.copy().drop_duplicates("date")
    context_full = context_full.merge(w, on="date", how="left")

# ERMi sündmused: üks või mitu sündmust samal päeval
if not museum_events_daily.empty:
    me = museum_events_daily.copy()
    if "event_type" in me.columns:
        event_day = (
            me.groupby("date", as_index=False)
              .agg(
                  museum_event_count=("event_type", "size"),
                  museum_event_types=("event_type", lambda x: " | ".join(sorted(set(x.dropna().astype(str)))))
              )
        )
    else:
        event_day = me.groupby("date", as_index=False).size().rename(columns={"size": "museum_event_count"})
    context_full = context_full.merge(event_day, on="date", how="left")

# Koolivaheajad
if not school_holidays.empty:
    sh = school_holidays.copy().drop_duplicates("date")
    holiday_cols = [c for c in sh.columns if c == "date" or c.startswith("school_holiday_")]
    context_full = context_full.merge(sh[holiday_cols], on="date", how="left")

for col in [
    "school_holiday_estonia",
    "school_holiday_latvia",
    "school_holiday_finland",
    "school_holiday_any",
]:
    if col not in context_full.columns:
        context_full[col] = False
    context_full[col] = context_full[col].fillna(False).astype(bool)

if "museum_event_count" not in context_full.columns:
    context_full["museum_event_count"] = 0
context_full["museum_event_count"] = context_full["museum_event_count"].fillna(0).astype(int)

print(
    "Täielik päevakontekst:",
    len(context_full),
    "päeva;",
    "piletimüügi päevad:",
    int(context_full["tickets_sold"].notna().sum()) if "tickets_sold" in context_full.columns else 0,
    "; ilma päevad:",
    int(context_full["temp_mean_c"].notna().sum()) if "temp_mean_c" in context_full.columns else 0,
)

# ============================================================
# 5. LAYOUT
# ============================================================
app = Dash(__name__, suppress_callback_exceptions=True)
server = app.server
app.title = "ERMi külastusandmed"

filter_bar = html.Div([
    html.Div([
        html.Label("Periood", style={"fontSize":"13px","fontWeight":"600","display":"block","marginBottom":"6px"}),
        dcc.DatePickerRange(id="date-range", min_date_allowed=min_date, max_date_allowed=max_date,
                            start_date=min_date, end_date=max_date, display_format="DD.MM.YYYY", first_day_of_week=1),
    ]),
    html.Div([
        html.Label("Piletikeel", style={"fontSize":"13px","fontWeight":"600","display":"block","marginBottom":"6px"}),
        dcc.Dropdown(id="language-filter", options=lang_options, value=[], multi=True,
                     placeholder="Kõik keeled", clearable=True),
    ], style={"minWidth":"300px","flex":"1"}),
], style={**CARD_STYLE, "display":"flex","gap":"24px","alignItems":"end","flexWrap":"wrap","marginBottom":"22px"})


def overview_layout():
    return html.Div([
        html.H2("Ülevaade"),
        html.Div([
            kpi_card("Müüdud pileteid", "kpi-tickets", "Piletimüügi andmed; keelefilter seda ei mõjuta"),
            kpi_card("Digitaalseid kasutussessioone", "kpi-sessions"),
            kpi_card("Digikasutuse määr", "kpi-rate", "Näidatakse ainult siis, kui keelefilter pole valitud"),
            kpi_card("Mediaan digikasutuse kestus", "kpi-duration", "Esimese ja viimase logitud tegevuse vahe"),
            kpi_card("Mediaan kasutatud eksponaate", "kpi-places"),
        ], style={"display":"grid","gridTemplateColumns":"repeat(auto-fit,minmax(190px,1fr))","gap":"14px","marginBottom":"20px"}),
        html.Div([graph_card("overview-sales", 430), graph_card("overview-language", 430)],
                 style={"display":"grid","gridTemplateColumns":"minmax(0,2fr) minmax(320px,1fr)","gap":"18px","marginBottom":"18px"}),
        html.Div([graph_card("overview-duration", 400), graph_card("overview-hour", 400)],
                 style={"display":"grid","gridTemplateColumns":"repeat(2,minmax(0,1fr))","gap":"18px"}),
    ])


def map_layout():
    return html.Div([
        html.H2("Näituse kasutus"),
        html.Div([
            html.Div([html.Label("Mõõdik"), dcc.RadioItems(id="map-metric", options=[
                {"label":" Unikaalsed digisessioonid","value":"unique_sessions"},
                {"label":" Logisündmused","value":"event_count"}], value="unique_sessions", inline=True)]),
            html.Div([html.Label("Tegevus"), dcc.Dropdown(id="map-action", options=[
                {"label":"Kõik tegevused","value":"ALL"},
                {"label":"0 – keele muutmine","value":"0"},
                {"label":"1 – teksti salvestamine","value":"1"}], value="ALL", clearable=False)], style={"minWidth":"250px"}),
        ], style={**CARD_STYLE,"display":"flex","gap":"30px","alignItems":"end","flexWrap":"wrap","marginBottom":"16px"}),
        graph_card("museum-map", 720),
        html.Div(style={"height":"18px"}),
        graph_card("exhibit-top", 440),
    ])


def language_layout():
    return html.Div([
        html.H2("Piletikeeled"),
        html.Div("Kestus tähendab digitaalse kasutuse ajavahemikku esimese ja viimase logitud tegevuse vahel, mitte kogu muuseumikülastuse kestust.",
                 style={"color":"#667085","marginBottom":"16px"}),
        html.Div([graph_card("lang-summary", 430), graph_card("lang-time", 430)],
                 style={"display":"grid","gridTemplateColumns":"repeat(2,minmax(0,1fr))","gap":"18px"}),
    ])


def context_layout():
    return html.Div([
        html.H2("Aeg ja kontekst"),
        html.Div([graph_card("ctx-timeline", 470), graph_card("ctx-holidays", 430)], style={"display":"grid","gap":"18px","marginBottom":"18px"}),
        html.Div([graph_card("ctx-events", 420), graph_card("ctx-weather", 420)],
                 style={"display":"grid","gridTemplateColumns":"repeat(2,minmax(0,1fr))","gap":"18px"}),
    ])


def compare_layout():
    return html.Div([
        html.H2("Võrdle perioode ja keeli"),
        html.Div([
            html.Div([html.B("A"), dcc.DatePickerRange(id="cmp-a-date", min_date_allowed=min_date, max_date_allowed=max_date,
                                                        start_date=min_date, end_date=(pd.Timestamp(min_date)+pd.Timedelta(days=30)).date(), display_format="DD.MM.YYYY"),
                      dcc.Dropdown(id="cmp-a-lang", options=[{"label":"Kõik keeled","value":"ALL"}]+lang_options, value="ALL", clearable=False)]),
            html.Div([html.B("B"), dcc.DatePickerRange(id="cmp-b-date", min_date_allowed=min_date, max_date_allowed=max_date,
                                                        start_date=(pd.Timestamp(max_date)-pd.Timedelta(days=30)).date(), end_date=max_date, display_format="DD.MM.YYYY"),
                      dcc.Dropdown(id="cmp-b-lang", options=[{"label":"Kõik keeled","value":"ALL"}]+lang_options, value="ALL", clearable=False)]),
        ], style={**CARD_STYLE,"display":"grid","gridTemplateColumns":"repeat(2,minmax(0,1fr))","gap":"30px","marginBottom":"18px"}),
        html.Div([graph_card("cmp-map-a", 600), graph_card("cmp-map-b", 600)],
                 style={"display":"grid","gridTemplateColumns":"repeat(2,minmax(0,1fr))","gap":"18px","marginBottom":"18px"}),
        html.Div([graph_card("cmp-kpis", 420), graph_card("cmp-languages", 420)],
                 style={"display":"grid","gridTemplateColumns":"repeat(2,minmax(0,1fr))","gap":"18px"}),
    ])

app.layout = html.Div([
    html.Div("EESTI RAHVA MUUSEUM", style={"fontSize":"12px","letterSpacing":"1.5px","fontWeight":"700","color":"#667085"}),
    html.H1("Külastusandmete uurija", style={"margin":"6px 0 4px","fontSize":"34px"}),
    html.Div("Piletimüük, digitaalsete eksponaatide kasutus ja muuseumi kontekst", style={"color":"#667085","marginBottom":"24px"}),
    filter_bar,
    dcc.Tabs(id="tabs", value="overview", children=[
        dcc.Tab(label="Ülevaade", value="overview"),
        dcc.Tab(label="Aeg ja kontekst", value="context"),
        dcc.Tab(label="Näitusekaart", value="map"),
        dcc.Tab(label="Keeled", value="languages"),
        dcc.Tab(label="Võrdle", value="compare"),
    ]),
    html.Div(id="tab-content", style={"paddingTop":"24px"}),
], style={"maxWidth":"1500px","margin":"0 auto","padding":"32px 28px 60px"})

@app.callback(Output("tab-content","children"), Input("tabs","value"))
def render_tab(tab):
    return {"overview":overview_layout,"context":context_layout,"map":map_layout,"languages":language_layout,"compare":compare_layout}.get(tab, overview_layout)()

# ============================================================
# 6. ÜLEVAADE
# ============================================================
@app.callback(
    Output("kpi-tickets","children"), Output("kpi-sessions","children"), Output("kpi-rate","children"),
    Output("kpi-duration","children"), Output("kpi-places","children"),
    Output("overview-sales","figure"), Output("overview-language","figure"), Output("overview-duration","figure"), Output("overview-hour","figure"),
    Input("date-range","start_date"), Input("date-range","end_date"), Input("language-filter","value"),
)
def update_overview(start_date, end_date, langs):
    s = filter_sessions(start_date, end_date, langs)
    sales = filter_dates(ticket_sales, start_date, end_date)
    tickets = sales["tickets_sold"].sum() if not sales.empty and "tickets_sold" in sales.columns else np.nan
    n_sessions = len(s)
    rate = (n_sessions / tickets * 100) if (not langs and pd.notna(tickets) and tickets > 0) else np.nan

    # Müük + digisessioonid ajas. Keelefilter rakendub ainult digisessioonidele.
    d = s.groupby("date").size().reset_index(name="digital_sessions")
    d = add_gap_breaks(d, "date", ["digital_sessions"])
    fig_sales = go.Figure()
    if not sales.empty and "tickets_sold" in sales.columns:
        t = sales[["date","tickets_sold"]].sort_values("date")
        t = add_gap_breaks(t, "date", ["tickets_sold"])
        fig_sales.add_trace(go.Scatter(x=t["date"], y=t["tickets_sold"], mode="lines", name="Müüdud pileteid",
                                       hovertemplate="<b>%{x|%d.%m.%Y}</b><br>Müüdud pileteid: %{y:,.0f}<extra></extra>"))
    fig_sales.add_trace(go.Scatter(x=d["date"], y=d["digital_sessions"], mode="lines", name="Digitaalseid sessioone",
                                   hovertemplate="<b>%{x|%d.%m.%Y}</b><br>Digitaalseid sessioone: %{y:,.0f}<extra></extra>"))
    fig_sales = style_fig(fig_sales, "Piletimüük ja digitaalse süsteemi kasutus")
    fig_sales.update_xaxes(title="")
    fig_sales.update_yaxes(title="Arv")

    lg = s.groupby("ticket_language", as_index=False).agg(
        sessions=("session_id","size"), median_duration=("duration_minutes","median"),
        median_exhibits=("unique_t_codes","median"), median_events=("event_count","median"),
    ).sort_values("sessions")
    fig_lang = px.bar(lg, x="sessions", y="ticket_language", orientation="h",
                      hover_data=["median_duration","median_exhibits","median_events"], labels=LABELS)
    fig_lang = style_fig(fig_lang, "Piletikeeled")
    fig_lang.update_xaxes(title="Digitaalseid sessioone")
    fig_lang.update_yaxes(title="")

    dur = s[s["duration_minutes"].between(0,300)]
    fig_dur = px.histogram(dur, x="duration_minutes", nbins=55, labels=LABELS)
    fig_dur = style_fig(fig_dur, "Digikasutuse kestus")
    fig_dur.update_yaxes(title="Sessioone")

    hh = s.dropna(subset=["start_hour"]).copy()
    hh["hour"] = np.floor(hh["start_hour"]).astype(int)
    hh = hh.groupby("hour").size().reset_index(name="sessions")
    fig_hour = px.bar(hh, x="hour", y="sessions", labels=LABELS)
    fig_hour = style_fig(fig_hour, "Mis kell digitaalne kasutus algab?")
    fig_hour.update_xaxes(dtick=1)

    return fmt_int(tickets), fmt_int(n_sessions), (fmt_num(rate)+"%" if pd.notna(rate) else "–"), fmt_num(s["duration_minutes"].median()), fmt_num(s["unique_t_codes"].median()), fig_sales, fig_lang, fig_dur, fig_hour

# ============================================================
# 7. NÄITUSEKAART
# ============================================================
@app.callback(
    Output("museum-map","figure"), Output("exhibit-top","figure"),
    Input("date-range","start_date"), Input("date-range","end_date"), Input("language-filter","value"),
    Input("map-metric","value"), Input("map-action","value"),
)
def update_map(start_date, end_date, langs, metric, action):
    fig = make_museum_map(start_date, end_date, langs, metric, action)
    df, msg = map_data(start_date, end_date, langs, metric, action)
    if msg or df.empty:
        return fig, empty_fig(msg or "Andmeid ei ole.")
    top = df.sort_values("value", ascending=False).head(20).sort_values("value")
    top["label"] = top["exhibit_name"]
    fig_top = px.bar(top, x="value", y="label", orientation="h", labels={"value":("Unikaalseid digisessioone" if metric=="unique_sessions" else "Logisündmusi"), "label":"Ekspositsioon"})
    fig_top = style_fig(fig_top, "20 enim kasutatud ekspositsiooni")
    fig_top.update_yaxes(title="")
    return fig, fig_top

# ============================================================
# 8. KEELED
# ============================================================
@app.callback(Output("lang-summary","figure"), Output("lang-time","figure"), Input("date-range","start_date"), Input("date-range","end_date"))
def update_languages(start_date, end_date):
    s = filter_sessions(start_date, end_date, [])
    lg = s.groupby("ticket_language", as_index=False).agg(
        sessions=("session_id","size"), median_duration=("duration_minutes","median"),
        median_exhibits=("unique_t_codes","median"), median_events=("event_count","median"),
    )
    fig1 = px.scatter(lg, x="median_duration", y="median_exhibits", size="sessions", color="ticket_language",
                      hover_name="ticket_language", hover_data={"sessions":True,"median_events":True,"median_duration":":.1f","median_exhibits":":.1f"}, labels=LABELS)
    fig1 = style_fig(fig1, "Keeled: kestus, kasutatud eksponaadid ja sessioonide arv")
    fig1.update_xaxes(title="Mediaan digikasutuse kestus (min)")
    fig1.update_yaxes(title="Mediaan kasutatud eksponaate")

    m = s.copy(); m["month_date"] = m["date"].dt.to_period("M").dt.to_timestamp()
    m = m.groupby(["month_date","ticket_language"]).size().reset_index(name="sessions")
    fig2 = px.line(m, x="month_date", y="sessions", color="ticket_language", labels=LABELS)
    fig2 = style_fig(fig2, "Piletikeeled ajas")
    fig2.update_xaxes(title="")
    fig2.update_yaxes(title="Digitaalseid sessioone")
    fig2.update_traces(connectgaps=False, hovertemplate="<b>%{x|%m.%Y}</b><br>Digitaalseid sessioone: %{y:,.0f}<extra></extra>")
    return fig1, fig2

# ============================================================
# 9. AEG JA KONTEKST
# ============================================================
@app.callback(
    Output("ctx-timeline","figure"), Output("ctx-holidays","figure"), Output("ctx-events","figure"), Output("ctx-weather","figure"),
    Input("date-range","start_date"), Input("date-range","end_date"), Input("language-filter","value"),
)
def update_context(start_date, end_date, langs):
    # Täielik kalender: piletimüük, ilm, sündmused ja koolivaheajad
    ctx = filter_dates(context_full, start_date, end_date)

    # Digisessioonid tulevad eraldi logidest ning keelefilter võib neid mõjutada.
    s = filter_sessions(start_date, end_date, langs)
    digital = (
        s.groupby("date")
         .size()
         .reset_index(name="digital_sessions")
    )

    # --------------------------------------------------------
    # 1. AJATELG
    # --------------------------------------------------------
    fig = go.Figure()

    if "tickets_sold" in ctx.columns:
        sales_plot = ctx.loc[ctx["tickets_sold"].notna(), ["date", "tickets_sold"]].copy()
        sales_plot = add_gap_breaks(sales_plot, "date", ["tickets_sold"])
        if not sales_plot.empty:
            fig.add_trace(go.Scatter(
                x=sales_plot["date"],
                y=sales_plot["tickets_sold"],
                mode="lines",
                name="Müüdud pileteid",
                connectgaps=False,
                hovertemplate="<b>%{x|%d.%m.%Y}</b><br>Müüdud pileteid: %{y:,.0f}<extra></extra>",
            ))

    if not digital.empty:
        digital_plot = add_gap_breaks(digital, "date", ["digital_sessions"])
        fig.add_trace(go.Scatter(
            x=digital_plot["date"],
            y=digital_plot["digital_sessions"],
            mode="lines",
            name="Digitaalseid sessioone",
            connectgaps=False,
            hovertemplate="<b>%{x|%d.%m.%Y}</b><br>Digitaalseid sessioone: %{y:,.0f}<extra></extra>",
        ))

    # Koolivaheaegade taustavööndid kasutavad nüüd täielikku kalendrit.
    for col, label in [
        ("school_holiday_estonia", "Eesti koolivaheaeg"),
        ("school_holiday_latvia", "Läti koolivaheaeg"),
        ("school_holiday_finland", "Soome koolivaheaeg"),
    ]:
        if col in ctx.columns:
            dates = ctx.loc[ctx[col] == True, "date"].sort_values()
            if not dates.empty:
                groups = dates.diff().dt.days.ne(1).cumsum()
                for _, g in dates.groupby(groups):
                    fig.add_vrect(
                        x0=g.min(),
                        x1=g.max() + pd.Timedelta(days=1),
                        opacity=.055,
                        line_width=0,
                    )

    fig = style_fig(fig, "Piletimüük, digikasutus ja koolivaheajad")
    fig.update_xaxes(title="")
    fig.update_yaxes(title="Arv")

    # --------------------------------------------------------
    # 2. KOOLIVAHEAEG VS TAVAPERIOOD
    # --------------------------------------------------------
    holiday_rows = []
    if "tickets_sold" in ctx.columns:
        for col, label in [
            ("school_holiday_estonia", "Eesti"),
            ("school_holiday_latvia", "Läti"),
            ("school_holiday_finland", "Soome"),
        ]:
            if col in ctx.columns:
                for flag, period_name in [(True, "Vaheaeg"), (False, "Tavaperiood")]:
                    vals = ctx.loc[(ctx[col] == flag) & ctx["tickets_sold"].notna(), "tickets_sold"]
                    holiday_rows.append({
                        "Riik": label,
                        "Periood": period_name,
                        "Keskmine pileteid päevas": vals.mean() if len(vals) else np.nan,
                        "Päevi": len(vals),
                    })

    hd = pd.DataFrame(holiday_rows)
    if not hd.empty and hd["Keskmine pileteid päevas"].notna().any():
        fig_h = px.bar(
            hd,
            x="Riik",
            y="Keskmine pileteid päevas",
            color="Periood",
            barmode="group",
            hover_data={"Päevi": True, "Keskmine pileteid päevas": ":.1f"},
        )
        fig_h = style_fig(fig_h, "Koolivaheaeg vs tavaperiood")
        fig_h.update_xaxes(title="")
        fig_h.update_yaxes(title="Keskmine müüdud piletite arv päevas")
    else:
        fig_h = empty_fig("Koolivaheaegade ja piletimüügi kattuvaid andmeid ei ole.")

    # --------------------------------------------------------
    # 3. ERMi SÜNDMUSED
    # --------------------------------------------------------
    if "museum_event_count" in ctx.columns and "tickets_sold" in ctx.columns:
        e = ctx.loc[ctx["tickets_sold"].notna()].copy()
        e["Päeva tüüp"] = np.where(
            e["museum_event_count"].fillna(0) > 0,
            "ERMi sündmusega päev",
            "Sündmuseta päev",
        )
        es = (
            e.groupby("Päeva tüüp", as_index=False)
             .agg(
                 **{
                     "Keskmine pileteid päevas": ("tickets_sold", "mean"),
                     "Päevi": ("date", "size"),
                 }
             )
        )
        fig_e = px.bar(
            es,
            x="Päeva tüüp",
            y="Keskmine pileteid päevas",
            hover_data={"Päevi": True, "Keskmine pileteid päevas": ":.1f"},
        )
        fig_e = style_fig(fig_e, "ERMi sündmused ja piletimüük")
        fig_e.update_xaxes(title="")
        fig_e.update_yaxes(title="Keskmine müüdud piletite arv päevas")
    else:
        fig_e = empty_fig("ERMi sündmuste ja piletimüügi kattuvaid andmeid ei ole.")

    # --------------------------------------------------------
    # 4. ILM
    # --------------------------------------------------------
    if "temp_mean_c" in ctx.columns and "tickets_sold" in ctx.columns:
        w = ctx.dropna(subset=["temp_mean_c", "tickets_sold"]).copy()
        if not w.empty:
            fig_w = px.scatter(
                w,
                x="temp_mean_c",
                y="tickets_sold",
                hover_data={
                    "date": "|%d.%m.%Y",
                    "temp_mean_c": ":.1f",
                    "tickets_sold": ":.0f",
                },
                labels={
                    "date": "Kuupäev",
                    "temp_mean_c": "Keskmine temperatuur (°C)",
                    "tickets_sold": "Müüdud pileteid",
                },
                opacity=.55,
            )
            fig_w = style_fig(fig_w, "Temperatuur ja piletimüük")
            fig_w.update_xaxes(title="Keskmine temperatuur (°C)")
            fig_w.update_yaxes(title="Müüdud pileteid")
        else:
            fig_w = empty_fig("Valitud perioodil ilma ja piletimüügi kattuvaid andmeid ei ole.")
    else:
        fig_w = empty_fig("Ilmaandmeid ei ole.")

    return fig, fig_h, fig_e, fig_w

# ============================================================
# 10. VÕRDLUS
# ============================================================
@app.callback(
    Output("cmp-map-a","figure"), Output("cmp-map-b","figure"), Output("cmp-kpis","figure"), Output("cmp-languages","figure"),
    Input("cmp-a-date","start_date"), Input("cmp-a-date","end_date"), Input("cmp-a-lang","value"),
    Input("cmp-b-date","start_date"), Input("cmp-b-date","end_date"), Input("cmp-b-lang","value"),
)
def update_compare(a_start,a_end,a_lang,b_start,b_end,b_lang):
    langs_a=[] if a_lang=="ALL" else [a_lang]
    langs_b=[] if b_lang=="ALL" else [b_lang]
    map_a=make_museum_map(a_start,a_end,langs_a,"unique_sessions","ALL",f"A · {a_lang if a_lang!='ALL' else 'kõik keeled'}")
    map_b=make_museum_map(b_start,b_end,langs_b,"unique_sessions","ALL",f"B · {b_lang if b_lang!='ALL' else 'kõik keeled'}")
    a=filter_sessions(a_start,a_end,langs_a); b=filter_sessions(b_start,b_end,langs_b)
    summ=pd.DataFrame({
        "Mõõdik":["Digitaalseid sessioone","Mediaankestus (min)","Mediaan eksponaate","Mediaan tegevusi"],
        "A":[len(a),a["duration_minutes"].median(),a["unique_t_codes"].median(),a["event_count"].median()],
        "B":[len(b),b["duration_minutes"].median(),b["unique_t_codes"].median(),b["event_count"].median()],
    }).melt(id_vars="Mõõdik",var_name="Periood",value_name="Väärtus")
    fig_k=px.bar(summ,x="Mõõdik",y="Väärtus",color="Periood",barmode="group")
    fig_k=style_fig(fig_k,"Kasutusmustri võrdlus"); fig_k.update_xaxes(title="")

    # Keelejaotus perioodides – kui konkreetne keel valitud, näitab sisuliselt selle osakaalu asemel sessioonide arvu; kõik keeled puhul täielik jaotus.
    frames=[]
    for label,df in [("A",filter_sessions(a_start,a_end,[])),("B",filter_sessions(b_start,b_end,[]))]:
        tmp=df.groupby("ticket_language").size().reset_index(name="Sessioone"); tmp["Periood"]=label; frames.append(tmp)
    ld=pd.concat(frames,ignore_index=True)
    fig_l=px.bar(ld,x="ticket_language",y="Sessioone",color="Periood",barmode="group",labels={"ticket_language":"Piletikeel"})
    fig_l=style_fig(fig_l,"Piletikeelte jaotus kahes perioodis"); fig_l.update_xaxes(title="Piletikeel")
    return map_a,map_b,fig_k,fig_l

# ============================================================
# 11. START
# ============================================================
if __name__ == "__main__":
    print("Ava brauseris: http://127.0.0.1:8050/")
    app.run(debug=False, host="127.0.0.1", port=8050)