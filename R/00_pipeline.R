source("~/visitor_data/R/01_parse_logs.R")
source("~/visitor_data/R/02_join_devices.R")
source("~/visitor_data/R/03_make_paths.R")
source("~/visitor_data/R/04_usage_summary.R")
source("~/visitor_data/R/05_plot_daily_usage.R")
rm(list = ls()) # clear environment 
print("Processing complete.")