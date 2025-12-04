"""
Dash application for interactive co-deletion analysis visualization.

This multi-page app loads pre-processed co-deletion data and provides interactive
controls for exploring conditional co-deletion probabilities.
"""

import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

from dash import Dash, Input, Output, State, html, dcc
import dash_bootstrap_components as dbc
import plotly.graph_objects as go

from layouts import create_home_layout, create_codeletion_layout, create_summary_layout, create_stats_display
from data import processed_loader
from visualization import codeletion_heatmap


# Initialize Dash app with multi-page support
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="TCGA Co-Deletion Analysis",
    suppress_callback_exceptions=True  # Allow callbacks for components not yet in layout
)

# Set the app layout with URL routing
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


# Callback: Display appropriate page based on URL
@app.callback(
    Output('page-content', 'children'),
    Input('url', 'pathname')
)
def display_page(pathname):
    """
    Route to the appropriate page based on URL pathname.
    
    Args:
        pathname: Current URL path
        
    Returns:
        Layout component for the requested page
    """
    if pathname == '/codeletion':
        return create_codeletion_layout()
    elif pathname == '/summary':
        return create_summary_layout()
    elif pathname == '/' or pathname == '/home':
        return create_home_layout()
    else:
        # 404 page
        return dbc.Container([
            dbc.Row([
                dbc.Col([
                    html.H1("404: Page Not Found", className="text-center mt-5 mb-4"),
                    html.P(
                        "The page you're looking for doesn't exist.",
                        className="text-center text-muted mb-4"
                    ),
                    html.Div([
                        dcc.Link(
                            dbc.Button("Go Home", color="primary", size="lg"),
                            href="/"
                        )
                    ], className="text-center")
                ])
            ])
        ], style={'maxWidth': '800px'})


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
        Input('study-dropdown', 'value'),
        Input('chromosome-dropdown', 'value')
    ]
)
def update_heatmap(colorscale, n_labels, study_id, chromosome):
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
    
    # Load processed data for selected study and chromosome
    conditional_matrix = processed_loader.load_conditional_matrix(
        chromosome=chromosome, 
        study_id=study_id
    )
    
    # Load gene metadata for cytoband labels
    try:
        gene_metadata = processed_loader.load_gene_metadata(
            chromosome=chromosome,
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
        title=f"Chr{chromosome} Conditional Co-Deletion Matrix - {study_name}",
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
        Input('study-dropdown', 'value'),
        Input('chromosome-dropdown', 'value')
    ]
)
def update_top_pairs(n_pairs, study_id, chromosome):
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
    
    # Load co-deletion pairs data for selected study and chromosome
    pairs_data = processed_loader.load_codeletion_pairs(
        chromosome=chromosome,
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
    [
        Input('study-dropdown', 'value'),
        Input('chromosome-dropdown', 'value')
    ]
)
def update_deletion_scatter(study_id, chromosome):
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
        chromosome=chromosome,
        study_id=study_id
    )
    
    # Load gene metadata for cytoband ordering
    try:
        gene_metadata = processed_loader.load_gene_metadata(
            chromosome=chromosome,
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
    [
        Input('study-dropdown', 'value'),
        Input('chromosome-dropdown', 'value')
    ]
)
def update_stats(study_id, chromosome):
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
    
    # Load data to get stats for selected study and chromosome
    conditional_matrix = processed_loader.load_conditional_matrix(
        chromosome=chromosome,
        study_id=study_id
    )
    
    # Calculate basic stats
    n_genes = conditional_matrix.shape[0]
    
    # Get deletion frequencies to calculate max and count genes with deletions
    try:
        del_freqs = processed_loader.load_deletion_frequencies(
            chromosome=chromosome,
            study_id=study_id
        )
        max_deletion_pct = int(del_freqs.max() * 100) if len(del_freqs) > 0 else 0
        n_genes_with_deletions = (del_freqs > 0).sum()  # Count genes deleted at least once
    except:
        max_deletion_pct = 0
        n_genes_with_deletions = 0
    
    # Create stats display with chromosome information
    stats_html = create_stats_display(
        n_genes=n_genes,
        n_genes_with_deletions=n_genes_with_deletions,
        max_deletion_pct=max_deletion_pct,
        chromosome=chromosome
    )
    
    return stats_html


# ============================================================================
# Summary Page Callbacks
# ============================================================================

