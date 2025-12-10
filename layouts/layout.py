"""
Dash layout for chromosome co-deletion heatmap visualization.

This module defines the Dash app layout for displaying interactive
co-deletion heatmaps and related visualizations.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc


def create_layout():
    """
    Create the main Dash layout for the co-deletion analysis app.
    
    Returns:
        Dash layout component
    """
    layout = dbc.Container([
        # Header
        dbc.Row([
            dbc.Col([
                html.H1(
                    "TCGA Co-Deletion Analysis",
                    className="text-center mb-4 mt-4"
                ),
                html.P(
                    "Interactive visualization of conditional co-deletion probabilities "
                    "across chromosomes and TCGA PanCancer Atlas studies.",
                    className="text-center text-muted mb-4"
                )
            ])
        ]),
        
        # Controls section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Visualization Controls")),
                    dbc.CardBody([
                        # Study selector
                        html.Label("TCGA Study:", className="fw-bold"),
                        dcc.Dropdown(
                            id='study-dropdown',
                            options=[],  # Will be populated by callback
                            value=None,  # Will be set by callback
                            clearable=False,
                            className="mb-3"
                        ),
                        
                        # Chromosome selector
                        html.Label("Chromosome:", className="fw-bold"),
                        dcc.Dropdown(
                            id='chromosome-dropdown',
                            options=[
                                *[{'label': f'Chromosome {i}', 'value': str(i)} for i in range(1, 23)],
                                {'label': 'Chromosome X', 'value': 'X'},
                                {'label': 'Chromosome Y', 'value': 'Y'}
                            ],
                            value='13',  # Default to chr13
                            clearable=False,
                            className="mb-3"
                        ),
                        
                        # Colorscale selector
                        html.Label("Colorscale:", className="fw-bold"),
                        dcc.Dropdown(
                            id='colorscale-dropdown',
                            options=[
                                {'label': 'Viridis', 'value': 'Viridis'},
                                {'label': 'YlOrRd (Yellow-Orange-Red)', 'value': 'YlOrRd'},
                                {'label': 'Blues', 'value': 'Blues'},
                                {'label': 'Reds', 'value': 'Reds'},
                                {'label': 'RdBu (Red-Blue)', 'value': 'RdBu'},
                                {'label': 'Plasma', 'value': 'Plasma'},
                            ],
                            value='Viridis',
                            clearable=False,
                            className="mb-3"
                        ),
                        
                        # Number of labels slider
                        html.Label("Number of axis labels:", className="fw-bold"),
                        dcc.Slider(
                            id='n-labels-slider',
                            min=5,
                            max=50,
                            step=5,
                            value=20,
                            marks={i: str(i) for i in range(5, 51, 5)},
                            tooltip={"placement": "bottom", "always_visible": True}
                        ),
                    ])
                ], className="mb-4")
            ], width=12, lg=3),
            
            # Stats section
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Dataset Statistics")),
                    dbc.CardBody([
                        html.Div(id='stats-display', children=[
                            html.P("Loading dataset information...", className="text-muted")
                        ])
                    ])
                ], className="mb-4")
            ], width=12, lg=9)
        ]),
        
        # Individual gene deletion frequencies
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Individual Gene Deletion Frequencies")),
                    dbc.CardBody([
                        dcc.Loading(
                            id="loading-deletion-scatter",
                            type="default",
                            children=dcc.Graph(
                                id='deletion-frequency-scatter',
                                config={
                                    'displayModeBar': True,
                                    'displaylogo': False
                                }
                            )
                        )
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Main heatmap
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Conditional Co-Deletion Heatmap")),
                    dbc.CardBody([
                        dcc.Loading(
                            id="loading-heatmap",
                            type="default",
                            children=dcc.Graph(
                                id='codeletion-heatmap',
                                config={
                                    'displayModeBar': True,
                                    'displaylogo': False,
                                    'toImageButtonOptions': {
                                        'format': 'png',
                                        'filename': 'chr13_codeletion_heatmap',
                                        'height': 1200,
                                        'width': 1200,
                                        'scale': 2
                                    }
                                }
                            )
                        )
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Additional visualizations section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Top Co-deleted Gene Pairs")),
                    dbc.CardBody([
                        # Number of top pairs selector
                        html.Label("Number of top pairs to display:", className="fw-bold mb-2"),
                        dcc.Slider(
                            id='n-pairs-slider',
                            min=10,
                            max=50,
                            step=5,
                            value=20,
                            marks={i: str(i) for i in range(10, 51, 10)},
                            tooltip={"placement": "bottom", "always_visible": True},
                            className="mb-3"
                        ),
                        dcc.Loading(
                            id="loading-barplot",
                            type="default",
                            children=dcc.Graph(
                                id='top-pairs-barplot',
                                config={
                                    'displayModeBar': True,
                                    'displaylogo': False
                                }
                            )
                        )
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Footer
        dbc.Row([
            dbc.Col([
                html.Hr(),
                html.Div(
                    id='footer-info',
                    children=[
                        html.P(
                            [
                                "Data source: ",
                                html.A("cBioPortal for Cancer Genomics", 
                                       href="https://www.cbioportal.org/", 
                                       target="_blank"),
                                " | TCGA PanCancer Atlas 2018"
                            ],
                            className="text-center text-muted small"
                        ),
                        html.P(
                            [
                                "Created by Trevor A. Zandi | ",
                                html.A("GitHub",
                                       href="https://github.com/TrevorZandi/TCGA-Codeletion",
                                       target="_blank")
                            ],
                            className="text-center text-muted small"
                        )
                    ]
                )
            ])
        ])
        
    ], fluid=True, style={'maxWidth': '1400px'})
    
    return layout


def create_stats_display(n_genes, n_genes_with_deletions, max_deletion_pct, chromosome="13"):
    """
    Create statistics display component.
    
    Args:
        n_genes: Number of genes on the chromosome
        n_genes_with_deletions: Number of genes deleted at least once
        max_deletion_pct: Maximum individual gene deletion frequency (as percentage)
        chromosome: Chromosome identifier (default: "13")
        
    Returns:
        HTML component with statistics
    """
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H4(str(n_genes), className="text-primary mb-0"),
                    html.P(f"Genes on Chr{chromosome}", className="text-muted small mb-0")
                ], className="text-center")
            ], width=4),
            dbc.Col([
                html.Div([
                    html.H4(str(n_genes_with_deletions), className="text-primary mb-0"),
                    html.P("Genes with Deletions", className="text-muted small mb-0")
                ], className="text-center")
            ], width=4),
            dbc.Col([
                html.Div([
                    html.H4(f"{max_deletion_pct}%", className="text-primary mb-0"),
                    html.P("Max Deletion Freq", className="text-muted small mb-0")
                ], className="text-center")
            ], width=4)
        ])
    ])
