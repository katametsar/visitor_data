suppressPackageStartupMessages(library(tidyverse))
suppressPackageStartupMessages(library(lubridate))

logs <- read_csv("data_clean/logs_with_devices.csv", show_col_types = FALSE)

# 1. Jätame alles ainult punktiga logid
# 2. Teeme aja ja külastaja ID
# 3. Sorteerime külastaja ja aja järgi
# 4. Eemaldame järjestikused korduvad punktid
logs_compact <- logs %>%
  filter(!is.na(point_id)) %>%
  mutate(
    timestamp = dmy_hms(time_raw),
    visitor_id = card_hex
  ) %>%
  arrange(visitor_id, timestamp) %>%
  group_by(visitor_id) %>%
  mutate(previous_point = lag(point_id)) %>%
  filter(is.na(previous_point) | point_id != previous_point) %>%
  ungroup()

# Teeme punktist-punkti liikumised
paths <- logs_compact %>%
  arrange(visitor_id, timestamp) %>%
  group_by(visitor_id) %>%
  mutate(
    next_point = lead(point_id),
    next_time = lead(timestamp),
    seconds_to_next = as.numeric(difftime(next_time, timestamp, units = "secs"))
  ) %>%
  ungroup() %>%
  filter(!is.na(next_point)) %>%
  filter(seconds_to_next > 0, seconds_to_next < 3600)

write_csv(paths, "data_clean/visitor_paths.csv")

print("Salvestatud: data_clean/visitor_paths.csv")
print(paste("Algseid logiridu:", nrow(logs)))
print(paste("Kompaktseid külastuspunkti ridu:", nrow(logs_compact)))
print(paste("Teekonnalõike:", nrow(paths)))

print(
  paths %>%
    count(point_id, next_point, sort = TRUE) %>%
    head(20)
)