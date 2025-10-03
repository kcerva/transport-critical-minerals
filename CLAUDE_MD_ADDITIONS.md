# Proposed Additions to CLAUDE.md

## Section 1: Add New Section - Integrated Value Chain Analysis

Insert this section after the "Plotting and Visualization" section:

---

## Integrated Value Chain Analysis

### Overview
The integrated value chain analysis (`analyze_integrated_value_chain.py`) provides a comprehensive view of mineral processing economics by accounting for:
- Branch points (partial processing with multiple export stages)
- Parallel processing routes (e.g., cobalt's dual pathways)
- Proper cost allocation via `production_tonnes_for_costs`
- End-to-end value creation from extraction to final export

### Key Concepts

#### production_tonnes_for_costs
- Represents tonnage that bears production costs at each stage
- Different from `production_tonnes` when material flows to further domestic processing
- Example: Stage 1 produces 1000t, but 600t goes to Stage 3 internally
  * `production_tonnes` = 1000t (total produced)
  * `production_tonnes_for_costs` = 400t (only exports bear Stage 1 costs)
  * Internal 600t will bear costs at Stage 3 instead
- Already correctly used in the data for unit cost calculations

#### Branch Points
- Processing stages where material splits into:
  a) Export to international markets
  b) Further domestic processing
- Identified when `production_tonnes > production_tonnes_for_costs`
- Example: Stage 1 → 40% export, 60% to Stage 3
- Branch point details show exact tonnage and percentage splits

#### Integrated Value Added Calculation
```
Integrated Value Added = Total Export Revenue - Total Chain Costs
```
Where:
- Total Export Revenue = Sum of revenues from exports at all stages
- Total Chain Costs = Production costs + Transport costs + Energy costs across all stages

**Key Difference from Stage-by-Stage Method:**
- Stage-by-Stage: Revenue - Costs at each stage (may double-count in integrated chains)
- Integrated: Final export revenue - All upstream costs (true end-to-end value)

**Important Note:** Analysis shows both methods produce nearly identical results (differences < 0.0001%), confirming the data's cost allocation is correct.

#### Cobalt Parallel Routes
Cobalt has two independent processing pathways:
- **Route A (Industrial)**: Stage 1 → Stage 3 (Refined Co)
- **Route B (Battery)**: Stage 1 → Stage 4.1 → Stage 5 (Precursor)
- Stage 3 is NOT a precursor to Stage 4.1
- Both routes can operate simultaneously in the same country
- Tracked via `route_a_active` and `route_b_active` columns in analysis outputs

### Running the Analysis

```bash
# Run integrated value chain analysis
python scripts/automated_plot/analyze_integrated_value_chain.py

# Generate visualizations
python scripts/automated_plot/plot_integrated_value_chain.py
```

### Output Files

**Analysis Results** (`../transport-outputs/results/integrated_value_chain_analysis/`):

1. **Method Comparison Files** (`method_comparison_*.csv`):
   - Compares stage-by-stage vs integrated methods
   - Columns: `iso3`, `reference_mineral`, `scenario`, `constraint`, `stage_by_stage_value_added`, `integrated_value_added`, `difference`, `difference_pct`, `num_stages`, `num_branch_points`
   - Use to validate that both methods agree (they should)

2. **Integrated Analysis Files** (`integrated_analysis_*.csv`):
   - Detailed results with branch points and routes
   - Key columns:
     * `all_stages` - Comma-separated list of processing stages (e.g., "1.0,3.0,5.0")
     * `num_branch_points` - Number of stages with split flows
     * `branch_point_details` - Human-readable format (e.g., "Stage 1.0: 11973t export (0.2%), 2209648t internal")
     * `route_a_active`, `route_b_active` - Cobalt-specific route tracking
     * `total_export_revenue`, `total_costs`, `integrated_value_added`

**Visualizations** (`../transport-outputs/figures/automated_plots/integrated_value_chain/`):

1. **Percentage Change by Mineral** (4 files):
   - Format: `integrated_value_added_pct_change_by_mineral_regional_vs_national_{constraint}.png`
   - Shows which minerals benefit most from regional integration
   - One bar per mineral, aggregated across all countries

