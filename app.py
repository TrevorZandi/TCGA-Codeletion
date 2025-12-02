"""
Dash application for interactive co-deletion analysis visualization.

This app loads pre-processed co-deletion data and provides interactive
controls for exploring conditional co-deletion probabilities.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from dash import Dash, Input, Output, State, html
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from layouts import create_layout, create_stats_display
from data import processed_loader
from visualization import codeletion_heatmap


# Initialize Dash app
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="Chromosome Co-Deletion Analysis"
)

# Set the layout
app.layout = create_layout()


# Callback: Populate study dropdown with available studies and set default
@app.callback(
    [Output('study-dropdown', 'options'),
     Output('study-dropdown', 'value')],
    Input('study-dropdown', 'id')  # Trigger on page load
)
def populate_study_dropdown(_):
    """
    Populate the study dropdown with available processed studies and set initial value.
    
    Returns:
        Tuple of (options list, default value)
    """
    available_studies = processed_loader.list_available_studies()
    
    if not available_studies:
        return [{'label': 'No studies processed yet - Run batch_process.py', 'value': 'none'}], 'none'
    
    # Create human-readable labels
    options = []
    for study_id in available_studies:
        # Convert study_id to readable name
        label = study_id.replace('_tcga_pan_can_atlas_2018', '').replace('_', ' ').upper()
        options.append({'label': label, 'value': study_id})
    
    # Set default to PRAD if available, otherwise first study
    default_value = 'prad_tcga_pan_can_atlas_2018' if 'prad_tcga_pan_can_atlas_2018' in available_studies else available_studies[0]
    
    return options, default_value


# Callback: Update heatmap based on controls
@app.callback(
    Output('codeletion-heatmap', 'figure'),
    [
        Input('colorscale-dropdown', 'value'),
        Input('n-labels-slider', 'value'),
        Input('study-dropdown', 'value')
    ]
)
def update_heatmap(colorscale, n_labels, study_id):
    """
    Update the heatmap visualization based on user selections.
    
    Args:
        colorscale: Selected colorscale name
        n_labels: Number of axis labels to display
        study_id: Selected study identifier
        
    Returns:
        Updated Plotly figure
    """
    # Handle None or empty study_id
    if study_id is None or study_id == 'none':
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No processed data available.<br>Run batch_process.py to generate data.",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Load processed data for selected study
    conditional_matrix = processed_loader.load_conditional_matrix(
        chromosome="13", 
        study_id=study_id
    )
    
    # Load gene metadata for cytoband labels
    try:
        gene_metadata = processed_loader.load_gene_metadata(
            chromosome="13",
            study_id=study_id
        )
        cytobands = gene_metadata["cytoband"].tolist()
    except FileNotFoundError:
        # Fallback to gene names if metadata not available
        cytobands = None
    
    # Extract study name for title
    study_name = study_id.replace('_tcga_pan_can_atlas_2018', '').replace('_', ' ').upper()
    
    # Create figure
    fig = codeletion_heatmap.create_heatmap_figure(
        mat=conditional_matrix,
        title=f"Chr13 Conditional Co-Deletion Matrix - {study_name}",
        colorscale=colorscale,
        cytobands=cytobands,
        n_labels=n_labels
    )
    
    return fig


# Callback: Update top pairs bar plot
@app.callback(
    Output('top-pairs-barplot', 'figure'),
    [
        Input('n-pairs-slider', 'value'),
        Input('study-dropdown', 'value')
    ]
)
def update_top_pairs(n_pairs, study_id):
    """
    Update the top pairs bar plot based on selected number of pairs.
    
    Args:
        n_pairs: Number of top pairs to display
        study_id: Selected study identifier
        
    Returns:
        Updated Plotly figure
    """
    # Handle None or empty study_id
    if study_id is None or study_id == 'none':
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Load co-deletion pairs data for selected study
    pairs_data = processed_loader.load_codeletion_pairs(
        chromosome="13",
        study_id=study_id
    )
    
    # Create figure
    fig = codeletion_heatmap.create_top_pairs_figure(
        long_table=pairs_data,
        n=n_pairs
    )
    
    return fig


# Callback: Update deletion frequency scatter plot
@app.callback(
    Output('deletion-frequency-scatter', 'figure'),
    Input('study-dropdown', 'value')
)
def update_deletion_scatter(study_id):
    """
    Update the deletion frequency scatter plot for the selected study.
    
    Args:
        study_id: Selected study identifier
        
    Returns:
        Updated Plotly figure
    """
    # Handle None or empty study_id
    if study_id is None or study_id == 'none':
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Load deletion frequencies
    deletion_freqs = processed_loader.load_deletion_frequencies(
        chromosome="13",
        study_id=study_id
    )
    
    # Load gene metadata for cytoband ordering
    try:
        gene_metadata = processed_loader.load_gene_metadata(
            chromosome="13",
            study_id=study_id
        )
    except FileNotFoundError:
        gene_metadata = None
    
    # Create figure
    fig = codeletion_heatmap.create_deletion_frequency_scatter(
        deletion_freqs=deletion_freqs,
        gene_metadata=gene_metadata
    )
    
    return fig


# Callback: Update dataset statistics
@app.callback(
    Output('stats-display', 'children'),
    Input('study-dropdown', 'value')
)
def update_stats(study_id):
    """
    Update the statistics display with dataset information.
    
    Args:
        study_id: Selected study identifier
        
    Returns:
        HTML component with statistics
    """
    # Handle None or empty study_id
    if study_id is None or study_id == 'none':
        return html.Div([
            html.P("No processed data available.", className="text-muted")
        ])
    
    # Load data to get stats for selected study
    conditional_matrix = processed_loader.load_conditional_matrix(
        chromosome="13",
        study_id=study_id
    )
    
    # Calculate basic stats
    n_genes = conditional_matrix.shape[0]
    
    # Try to get more detailed stats from pairs data
    try:
        pairs_data = processed_loader.load_codeletion_pairs(
            chromosome="13",
            study_id=study_id
        )
        max_codeletions = int(pairs_data['co_deletion_frequency'].max()) if len(pairs_data) > 0 else 0
    except:
        max_codeletions = 0
    
    # Create stats display
    # Note: n_samples would need to be extracted from the data
    stats_html = create_stats_display(
        n_genes=n_genes,
        n_samples=conditional_matrix.shape[0],  # Approximation
        n_deletions=max_codeletions
    )
    
    return stats_html


# Run the app
if __name__ == '__main__':
    # Check if processed data exists
    available_studies = processed_loader.list_available_studies()
    
    if not available_studies:
        print("⚠ Warning: No processed studies found!")
        print("Please run batch_process.py to generate data for all studies:")
        print("  python batch_process.py")
        print()
    else:
        print(f"✓ Found {len(available_studies)} processed studies:")
        for study in available_studies[:5]:  # Show first 5
            print(f"  - {study}")
        if len(available_studies) > 5:
            print(f"  ... and {len(available_studies) - 5} more")
        print()
    
    print("Starting Dash app...")
    print("Open your browser to: http://127.0.0.1:8050")
    
    app.run(debug=True, host='127.0.0.1', port=8050)
