import os
import plotly.graph_objects as go
import plotly.io as pio

# Reference processing types and color map (updated to match grouped bar chart style)
PROCESSING_TYPE_COLORS = {
    "Beneficiation": "#fed976",
    "Early refining": "#fb6a4a",
    "Precursor related product": "#7f0000"
}

REFERENCE_MINERALS = ["cobalt", "copper", "graphite", "lithium", "manganese", "nickel"]
REFERENCE_MINERALS_SHORT = ["Co", "Cu", "Gr", "Li", "Mn", "Ni"]
REFERENCE_MINERAL_COLORS = ["#fdae61", "#f46d43", "#66c2a5", "#c2a5cf", "#fee08b", "#3288bd"]

REFERENCE_MINERAL_COLORMAP = dict(zip(REFERENCE_MINERALS, REFERENCE_MINERAL_COLORS))
REFERENCE_MINERAL_NAMEMAP = dict(zip(REFERENCE_MINERALS, REFERENCE_MINERALS_SHORT))
REFERENCE_MINERAL_COLORMAPSHORT = dict(zip(REFERENCE_MINERALS_SHORT, REFERENCE_MINERAL_COLORS))

def get_processing_type_colors():
    return PROCESSING_TYPE_COLORS

def get_mineral_colors():
    return REFERENCE_MINERAL_COLORMAP

def get_mineral_colors_short():
    return REFERENCE_MINERAL_COLORMAPSHORT

def generate_country_colormap(iso3_list):
    sorted_countries = sorted(iso3_list)
    color_palette = plt.cm.tab20.colors
    repeats = -(-len(sorted_countries) // len(color_palette))  # ceiling division
    full_palette = (color_palette * repeats)[:len(sorted_countries)]
    return dict(zip(sorted_countries, full_palette))

def annotate_stacked_bars(ax, pivot, min_display_frac=0.05, orientation='horizontal'):
    if orientation == 'horizontal':
        limit = ax.get_xlim()[1]
        for i, index in enumerate(pivot.index):
            cumulative = 0
            for col in pivot.columns:
                value = pivot.loc[index, col]
                if value > min_display_frac * limit:
                    ax.text(
                        cumulative + value / 2,
                        i,
                        str(col),
                        ha='center',
                        va='center',
                        fontsize=10,
                        color='white',
                        fontweight='bold'
                    )
                cumulative += value
    else:
        limit = ax.get_ylim()[1]
        for i, index in enumerate(pivot.columns):
            cumulative = 0
            for row in pivot.index:
                value = pivot.loc[row, index]
                if value > min_display_frac * limit:
                    ax.text(
                        i,
                        cumulative + value / 2,
                        str(row),
                        ha='center',
                        va='center',
                        fontsize=10,
                        color='white',
                        fontweight='bold'
                    )
                cumulative += value

def format_legend(ax, fontsize=12, title_fontsize=13, loc="upper left", outside=True, ncol=1, title="Mineral"):
    bbox = (1.01, 1) if outside else None
    ax.legend(
        title=title,
        loc=loc,
        fontsize=fontsize,
        title_fontsize=title_fontsize,
        bbox_to_anchor=bbox,
        ncol=ncol
    )
    
def apply_plot_layout(fig, title="", barmode="group"):
    fig.update_layout(
        title=title,
        title_font_size=18,
        barmode=barmode,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=40, r=20, t=60, b=40),
        font=dict(size=12)
    )

def save_plot(fig, filepath):
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    pio.write_image(fig, filepath, format="png", width=1000, height=600, scale=2)
