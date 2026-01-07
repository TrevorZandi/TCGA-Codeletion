"""
Dash application for interactive co-deletion analysis visualization with tabbed interface.

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

from src.layouts import create_home_layout, create_codeletion_layout, create_summary_layout, create_stats_display
from src.layouts.codeletion import (
    create_deletion_freq_tab,
    create_heatmap_tab,
    create_gene_pairs_tab,
    create_distance_scatter_tab
)
from src.data import processed_loader
from src.visualization import codeletion_heatmap


# ============================================================================
# Health Check Endpoint (for ELB)
# ============================================================================

def register_health_check(server):
    """
    Register lightweight health check endpoint for AWS Elastic Load Balancer.
    This endpoint requires no S3/file I/O and responds quickly.
    """
    @server.route('/health')
    def health_check():
        return {"status": "ok"}, 200


# ============================================================================
# Helper Functions
# ============================================================================

def get_study_display_name(study_id):
    """
    Get human-readable study name from cBioPortal API.
    
    Args:
        study_id: Study identifier (e.g., 'brca_tcga_pan_can_atlas_2018')
        
    Returns:
        Human-readable name (e.g., 'Breast Invasive Carcinoma')
    """
    try:
        from data.cbioportal_client import get_studies
        
        # Fetch all studies (cached)
        studies = get_studies()
        
        # Find matching study
        for study in studies:
            if study.get('studyId') == study_id:
                name = study.get('name', study_id)
                # Remove (TCGA, PanCancer Atlas) suffix
                name = name.replace('(TCGA, PanCancer Atlas)', '').strip()
                return name
        
        # Fallback to formatted study_id if not found
        return study_id.replace('_', ' ').replace('tcga', 'TCGA').replace('pan can atlas', 'PanCanAtlas').title()
    except Exception as e:
        # Fallback on error
        return study_id.replace('_', ' ').replace('tcga', 'TCGA').replace('pan can atlas', 'PanCanAtlas').title()


def get_study_options_with_names(available_studies):
    """
    Create dropdown options with human-readable study names.
    
    Args:
        available_studies: List of study IDs
        
    Returns:
        List of {'label': human_name, 'value': study_id} dicts
    """
    options = []
    for study_id in available_studies:
        display_name = get_study_display_name(study_id)
        options.append({'label': display_name, 'value': study_id})
    
    # Sort by label for better UX
    options.sort(key=lambda x: x['label'])
    
    return options


# Initialize Dash app with multi-page support
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.BOOTSTRAP],
    title="TCGA Co-Deletion Analysis",
    suppress_callback_exceptions=True  # Allow callbacks for components not yet in layout
)

# Expose server for WSGI
server = app.server

# Set the app layout with URL routing
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content')
])


# ============================================================================
# Page Routing Callbacks
# ============================================================================

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


# Callback: Display appropriate tab content
@app.callback(
    Output('tab-content', 'children'),
    Input('visualization-tabs', 'active_tab')
)
def display_tab_content(active_tab):
    """
    Display the appropriate content based on selected tab.
    
    Args:
        active_tab: ID of the active tab
        
    Returns:
        Layout component for the selected tab
    """
    if active_tab == 'tab-deletion-freq':
        return create_deletion_freq_tab()
    elif active_tab == 'tab-heatmap':
        return create_heatmap_tab()
    elif active_tab == 'tab-gene-pairs':
        return create_gene_pairs_tab()
    elif active_tab == 'tab-distance-scatter':
        return create_distance_scatter_tab()
    elif active_tab == 'tab-target-discovery':
        from layouts.target_discovery_tab import create_target_discovery_tab
        return create_target_discovery_tab()
    else:
        return create_heatmap_tab()  # Default


# ============================================================================
# Deletion Frequency Tab Callbacks
# ============================================================================

# Callback: Populate deletion tab study dropdown
@app.callback(
    [Output('deletion-study-dropdown', 'options'),
     Output('deletion-study-dropdown', 'value')],
    Input('deletion-study-dropdown', 'id')
)
def populate_deletion_study_dropdown(_):
    """Populate study dropdown for deletion frequency tab."""
    available_studies = processed_loader.list_available_studies()
    
    if not available_studies:
        return [{'label': 'No studies processed yet', 'value': 'none'}], 'none'
    
    options = get_study_options_with_names(available_studies)
    
    # Default to Breast Invasive Carcinoma if available, otherwise first alphabetically
    default_study_id = 'brca_tcga_pan_can_atlas_2018'
    if any(opt['value'] == default_study_id for opt in options):
        default_value = default_study_id
    else:
        default_value = options[0]['value'] if options else available_studies[0]
    
    return options, default_value

# Callback: Update deletion frequency scatter plot
@app.callback(
    Output('deletion-frequency-scatter', 'figure'),
    [
        Input('deletion-study-dropdown', 'value'),
        Input('deletion-chromosome-dropdown', 'value')
    ]
)
def update_deletion_scatter(study_id, chromosome):
    """Update the deletion frequency scatter plot."""
    if study_id is None or study_id == 'none':
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    deletion_freqs = processed_loader.load_deletion_frequencies(
        chromosome=chromosome,
        study_id=study_id
    )
    
    gene_metadata = processed_loader.load_gene_metadata(
        chromosome=chromosome,
        study_id=study_id
    )
    
    fig = codeletion_heatmap.create_deletion_frequency_scatter(
        deletion_freqs=deletion_freqs,
        gene_metadata=gene_metadata
    )
    
    return fig


# Callback: Update deletion frequency stats
@app.callback(
    Output('deletion-stats-display', 'children'),
    [
        Input('deletion-study-dropdown', 'value'),
        Input('deletion-chromosome-dropdown', 'value')
    ]
)
def update_deletion_stats(study_id, chromosome):
    """Update statistics for deletion frequency tab."""
    if study_id is None or study_id == 'none':
        return html.P("No data available", className="text-muted")
    
    deletion_freqs = processed_loader.load_deletion_frequencies(
        chromosome=chromosome,
        study_id=study_id
    )
    
    n_genes = len(deletion_freqs)
    # Handle both dict and Series/array types
    if hasattr(deletion_freqs, 'values'):
        if callable(deletion_freqs.values):
            freq_values = deletion_freqs.values()
        else:
            freq_values = deletion_freqs.values
    else:
        freq_values = deletion_freqs
    
    n_genes_with_deletions = sum(1 for freq in freq_values if freq > 0)
    max_deletion_pct = round(max(freq_values) * 100, 1) if len(freq_values) > 0 else 0
    
    return create_stats_display(n_genes, n_genes_with_deletions, max_deletion_pct, chromosome)


# ============================================================================
# Heatmap Tab Callbacks
# ============================================================================

# Callback: Populate heatmap tab study dropdown
@app.callback(
    [Output('heatmap-study-dropdown', 'options'),
     Output('heatmap-study-dropdown', 'value')],
    Input('heatmap-study-dropdown', 'id')
)
def populate_heatmap_study_dropdown(_):
    """Populate study dropdown for heatmap tab."""
    available_studies = processed_loader.list_available_studies()
    
    if not available_studies:
        return [{'label': 'No studies processed yet', 'value': 'none'}], 'none'
    
    options = get_study_options_with_names(available_studies)
    default_value = options[0]['value'] if options else available_studies[0]
    
    return options, default_value


# Callback: Update heatmap
@app.callback(
    Output('codeletion-heatmap', 'figure'),
    [
        Input('heatmap-colorscale-dropdown', 'value'),
        Input('heatmap-n-labels-slider', 'value'),
        Input('heatmap-study-dropdown', 'value'),
        Input('heatmap-chromosome-dropdown', 'value')
    ]
)
def update_heatmap(colorscale, n_labels, study_id, chromosome):
    """Update the co-deletion heatmap."""
    if study_id is None or study_id == 'none':
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    conditional_matrix = processed_loader.load_conditional_matrix(
        chromosome=chromosome,
        study_id=study_id
    )
    
    gene_metadata = processed_loader.load_gene_metadata(
        chromosome=chromosome,
        study_id=study_id
    )
    
    # Extract gene labels from metadata DataFrame
    gene_labels = None
    if gene_metadata is not None and not gene_metadata.empty:
        gene_labels = gene_metadata['hugoGeneSymbol'].tolist()
    
    fig = codeletion_heatmap.create_heatmap_figure(
        mat=conditional_matrix,
        colorscale=colorscale,
        n_labels=n_labels,
        cytobands=gene_labels
    )
    
    return fig


# Callback: Update heatmap stats
@app.callback(
    Output('heatmap-stats-display', 'children'),
    [
        Input('heatmap-study-dropdown', 'value'),
        Input('heatmap-chromosome-dropdown', 'value')
    ]
)
def update_heatmap_stats(study_id, chromosome):
    """Update statistics for heatmap tab."""
    if study_id is None or study_id == 'none':
        return html.P("No data available", className="text-muted")
    
    deletion_freqs = processed_loader.load_deletion_frequencies(
        chromosome=chromosome,
        study_id=study_id
    )
    
    n_genes = len(deletion_freqs)
    # Handle both dict and Series/array types
    if hasattr(deletion_freqs, 'values'):
        if callable(deletion_freqs.values):
            freq_values = deletion_freqs.values()
        else:
            freq_values = deletion_freqs.values
    else:
        freq_values = deletion_freqs
    
    n_genes_with_deletions = sum(1 for freq in freq_values if freq > 0)
    max_deletion_pct = round(max(freq_values) * 100, 1) if len(freq_values) > 0 else 0
    
    return create_stats_display(n_genes, n_genes_with_deletions, max_deletion_pct, chromosome)


# ============================================================================
# Gene Pairs Tab Callbacks
# ============================================================================

# Callback: Populate gene pairs tab study dropdown
@app.callback(
    [Output('pairs-study-dropdown', 'options'),
     Output('pairs-study-dropdown', 'value')],
    Input('pairs-study-dropdown', 'id')
)
def populate_pairs_study_dropdown(_):
    """Populate study dropdown for gene pairs tab."""
    available_studies = processed_loader.list_available_studies()
    
    if not available_studies:
        return [{'label': 'No studies processed yet', 'value': 'none'}], 'none'
    
    options = get_study_options_with_names(available_studies)
    default_value = options[0]['value'] if options else available_studies[0]
    
    return options, default_value


# Callback: Update top pairs table
@app.callback(
    Output('top-pairs-table', 'children'),
    [
        Input('pairs-n-pairs-slider', 'value'),
        Input('pairs-study-dropdown', 'value'),
        Input('pairs-chromosome-dropdown', 'value'),
        Input('pairs-gene-search-input', 'value'),
        Input('pairs-min-distance', 'value'),
        Input('pairs-max-distance', 'value'),
        Input('pairs-min-freq', 'value'),
        Input('pairs-min-pab', 'value'),
        Input('pairs-min-pba', 'value'),
        Input('pairs-min-joint', 'value')
    ]
)
def update_top_pairs_table(n_pairs, study_id, chromosome, gene_filter,
                          min_distance, max_distance, min_freq, min_pab, min_pba, min_joint):
    """Update the top gene pairs table."""
    if study_id is None or study_id == 'none':
        return html.P("No data available", className="text-muted")
    
    conditional_matrix = processed_loader.load_conditional_matrix(
        chromosome=chromosome,
        study_id=study_id
    )
    
    deletion_freqs = processed_loader.load_deletion_frequencies(
        chromosome=chromosome,
        study_id=study_id
    )
    
    joint_data = processed_loader.load_codeletion_pairs(
        chromosome=chromosome,
        study_id=study_id
    )
    
    gene_metadata = processed_loader.load_gene_metadata(
        chromosome=chromosome,
        study_id=study_id
    )
    
    table_data = codeletion_heatmap.create_top_pairs_table_data(
        conditional_matrix=conditional_matrix,
        deletion_freqs=deletion_freqs,
        joint_data=joint_data,
        gene_metadata=gene_metadata,
        n=n_pairs,
        gene_filter=gene_filter if gene_filter and gene_filter.strip() else None,
        min_distance=min_distance,
        max_distance=max_distance,
        min_freq=min_freq,
        min_pab=min_pab,
        min_pba=min_pba,
        min_joint=min_joint
    )
    
    return table_data


# ============================================================================
# Distance Scatter Tab Callbacks
# ============================================================================

# Callback: Populate distance scatter tab study dropdown
@app.callback(
    [Output('scatter-study-dropdown', 'options'),
     Output('scatter-study-dropdown', 'value')],
    Input('scatter-study-dropdown', 'id')
)
def populate_scatter_study_dropdown(_):
    """Populate study dropdown for distance scatter tab."""
    available_studies = processed_loader.list_available_studies()
    
    if not available_studies:
        return [{'label': 'No studies processed yet', 'value': 'none'}], 'none'
    
    options = get_study_options_with_names(available_studies)
    default_value = options[0]['value'] if options else available_studies[0]
    
    return options, default_value


# Callback: Update distance-frequency scatter plot
@app.callback(
    Output('distance-frequency-scatter', 'figure'),
    [
        Input('scatter-study-dropdown', 'value'),
        Input('scatter-chromosome-dropdown', 'value'),
        Input('scatter-gene-filter', 'value'),
        Input('scatter-min-freq-a', 'value'),
        Input('scatter-max-freq-a', 'value'),
        Input('scatter-min-distance', 'value'),
        Input('scatter-max-distance', 'value'),
        Input('scatter-min-pba', 'value'),
        Input('scatter-max-pba', 'value')
    ]
)
def update_distance_scatter(study_id, chromosome, gene_filter,
                           min_freq_a, max_freq_a, min_distance, max_distance, min_pba, max_pba):
    """Update the distance vs frequency scatter plot."""
    if study_id is None or study_id == 'none':
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    conditional_matrix = processed_loader.load_conditional_matrix(
        chromosome=chromosome,
        study_id=study_id
    )
    
    gene_metadata = processed_loader.load_gene_metadata(
        chromosome=chromosome,
        study_id=study_id
    )
    
    deletion_freqs = processed_loader.load_deletion_frequencies(
        chromosome=chromosome,
        study_id=study_id
    )
    
    fig = codeletion_heatmap.create_distance_frequency_scatter(
        conditional_matrix=conditional_matrix,
        gene_metadata=gene_metadata,
        deletion_freqs=deletion_freqs,
        gene_filter=gene_filter if gene_filter and gene_filter.strip() else None,
        freq_a=min_freq_a  # Using min as the threshold for filtering
    )
    
    return fig


# ============================================================================
# Summary Page Callbacks (unchanged)
# ============================================================================

# Callback: Populate summary page study dropdown
@app.callback(
    Output('summary-study-dropdown', 'options'),
    Input('summary-study-dropdown', 'id')
)
def populate_summary_study_dropdown(_):
    """Populate study dropdown for summary page."""
    available_studies = processed_loader.list_available_studies()
    
    if not available_studies:
        return [{'label': 'All Studies', 'value': 'all'}]
    
    options = [{'label': 'All Studies', 'value': 'all'}]
    options.extend(get_study_options_with_names(available_studies))
    
    return options


# Callback: Update summary statistics
@app.callback(
    [Output('summary-total-studies', 'children'),
     Output('summary-total-chromosomes', 'children'),
     Output('summary-total-analyses', 'children')],
    [Input('summary-study-dropdown', 'value'),
     Input('summary-chromosome-dropdown', 'value')]
)
def update_summary_stats(study_filter, chromosome_filter):
    """Update summary statistics."""
    available_studies = processed_loader.list_available_studies()
    
    if study_filter and study_filter != 'all':
        n_studies = 1
    else:
        n_studies = len(available_studies)
    
    if chromosome_filter and chromosome_filter != 'all':
        n_chromosomes = 1
    else:
        n_chromosomes = 24
    
    n_analyses = n_studies * n_chromosomes
    
    return str(n_studies), str(n_chromosomes), str(n_analyses)


# Callback: Update summary distribution chart
@app.callback(
    Output('summary-distribution-chart', 'figure'),
    [Input('summary-study-dropdown', 'value'),
     Input('summary-chromosome-dropdown', 'value')]
)
def update_summary_distribution(study_filter, chromosome_filter):
    """Update summary distribution chart."""
    import pandas as pd
    
    available_studies = processed_loader.list_available_studies()
    
    if study_filter and study_filter != 'all':
        studies_to_process = [study_filter]
    else:
        studies_to_process = available_studies[:5] if len(available_studies) > 5 else available_studies
    
    if chromosome_filter and chromosome_filter != 'all':
        chromosomes = [chromosome_filter]
    else:
        chromosomes = ['13']  # Default to chr13 for summary
    
    data = []
    for study in studies_to_process:
        for chrom in chromosomes:
            try:
                deletion_freqs = processed_loader.load_deletion_frequencies(
                    chromosome=chrom,
                    study_id=study
                )
                for gene, freq in deletion_freqs.items():
                    data.append({
                        'study': study,
                        'chromosome': chrom,
                        'gene': gene,
                        'deletion_freq': freq
                    })
            except:
                continue
    
    df = pd.DataFrame(data)
    
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    fig = go.Figure()
    fig.add_trace(go.Histogram(
        x=df['deletion_freq'],
        nbinsx=50,
        name='Deletion Frequency Distribution'
    ))
    
    fig.update_layout(
        title='Distribution of Gene Deletion Frequencies',
        xaxis_title='Deletion Frequency',
        yaxis_title='Count',
        template='plotly_white',
        height=400
    )
    
    return fig


# Callback: Update chromosome comparison chart
@app.callback(
    Output('summary-chromosome-comparison', 'figure'),
    [Input('summary-study-dropdown', 'value'),
     Input('summary-chromosome-dropdown', 'value')]
)
def update_chromosome_comparison(study_filter, chromosome_filter):
    """Update chromosome comparison chart."""
    fig = go.Figure()
    fig.add_annotation(
        text="Chromosome comparison visualization",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16)
    )
    return fig


# Callback: Update study comparison chart
@app.callback(
    Output('summary-study-comparison', 'figure'),
    [Input('summary-study-dropdown', 'value'),
     Input('summary-chromosome-dropdown', 'value')]
)
def update_study_comparison(study_filter, chromosome_filter):
    """Update study comparison chart."""
    fig = go.Figure()
    fig.add_annotation(
        text="Study comparison visualization",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16)
    )
    return fig


# Callback: Update summary table
@app.callback(
    Output('summary-table', 'children'),
    [Input('summary-study-dropdown', 'value'),
     Input('summary-chromosome-dropdown', 'value')]
)
def update_summary_table(study_filter, chromosome_filter):
    """Update summary table."""
    return html.P("Summary table", className="text-muted")


# ============================================================================
# Synthetic Lethality Target Discovery Callbacks
# ============================================================================

# Callback: Populate target discovery study dropdown
@app.callback(
    Output('target-study-dropdown', 'options'),
    Input('target-study-dropdown', 'id')
)
def populate_target_study_dropdown(_):
    """Populate study dropdown for target discovery tab."""
    studies = processed_loader.list_available_studies()
    return get_study_options_with_names(studies)


# Callback: Update target discovery visualizations
@app.callback(
    Output('target-viz-content', 'children'),
    [Input('target-viz-tabs', 'active_tab'),
     Input('target-study-dropdown', 'value'),
     Input('fdr-threshold-slider', 'value'),
     Input('min-del-freq-slider', 'value'),
     Input('essentiality-filter', 'value')]
)
def update_target_discovery_viz(active_viz_tab, study_id, fdr_threshold, min_del_freq, ess_filter):
    """Update target discovery visualizations based on user selections."""
    from analysis import synthetic_lethality
    from visualization import target_discovery
    
    if study_id is None:
        return html.Div([
            html.P("Please select a study to view therapeutic opportunities.", 
                   className="text-center text-muted mt-5")
        ])
    
    try:
        # Load synthetic lethality data
        sl_data = synthetic_lethality.load_synthetic_lethal_data(fdr_threshold=fdr_threshold)
        
        if sl_data.empty:
            return html.Div([
                html.P("No synthetic lethal pairs found with current FDR threshold.", 
                       className="text-center text-muted mt-5")
            ])
        
        hit_freq_df = synthetic_lethality.calculate_hit_frequency(sl_data)
        
        # Load genome-wide deletions for selected study
        deletions = synthetic_lethality.aggregate_deletions_genome_wide(study_id)
        
        if deletions.empty:
            return html.Div([
                dbc.Alert([
                    html.H5("No Deletion Data Available", className="alert-heading"),
                    html.P(f"No processed deletion data found for study: {study_id}"),
                    html.Hr(),
                    html.P("Please ensure the study has been processed with batch_process.py", 
                           className="mb-0 small")
                ], color="warning")
            ])
        
        # Join with SL data
        opportunities = synthetic_lethality.join_deletion_with_synthetic_lethality(
            deletion_df=deletions,
            sl_data=sl_data,
            hit_frequency_df=hit_freq_df,
            min_deletion_freq=min_del_freq
        )
        
        # Apply essentiality filter
        if ess_filter == 'essential':
            opportunities = opportunities[opportunities['target_is_common_essential'] == True]
        elif ess_filter == 'non-essential':
            opportunities = opportunities[opportunities['target_is_common_essential'] == False]
        
        # Check if we have data
        if opportunities.empty:
            return html.Div([
                dbc.Alert([
                    html.H5("No Opportunities Found", className="alert-heading"),
                    html.P("No therapeutic opportunities found with current filters."),
                    html.Hr(),
                    html.P([
                        "Try adjusting: ",
                        html.Ul([
                            html.Li("Lower the minimum deletion frequency"),
                            html.Li("Increase the FDR threshold"),
                            html.Li("Change the essentiality filter to 'All Targets'")
                        ])
                    ], className="mb-0 small")
                ], color="info")
            ])
        
        # Render appropriate visualization
        if active_viz_tab == 'tab-sl-opportunities':
            return target_discovery.create_target_ranking_table(opportunities)
        
        elif active_viz_tab == 'tab-sl-scatter':
            fig = target_discovery.create_gi_score_scatter(opportunities)
            return dcc.Graph(figure=fig, config={'displayModeBar': True, 'toImageButtonOptions': {
                'format': 'png',
                'filename': f'therapeutic_opportunities_{study_id}',
                'height': 800,
                'width': 1200,
                'scale': 2
            }})
        
        else:
            return html.Div("Unknown visualization type")
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        return html.Div([
            dbc.Alert([
                html.H5("Error Loading Data", className="alert-heading"),
                html.P(f"Failed to load target discovery data: {str(e)}"),
                html.Hr(),
                html.Details([
                    html.Summary("Error Details", className="text-muted small"),
                    html.Pre(error_details, className="small text-muted", 
                            style={'maxHeight': '200px', 'overflow': 'auto'})
                ])
            ], color="danger")
        ])


# Register health check endpoint
register_health_check(app.server)


# Run the app
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8050)
