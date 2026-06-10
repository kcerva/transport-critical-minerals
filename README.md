# transport-critical-minerals

Models global transport flows of critical minerals with a focus on African countries. Analyses transport costs, CO₂ emissions, water use, and economic impacts (value addition, net export revenue, GDP share) across policy scenarios combining different processing ambition levels, trade policies, and demand projections.

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
