suppressPackageStartupMessages(library(tidyverse))
suppressPackageStartupMessages(library(lubridate))

daily_usage <- read_csv(
  "outputs/daily_usage.csv",
  show_col_types = FALSE
) %>%
  mutate(date = as_date(date)) %>%
  arrange(date)

# Täiendame ajatelje kõigi kuupäevadega.
# Oluline: puuduvad päevad jäävad NA, mitte 0.
# See tähendab "andmed puuduvad", mitte "külastusi polnud".
daily_complete <- daily_usage %>%
  complete(
    date = seq(min(date), max(date), by = "day")
  ) %>%
  mutate(
    has_data = !is.na(interactions)
  )

dir.create("outputs", showWarnings = FALSE)

# 1. Graafik: ainult olemasolevad andmepunktid
p_points <- ggplot(daily_complete, aes(x = date, y = interactions)) +
  geom_point(
    data = daily_complete %>% filter(has_data),
    alpha = 0.55,
    size = 0.8
  ) +
  geom_smooth(
    data = daily_complete %>% filter(has_data),
    method = "loess",
    se = FALSE,
    linewidth = 0.8
  ) +
  labs(
    title = "Päevane interaktsioonide arv",
    subtitle = "Puuduvad kuupäevad on jäetud tühjaks; neid ei tõlgendata nullkasutusena",
    x = "Kuupäev",
    y = "Interaktsioonide arv"
  ) +
  theme_minimal()

ggsave(
  "outputs/daily_usage_points.png",
  plot = p_points,
  width = 13,
  height = 6
)

# 2. Graafik: katkestatud joon ainult järjestikuste olemasolevate päevade kohta
daily_segments <- daily_complete %>%
  mutate(
    gap = is.na(interactions),
    segment_id = cumsum(gap)
  ) %>%
  filter(!gap)

p_line <- ggplot(daily_segments, aes(x = date, y = interactions, group = segment_id)) +
  geom_line(linewidth = 0.4) +
  geom_point(size = 0.6, alpha = 0.5) +
  labs(
    title = "Päevane interaktsioonide arv katkestatud ajateljel",
    subtitle = "Joon ei ühenda perioode, mille vahel logiandmed puuduvad",
    x = "Kuupäev",
    y = "Interaktsioonide arv"
  ) +
  theme_minimal()

ggsave(
  "outputs/daily_usage_discontinuous_line.png",
  plot = p_line,
  width = 13,
  height = 6
)

# 3. Andmekatvuse kokkuvõte
coverage_summary <- daily_complete %>%
  summarise(
    first_date = min(date),
    last_date = max(date),
    total_days_in_range = n(),
    days_with_logs = sum(has_data),
    days_without_logs = sum(!has_data),
    coverage_percent = round(days_with_logs / total_days_in_range * 100, 1)
  )

write_csv(
  daily_complete,
  "outputs/daily_usage_complete_calendar.csv"
)

write_csv(
  coverage_summary,
  "outputs/daily_usage_coverage_summary.csv"
)

print("Salvestatud:")
print("outputs/daily_usage_points.png")
print("outputs/daily_usage_discontinuous_line.png")
print("outputs/daily_usage_complete_calendar.csv")
print("outputs/daily_usage_coverage_summary.csv")

print("Andmekatvuse kokkuvõte:")
print(coverage_summary)