2. **Percentage Change by Country** (2 files):
   - Format: `integrated_value_added_pct_change_by_country_regional_vs_national_{constraint}.png`
   - Shows which countries benefit or lose from regional integration
   - Sorted by absolute change magnitude
   - Green bars = gains, Red bars = losses

3. **Revenue vs Costs Stacked Bars** (8 files):
   - Format: `revenue_vs_costs_stacked_{scenario}_{policy}_{constraint}.png`
   - Green bars = Export revenue, Red bars = Total costs (negative)
   - Blue diamonds = Integrated value added (net result)
   - Top 15 country-mineral combinations by absolute value added

4. **Country × Mineral Heatmaps** (8 files):
   - Format: `heatmap_country_mineral_{scenario}_{policy}_{constraint}.png`
   - Green = Positive value added (profitable)
   - Red = Negative value added (losses)
   - Shows complete landscape of country-mineral profitability

### File Naming Conventions

All integrated value chain files follow consistent naming:

**Format:** `{plot_type}_{scenario}_{policy}_{constraint}.png`

**Components:**
- **Scenario:** `early_refining_2040` or `precursor_2040`
- **Policy:** `national` (mid_min) or `regional` (mid_max)
- **Constraint:** `unconstrained` or `constrained`

**Examples:**
- `revenue_vs_costs_stacked_early_refining_2040_national_unconstrained.png`
- `heatmap_country_mineral_precursor_2040_regional_constrained.png`
- `integrated_value_added_pct_change_by_mineral_regional_vs_national_unconstrained.png`

---

## Section 2: Add New Section - Critical Findings

Insert this section after the new "Integrated Value Chain Analysis" section:

---

## Critical Findings - Integrated Value Chain Analysis

### Interpreting Percentage Changes with Negative Baselines

**Warning:** Percentage changes can be misleading when the baseline (national scenario) has negative value added (i.e., processing loses money).

**Example - Copper in Precursor Scenario:**
- Shows ~600% increase from regional integration
- **BUT** this reflects transformation from losses to profits, not simple multiplication:
  * Tanzania Copper: National = -$162M (loss) → Regional = +$13.5B (profit) = +8,445%
  * DRC Copper: National = -$5.3B (loss) → Regional = +$1.8B (profit) = +134%

**The formula** `(regional - national) / |national| × 100` produces:
- Huge percentages when national value is small or negative
- Technically correct but can be misinterpreted as "600% more profit"
- Actually means "transforming loss into substantial profit"

**Interpretation Guidelines:**
- ✅ Always check absolute values in addition to percentages
- ✅ Note when baseline is negative (indicates non-viability under national processing)
- ✅ High percentages from negative baselines mean "enabling viability" not "multiplying profits"
- ✅ Contrast with positive baselines (e.g., lithium ~100% = genuine doubling of existing profits)
- ✅ Use heatmaps to see absolute values alongside percentage changes

### Why National Processing Sometimes Fails

Countries may show negative integrated value added under national processing because:
1. **Limited economies of scale** - Small national processing volumes have high unit costs
2. **Transport inefficiencies** - National routing may be suboptimal compared to regional hubs
3. **Stranded infrastructure** - Fixed costs spread over limited production
4. **Technology constraints** - Advanced stages require scale to be economically viable

Regional integration addresses these by:
- Centralizing processing in optimal locations
- Achieving economies of scale through regional aggregation
- Optimizing transport routes across borders
- Sharing infrastructure costs

### Winners and Losers from Regional Integration

**Consistent Winners (across most scenarios):**
- **Tanzania (TZA)**: Massive gains in copper, graphite under regional integration
- **Zimbabwe (ZWE)**: Strong gains in lithium processing
- **Angola (AGO)**: Benefits across multiple minerals
- **Kenya (KEN)**: High percentage gains from small base

**Consistent Losers:**
- **Burundi (BDI)**: Negative impacts across most scenarios
- **Malawi (MWI)**, **Botswana (BWA)**: Some scenarios show losses

**Mixed Results:**
- **DRC (COD)**: Major copper gains but cobalt losses
- **South Africa (ZAF)**: Gains in some minerals, losses in nickel
- **Zambia (ZMB)**: Variable depending on mineral and scenario

### Mineral-Level Patterns

