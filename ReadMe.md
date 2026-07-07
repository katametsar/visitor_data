# Visitor interaction log analysis

This repository contains scripts and documentation for analysing interaction logs from the Estonian National Museum permanent exhibition.

The purpose of the project is to explore how interactive exhibition points are used over time and how event sequences can be transformed into approximate movement paths between exhibition points.

The dataset supports analysis of system interactions, exhibition point usage, temporal patterns and inferred movement sequences. It does not directly measure attention, learning, emotional engagement or the full visitor experience.

---

## RQs, tasks and progress

How do different visitors walk through the exhibition? 

- [] Model the paths of visitors  
  - [x] isolate the paths
  - [] visualise the paths 
    - [] visualise the model of the museum exhibition 
- [] Heatmap of the most visited parts of the exhibition 
  - [x] counts of the devices
  - [] visualise 

How do visitors visit the exhibition? What patterns, what dates, events, weather... 

- [] Visitor data 
  - [] Model with the  ticket sales data - fixed effects/multi var regression? 
      - [] seasonal effects 
      - [] weather effects 
      - [] weekday effects
    - [] import the ticket sales 
    - [] school vacations 
    - [] ERM events 
    - [] weather in Tartu 

---

## Access & allowed use

This dataset is provided for:

- research and prototyping
- visualizations and exploratory analysis
- presentations and demo publications
- methodological development for visitor analytics

Not allowed:

- commercial reuse
- re-publishing raw data outside this repository
- attempts to identify individual visitors
- combining the data with other datasets for deanonymization
- interpreting anonymized identifiers as personal identities

---

## Citation requirement

Estonian National Museum. *Encounters exhibition interactive ticket log dataset*, 2026.

---

## Repository structure

```text
visitor-logs/
│
├── data_raw/
│   ├── Logide_failid/
│   │   ├── log_*.log
│   ├── Device_id.xlsx
│   ├── Cards - languages.csv
│   └── Permanent_exhibition_plan.pdf
│
├── data_clean/
│   ├── parsed_logs.csv
│   ├── logs_with_devices.csv
│   └── visitor_paths.csv
│
├── outputs/
│   ├── point_usage.csv
│   ├── daily_usage.csv
│   ├── daily_visitors.csv
│   ├── hourly_usage.csv
│   ├── weekday_usage.csv
│   ├── daily_usage_points.png
│   ├── daily_usage_discontinuous_line.png
│   ├── daily_usage_complete_calendar.csv
│   └── daily_usage_coverage_summary.csv
│
├── R/
│   ├── 00_pipeline.R
│   ├── 01_parse_logs.R
│   ├── 02_join_devices.R
│   ├── 03_make_paths.R
│   ├── 04_usage_summary.R
│   └── 05_plot_daily_usage.R
│
└── README.md