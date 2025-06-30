
import matplotlib.pyplot as plt

def annotate_stacked_bars(ax, pivot, min_display_frac=0.05, orientation='horizontal'):
    """
    Annotates bars in a stacked bar chart using the pivot table directly.

    Parameters:
        ax : matplotlib axis with the bar plot
        pivot : pivot table (index = y-axis category, columns = stacked categories)
        min_display_frac : minimum fraction of axis limit required to annotate
        orientation : 'horizontal' or 'vertical'
    """
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

def generate_country_colormap(iso3_list):
    sorted_countries = sorted(iso3_list)
    color_palette = plt.cm.tab20.colors
    repeats = -(-len(sorted_countries) // len(color_palette))  # ceiling division
    full_palette = (color_palette * repeats)[:len(sorted_countries)]
    return dict(zip(sorted_countries, full_palette))

def format_legend(ax, fontsize=12, title_fontsize=13, loc="upper left", outside=True, ncol=1, title="Mineral"):
    """
    Formats the legend of a matplotlib axis.

    Parameters:
        ax : matplotlib axis
        fontsize : legend label font size
        title_fontsize : legend title font size
        loc : legend location
        outside : place legend outside of plot
        ncol : number of legend columns
        title : legend title
    """
    bbox = (1.01, 1) if outside else None
    ax.legend(
        title=title,
        loc=loc,
        fontsize=fontsize,
        title_fontsize=title_fontsize,
        bbox_to_anchor=bbox,
        ncol=ncol
    )
