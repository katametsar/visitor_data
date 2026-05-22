## Access & allowed use

This dataset is provided for:

- hackathon research and prototyping  
- visualizations and models  
- presentations and demo publications  

Not allowed:

- commercial reuse  
- re-publishing raw data outside this repository  
- attempts to identify individual visitors  
- combining the data with other datasets for deanonymization  

---

## Citation requirement

Estonian National Museum. *Encounters exhibition interactive ticket log dataset*, 2026.

---

## Data structure

Main files:

- `log_m-y.log` – interaction logs (plain text)  
- `device_id.xlsx` – mapping of devices and interaction points to exhibition locations and topics
- `cards-languages.csv` - language id's

Format:

- logs: plain text  
- mapping: structured table (XLSX / CSV)  

Encoding: UTF-8  

---

## Row represents

One interaction event recorded by the system.

Not:

- one complete visit  
- one individual visitor  
- one exhibition object  
- a direct statement of visitor intent  

A visit must be reconstructed from a sequence of events.

---

## Example row
[01/Mar/2020:11:13:11 +0200] 00:18:2d:00:17:bf/0: 04000000045e5b7c10 e0040150ca2bd886


---

## Key fields

| Field | Meaning | Notes |
|------|--------|------|
| timestamp | time of event | includes timezone |
| device_id | sensor / reader identifier | maps to exhibition location |
| channel_flag | technical state indicator | system-level value |
| ticket_id | anonymized ticket identifier | used to reconstruct visits |
| interaction_id | interaction target | may correspond to exhibit |

---

## Interpreting visits and movement

The dataset does not explicitly define visits or movement.  
These must be inferred from `ticket_id` and timestamps.

This enables:

- reconstruction of visit sessions  
- ordering of events in time  
- estimation of visit duration  
- analysis of movement paths  

Important:

- sessions are inferred, not explicit  
- movement is indirect (event-based)  
- absence of events ≠ absence of activity  

---

## Interaction and content use

Some events reflect interaction with system content (e.g. language selection or media access).

This allows analysis of:

- language-switching behavior  
- interaction intensity  
- content engagement patterns  

These logs reflect system interaction, not the full visitor experience.

---

## Temporal analysis

Each event is time-stamped, enabling:

- visit duration analysis  
- time-of-day patterns  
- weekday vs weekend comparison  
- seasonal variation  

---

## Mapping file (device_id.xlsx)

The logs contain only technical identifiers.  
To interpret them, a separate mapping file is required.

This file links `device_id` values to:

- interaction points (e.g. `T01.01.01-E1`)  
- installations (`T01.01.01-V1`)  
- exhibition topics  

### Identifier structure

- `E` → individual interaction element  
- `V` → grouped installation  

Multiple `E` elements may belong to one `V`.

This supports analysis at:

- interaction level  
- installation level  

---

## Example interpretation

`device_id = 00:18:2d:00:17:bf`

→ `T01.01.01-E1`  
→ `T01.01.01-V1`  
→ topic: *#Estonianmafia ja e-Eesti*  