# Callback: Populate summary page study dropdown
@app.callback(
    Output('summary-study-dropdown', 'options'),
    Input('summary-study-dropdown', 'id')
)
def populate_summary_study_dropdown(_):
    """Populate the summary study dropdown."""
    available_studies = processed_loader.list_available_studies()
    
    if not available_studies:
        return [{'label': 'No studies processed yet', 'value': 'none'}]
    
    options = [{'label': 'All Studies', 'value': 'all'}]
    for study_id in available_studies:
        label = study_id.replace('_tcga_pan_can_atlas_2018', '').replace('_', ' ').upper()
        options.append({'label': label, 'value': study_id})
    
    return options


# Callback: Update summary statistics
@app.callback(
    [Output('summary-total-studies', 'children'),
     Output('summary-total-chromosomes', 'children'),
     Output('summary-total-analyses', 'children')],
    [Input('summary-study-dropdown', 'value'),
     Input('summary-chromosome-dropdown', 'value')]
)
def update_summary_stats(study_id, chromosome):
    """Update the summary statistics cards."""
    available_studies = processed_loader.list_available_studies()
    
    if not available_studies:
        return "0", "0", "0"
    
    n_studies = len(available_studies) if study_id == 'all' or study_id is None else 1
    n_chromosomes = 24 if chromosome == 'all' else 1
    n_analyses = n_studies * n_chromosomes
    
    return str(n_studies), str(n_chromosomes), str(n_analyses)


