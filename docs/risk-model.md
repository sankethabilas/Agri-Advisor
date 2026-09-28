# Weather Risk Model

The weather agent computes transparent rule-based scores from current temperature, relative humidity, and rainfall. Scores are clamped to $[0, 1]$ and mapped to response levels as follows. The task examples call the $0.60$ level “Medium”; this API uses the contract label “Moderate” for the same band.

| Score | Level |
| --- | --- |
| $0.95$ to $1.00$ | Critical |
| $0.85$ to $0.94$ | High |
| $0.60$ to $0.84$ | Moderate |
| Below $0.60$ | Low |

## Disease Risk

| Condition | Score contribution |
| --- | ---: |
| Temperature from 20 C through 32 C | 0.25 |
| Relative humidity at least 80% | 0.35 |
| Current rainfall at least 5 mm | 0.25 |
| Both warm temperature and high humidity | 0.25 additional |

Warm, high-humidity conditions therefore score $0.85$ (High), prompting crop inspection within 24 hours. Rainfall can increase the score further, up to 1.00.

## Pest Risk

| Condition | Score contribution |
| --- | ---: |
| Temperature from 25 C through 35 C | 0.35 |
| Relative humidity from 60% through 85% | 0.25 |
| Current rainfall below 5 mm | 0.25 |

Warm, moderately humid, dry conditions score $0.85$ (High). Recommendations prioritize scouting and cultural or physical control rather than automatic pesticide use.

## Forecast Alerts and Spray Safety

| Forecast condition | Alert |
| --- | --- |
| At least 25 mm cumulative rainfall in the next three forecast days | Heavy rain (`watch`); `warning` at 50 mm |
| At least 50 mm rainfall in any of the next three days | Flood (`emergency`) |
| Forecast wind speed at least 40 km/h | High wind (`warning`) |
| Forecast daily maximum temperature at least 38 C | Extreme heat (`warning`) |

BR-12: when a heavy-rain alert is active, pesticide applications are deferred until rain has passed and foliage is dry. Disease-risk recommendations switch to drainage, inspection, and sanitation actions; the advisory does not suggest spraying during the rain window.

These are explicit operational assumptions for this implementation, not calibrated epidemiological models. Risk scores are indicators for field scouting and should not be treated as disease diagnoses.