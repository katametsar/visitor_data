suppressPackageStartupMessages(library(tidyverse))
suppressPackageStartupMessages(library(lubridate))

logs <- read_csv("~/ERM/data_clean/logs_with_devices.csv", show_col_types = FALSE)

usage <- logs %>%
  filter(!is.na(point_id)) %>%
  mutate(
    timestamp = dmy_hms(time_raw),
    date = as_date(timestamp),
    hour = hour(timestamp),
    weekday = wday(timestamp, label = TRUE, week_start = 1),
    visitor_id = card_hex
  )

# 1. Punktide kasutus
point_usage <- usage %>%
  count(point_id, topic, sort = TRUE)

# 2. Päevade kasutus
daily_usage <- usage %>%
  count(date, name = "interactions")

# 3. Unikaalsed külastajad päevas
daily_visitors <- usage %>%
  distinct(date, visitor_id) %>%
  count(date, name = "visitors")

# 4. Tunnipõhine kasutus
hourly_usage <- usage %>%
  count(hour, name = "interactions")

# 5. Nädalapäevade kasutus
weekday_usage <- usage %>%
  count(weekday, name = "interactions")

dir.create("outputs", showWarnings = FALSE)

write_csv(point_usage, "~/ERM/outputs/point_usage.csv")
write_csv(daily_usage, "~/ERM/outputs/daily_usage.csv")
write_csv(daily_visitors, "~/ERM/outputs/daily_visitors.csv")
write_csv(hourly_usage, "~/ERM/outputs/hourly_usage.csv")
write_csv(weekday_usage, "~/ERM/outputs/weekday_usage.csv")

print("Valmis. Salvestatud outputs kausta:")
print("point_usage.csv")
print("daily_usage.csv")
print("daily_visitors.csv")
print("hourly_usage.csv")
print("weekday_usage.csv")

print("Top 20 enim kasutatud punkti:")
print(head(point_usage, 20))