# Callback: Update summary distribution chart
@app.callback(
    Output('summary-distribution-chart', 'figure'),
    [Input('summary-study-dropdown', 'value'),
     Input('summary-chromosome-dropdown', 'value')]
)
def update_summary_distribution(study_id, chromosome):
    """
    Update the deletion frequency distribution chart.
    Shows all genes with cytobands on x-axis and deletion frequency on y-axis.
    Only includes genes with at least one deletion across all studies.
    """
    try:
        # Determine which studies and chromosomes to load
        studies_to_load = [study_id] if study_id else processed_loader.list_available_studies()
        
        if chromosome == 'all':
            chromosomes_to_load = [str(i) for i in range(1, 23)] + ['X', 'Y']
        else:
            chromosomes_to_load = [chromosome]
        
        # Collect all gene deletion data
        all_gene_data = []
        
        for study in studies_to_load:
            for chrom in chromosomes_to_load:
                try:
                    # Load deletion frequencies
                    del_freqs = processed_loader.load_deletion_frequencies(chrom, study)
                    
                    # Load gene metadata for cytoband information
                    gene_metadata = processed_loader.load_gene_metadata(chrom, study)
                    
                    # Create a mapping from gene name to cytoband
                    gene_metadata['gene_name'] = gene_metadata['hugoGeneSymbol'] + ' (' + gene_metadata['entrezGeneId'].astype(str) + ')'
                    cytoband_map = dict(zip(gene_metadata['gene_name'], gene_metadata['cytoband']))
                    
                    # Process each gene
                    for gene_name, freq in del_freqs.items():
                        if freq > 0:  # Only include genes with deletions
                            cytoband = cytoband_map.get(gene_name, f"{chrom}q")
                            gene_symbol = gene_name.split(' ')[0]
                            
                            all_gene_data.append({
                                'gene': gene_symbol,
                                'gene_full': gene_name,
                                'chromosome': chrom,
                                'cytoband': cytoband,
                                'deletion_frequency': freq,
                                'study': study
                            })
                            
                except Exception as e:
                    # Skip if data not available for this study/chromosome
                    continue
        
        if not all_gene_data:
            fig = go.Figure()
            fig.add_annotation(
                text="No deletion data available for selected filters",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            fig.update_layout(height=500)
            return fig
        
        # Convert to DataFrame
        import pandas as pd
        df = pd.DataFrame(all_gene_data)
        
        # Average deletion frequency across studies for each gene
        gene_avg = df.groupby(['gene', 'gene_full', 'chromosome', 'cytoband'])['deletion_frequency'].mean().reset_index()
        
        # Sort by chromosome and cytoband
        chrom_order = {str(i): i for i in range(1, 23)}
        chrom_order['X'] = 23
        chrom_order['Y'] = 24
        gene_avg['chrom_num'] = gene_avg['chromosome'].map(chrom_order)
        gene_avg = gene_avg.sort_values(['chrom_num', 'cytoband'])
        
        # Create x-axis labels (cytoband)
        gene_avg['x_label'] = gene_avg['cytoband']
        gene_avg['x_pos'] = range(len(gene_avg))
        
        # Create figure
        fig = go.Figure()
        
        # Group by chromosome for coloring
        colors = {
            '1': '#1f77b4', '2': '#ff7f0e', '3': '#2ca02c', '4': '#d62728',
            '5': '#9467bd', '6': '#8c564b', '7': '#e377c2', '8': '#7f7f7f',
            '9': '#bcbd22', '10': '#17becf', '11': '#1f77b4', '12': '#ff7f0e',
            '13': '#2ca02c', '14': '#d62728', '15': '#9467bd', '16': '#8c564b',
            '17': '#e377c2', '18': '#7f7f7f', '19': '#bcbd22', '20': '#17becf',
            '21': '#1f77b4', '22': '#ff7f0e', 'X': '#2ca02c', 'Y': '#d62728'
        }
        
        for chrom in gene_avg['chromosome'].unique():
            chrom_data = gene_avg[gene_avg['chromosome'] == chrom]
            fig.add_trace(go.Scatter(
                x=chrom_data['x_pos'],
                y=chrom_data['deletion_frequency'] * 100,  # Convert to percentage
                mode='markers',
                marker=dict(
                    size=5,
                    color=colors.get(chrom, '#888888'),
                    opacity=0.6
                ),
                name=f'Chr {chrom}',
                text=[f"{row['gene']}<br>{row['cytoband']}<br>{row['deletion_frequency']*100:.1f}%" 
                      for _, row in chrom_data.iterrows()],
                hovertemplate='%{text}<extra></extra>'
            ))
        
        # Add chromosome boundaries as vertical lines
        chrom_boundaries = gene_avg.groupby('chromosome')['x_pos'].min().values
        for boundary in chrom_boundaries[1:]:  # Skip first
            fig.add_vline(x=boundary - 0.5, line_dash="dash", line_color="gray", opacity=0.3)
        
        # Update layout
        fig.update_layout(
            height=600,
            title={
                'text': 'Deletion Frequency by Cytoband (Genes with Deletions Only)',
                'x': 0.5,
                'xanchor': 'center'
            },
            xaxis_title="Cytoband Position",
            yaxis_title="Deletion Frequency (%)",
            hovermode='closest',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            xaxis=dict(
                showticklabels=False  # Too many cytobands to show
            )
        )
        
        return fig
        
    except Exception as e:
        # Error handling
        fig = go.Figure()
        fig.add_annotation(
            text=f"Error loading data: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=14, color="red")
        )
        fig.update_layout(height=500)
        return fig


# Callback: Update chromosome comparison chart
@app.callback(
    Output('summary-chromosome-comparison', 'figure'),
    [Input('summary-study-dropdown', 'value'),
     Input('summary-chromosome-dropdown', 'value')]
)
def update_chromosome_comparison(study_id, chromosome):
    """Update the chromosome comparison chart."""
    fig = go.Figure()
    fig.add_annotation(
        text="Chromosome comparison coming soon...",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16)
    )
    fig.update_layout(
        height=400,
        xaxis_title="Chromosome",
        yaxis_title="Avg Deletion Frequency"
    )
    return fig


# Callback: Update study comparison chart
@app.callback(
    Output('summary-study-comparison', 'figure'),
    [Input('summary-study-dropdown', 'value'),
     Input('summary-chromosome-dropdown', 'value')]
)
def update_study_comparison(study_id, chromosome):
    """Update the study comparison chart."""
    fig = go.Figure()
    fig.add_annotation(
        text="Study comparison coming soon...",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16)
    )
    fig.update_layout(
        height=400,
        xaxis_title="Study",
        yaxis_title="Avg Deletion Frequency"
    )
    return fig


# Callback: Update summary table
@app.callback(
    Output('summary-table', 'children'),
    [Input('summary-study-dropdown', 'value'),
     Input('summary-chromosome-dropdown', 'value')]
)
def update_summary_table(study_id, chromosome):
    """Update the summary statistics table."""
    return html.P(
        "Detailed statistics table coming soon...",
        className="text-muted text-center"
    )


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
