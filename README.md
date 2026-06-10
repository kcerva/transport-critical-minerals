# Quantifying Critical Mineral Value Chains Opportunities

This repo models global transport flows of critical minerals, and brings together results from production, energy requirements and environmental implications. The study has first been applied to 14 African countries and 6 battery minerals (cobalt, copper, graphite, nickel, manganese and lithium). The analysis focuses on mineral production and battery commodity manufacturing, transport flows, transport costs, CO₂ emissions, electricity requirements, electricity costs, water use, and economic impacts (export revenues, GDP share) across policy scenarios combining different mineral processing ambition levels, resource nationalist or regionalist policies, and demand projections.

## Prerequisites

```bash
micromamba activate myenv
pip install -r scripts/automated_plot/requirements.txt
```

## Configuration

Copy the template and set your local paths:

```bash
cp config.template.json config.json
```

Edit `config.json` to point to your local directories:

| Key | Description |
|---|---|
| `incoming_data` | Raw input data (provided externally) |
| `data` | Working data files |
| `figures` | Output figures and plots |
| `scratch` | Temporary working files |
| `results` | Analysis results, CSVs, pivot tables, reports |

The outputs folder (`transport-outputs/`) lives **outside** the repo and is not committed to git.

## Input data

The main input is `results/all_data.xlsx`, generated from `combined_transport_totals_by_stage.xlsx` (produced by the flow modelling pipeline, run by others). A version with filled production costs is at `results/all_data_filled_costs.xlsx`.

## Running the analysis

**Run all publication figures:**
```bash
python scripts/automated_plot/run_all_figures.py
```

**Run a specific figure group:**
```bash
python scripts/automated_plot/run_all_figures.py --group publication
python scripts/automated_plot/run_all_figures.py --plots figure_economic_indicators
```

**Net export revenue pipeline** (run in order):
```bash
python scripts/automated_plot/consolidate_tonnage_flows.py      # → tonnage_flows_comprehensive.xlsx
python scripts/automated_plot/fill_missing_production_costs.py  # → all_data_filled_costs.xlsx
python scripts/automated_plot/merge_prices_with_flows.py        # → tonnage_flows_with_revenues.xlsx
```

## Outputs

| Location | Contents |
|---|---|
| `results/all_data.xlsx` | Main analysis file |
| `results/tonnage_flows_with_revenues.xlsx` | Net export revenue calculations |
| `results/pivot_tables/` | Country-specific pivot files (e.g. `all_data_pivots_AGO.xlsx`) |
| `results/country_reports/` | Per-country DOCX reports and dashboards |
| `figures/` | All generated plots (PNG and PDF) |

## Repo structure

| Directory | Description |
|---|---|
| `scripts/automated_plot/` | **Our primary work area** — visualisations, pivot tables, reports |

| `scripts/flow_modelling/` | Transport flow modelling and optimisation — run by others |
| `scripts/preprocess/` | Data preprocessing — run by others |

> `scripts/plot/` contains outdated scripts — use `scripts/automated_plot/` instead.

## Applications
This repo has been used to create the analysis in the following publications:

Cervantes Barron, K., Pant, R., Andrieu, B., Heydari, M., Korkovelos, A., Osei-Owusu, S., Barzin, S., Ciftci, M.M., Stringer, M., Gomez, C.R., Hawkes, A., Hall, J., Foster, V., 2026. Nationalist versus regional approaches for increased battery mineral value addition in Southern Africa. https://doi.org/10.21203/rs.3.rs-9179870/v1 (Under review in Nature Communications)

Foster, V., Cervantes Barron, K., Pant, R., Andrieu, B., Heydari, M., Osei-Owusu, S., Barzin, S., Ciftci, M., Stringer, M., Gomez, C.R., Verdin, G.C., Hawkes, A., Hall, J.W., 2026. Beyond Extraction: Simulating Increased Battery Mineral Value Addition in Southern Africa - Policy Brief (Policy Brief). Climate Compatible Growth. https://climatecompatiblegrowth.com/wp-content/uploads/Policy-Brief-Battery-Minerals-Southern-Africa_260126.pdf 