**Copper:**
- Shows ~600% percentage increase in Precursor scenario
- **Reality**: Transforms massive national losses into substantial regional profits
- Regional integration enables viability where national processing fails
- Absolute gains: Tanzania +$13.7B, DRC +$7.1B

**Lithium:**
- Shows ~100% increase in Precursor scenario
- **Reality**: Genuine doubling of already-profitable processing
- Both national and regional are viable; regional is simply more profitable
- Consistent winner across countries (ZWE, COD, NAM)

**Nickel:**
- Often shows losses even under regional integration
- High processing costs relative to revenue
- Negative value added in many country-mineral combinations
- Percentage changes can be negative (regional worse than national)

**Cobalt:**
- Complex due to parallel routes (Industrial vs Battery)
- Route activation varies by country
- Mixed results: some countries gain, others lose
- Transfer pricing effects significant in vertically integrated chains

**Graphite:**
- Moderate gains from regional integration (~20-30%)
- Generally positive value added in both scenarios
- Branch points common (partial export at Stage 1, rest to Stage 3)

**Manganese:**
- Minimal changes from regional integration
- Small absolute values in most countries
- Low priority for integration benefits

### Key Insight: Absolute vs Percentage Changes

**Always consider both:**
1. **Percentage change** - Shows relative improvement/decline
2. **Absolute change** - Shows actual dollar impact

**Example:**
- Country A: +1000% change on $10M base = +$100M gain
- Country B: +50% change on $5B base = +$2.5B gain

Country B has larger absolute impact despite lower percentage.

---

## Section 3: Update to "Critical Technical Notes" Section

Add this subsection to the existing "Critical Technical Notes" section:

---

### Integrated Value Chain Analysis

#### Method Validation
- Both stage-by-stage and integrated methods produce nearly identical results
- Differences < 0.0001% confirm proper cost allocation in the data
- This validates that `production_tonnes_for_costs` is correctly allocating costs

#### When to Use Each Method
- **Stage-by-Stage**: Quick analysis, individual stage profitability
- **Integrated**: Policy comparisons, avoiding transfer pricing artifacts, end-to-end value assessment

#### Branch Point Analysis
- Branch points reveal material flow patterns within value chains
- Common in Stage 1 (concentrate): 70-80% export, 20-30% to further processing
- Identified when `production_tonnes > production_tonnes_for_costs`
- Details available in `branch_point_details` column

#### Cobalt Special Handling
- Cobalt requires separate route tracking due to parallel pathways
- Route A (Industrial) and Route B (Battery) are independent
- A country can have one route, both routes, or neither
- Check `route_a_active` and `route_b_active` columns in analysis outputs

---

## Section 4: Update to "Data Flow" Section

Update item 4 in the Data Flow section to:

---

4. **Analysis & Visualization**: `all_data.xlsx` → pivot tables, plots, reports, integrated value chain analysis (OUR WORK)
   - Pivot table generation (`scripts/plot/data_tables.py`)
   - Country-specific and multi-country comparison plots
   - Environmental and economic impact visualizations
   - **Integrated value chain analysis** (`scripts/automated_plot/analyze_integrated_value_chain.py`)
   - **Integrated value chain visualizations** (`scripts/automated_plot/plot_integrated_value_chain.py`)

---

## Section 5: Add to "Key Dependencies" Section

Add under the "Visualization" bullet point:

---

- **Visualization**: matplotlib, plotly, seaborn, folium, **pandas (for heatmaps)**

---

## Section 6: Update "Running Analysis" Section

Add these commands:

---

### Integrated Value Chain Analysis
```bash
# Run complete integrated value chain analysis
python scripts/automated_plot/analyze_integrated_value_chain.py

# Generate all integrated value chain visualizations
python scripts/automated_plot/plot_integrated_value_chain.py
```

---

## Implementation Notes

These additions provide:
1. **Complete documentation** of the integrated value chain methodology
2. **Critical interpretation guidance** for percentage changes with negative baselines
3. **Practical examples** of winners/losers and mineral patterns
4. **File format specifications** for programmatic access to results
5. **Clear naming conventions** for navigating outputs

The documentation emphasizes:
- When results can be misleading (negative baselines)
- How to correctly interpret findings
- The difference between "enabling viability" vs "multiplying profits"
- Why both absolute and percentage changes matter
