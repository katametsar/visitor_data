suppressPackageStartupMessages(library(tidyverse))
suppressPackageStartupMessages(library(readxl))

logs <- read_csv("~/ERM/data_clean/parsed_logs.csv", show_col_types = FALSE)

devices <- read_excel(
  "~/ERM/data_raw/Device_id.xlsx",
  sheet = "kõik logid"
)

print(names(devices))
print(head(devices, 10))

devices_clean <- devices %>%
  select(
    point_id = Name,
    device_id = Device,
    topic = Topic,
    regroup_1 = `Regrouping of "names", vol 1`,
    regroup_2 = `Regrouping of "names", vol 2`
  ) %>%
  filter(!is.na(device_id))

logs_with_devices <- logs %>%
  left_join(devices_clean, by = "device_id")

print("Logiridu kokku:")
print(nrow(logs_with_devices))

print("Mitu logirida sai näitusepunkti külge:")
print(sum(!is.na(logs_with_devices$point_id)))

print("Mitu jäi ühendamata:")
print(sum(is.na(logs_with_devices$point_id)))

print(head(logs_with_devices, 10))

write_csv(
  logs_with_devices,
  "~/ERM/data_clean/logs_with_devices.csv"
)

print("Salvestatud: ~/ERM/data_clean/logs_with_devices.csv")