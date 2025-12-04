"""
Summary statistics page layout.

This module contains the layout for viewing summary statistics across
all processed studies and chromosomes.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc


def create_summary_layout():
    """
    Create the summary statistics layout.
    
    Returns:
        Dash layout component for the summary page
    """
    layout = dbc.Container([
        # Header with back button
        dbc.Row([
            dbc.Col([
                dcc.Link(
                    dbc.Button("← Home", color="secondary", outline=True, size="sm", className="mb-3"),
                    href="/"
                ),
                html.H1(
                    "Summary Statistics",
                    className="text-center mb-4"
                ),
                html.P(
                    "Comprehensive overview of co-deletion patterns across all TCGA studies and chromosomes.",
                    className="text-center text-muted mb-4"
                )
            ])
        ]),
        
        # Controls section
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Filter Options")),
                    dbc.CardBody([
                        # Study selector
                        html.Label("TCGA Study:", className="fw-bold"),
                        dcc.Dropdown(
                            id='summary-study-dropdown',
                            options=[],  # Will be populated by callback
                            value=None,
                            placeholder="Select a study or view all...",
                            clearable=True,
                            className="mb-3"
                        ),
                        
                        # Chromosome selector
                        html.Label("Chromosome:", className="fw-bold"),
                        dcc.Dropdown(
                            id='summary-chromosome-dropdown',
                            options=[
                                {'label': 'All Chromosomes', 'value': 'all'},
                                *[{'label': f'Chromosome {i}', 'value': str(i)} for i in range(1, 23)],
                                {'label': 'Chromosome X', 'value': 'X'},
                                {'label': 'Chromosome Y', 'value': 'Y'}
                            ],
                            value='all',
                            clearable=False,
                            className="mb-3"
                        ),
                    ])
                ], className="mb-4")
            ], width=12, lg=3),
            
            # Summary stats cards
            dbc.Col([
                dbc.Row([
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3("--", id="summary-total-studies", className="text-primary mb-0"),
                                html.P("Studies Processed", className="text-muted small mb-0")
                            ], className="text-center")
                        ])
                    ], width=4, className="mb-3"),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3("--", id="summary-total-chromosomes", className="text-primary mb-0"),
                                html.P("Chromosomes Analyzed", className="text-muted small mb-0")
                            ], className="text-center")
                        ])
                    ], width=4, className="mb-3"),
                    dbc.Col([
                        dbc.Card([
                            dbc.CardBody([
                                html.H3("--", id="summary-total-analyses", className="text-primary mb-0"),
                                html.P("Total Analyses", className="text-muted small mb-0")
                            ], className="text-center")
                        ])
                    ], width=4, className="mb-3")
                ])
            ], width=12, lg=9)
        ]),
        
        # Deletion frequency distribution chart
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Deletion Frequency Distribution")),
                    dbc.CardBody([
                        dcc.Loading(
                            id="loading-summary-distribution",
                            type="default",
                            children=dcc.Graph(
                                id='summary-distribution-chart',
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
        
        # Chromosome comparison chart
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Chromosome Comparison")),
                    dbc.CardBody([
                        dcc.Loading(
                            id="loading-summary-comparison",
                            type="default",
                            children=dcc.Graph(
                                id='summary-chromosome-comparison',
                                config={
                                    'displayModeBar': True,
                                    'displaylogo': False
                                }
                            )
                        )
                    ])
                ])
            ], width=12, lg=6, className="mb-4"),
            
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Study Comparison")),
                    dbc.CardBody([
                        dcc.Loading(
                            id="loading-summary-study-comparison",
                            type="default",
                            children=dcc.Graph(
                                id='summary-study-comparison',
                                config={
                                    'displayModeBar': True,
                                    'displaylogo': False
                                }
                            )
                        )
                    ])
                ])
            ], width=12, lg=6, className="mb-4")
        ]),
        
        # Data table
        dbc.Row([
            dbc.Col([
                dbc.Card([
                    dbc.CardHeader(html.H5("Detailed Statistics Table")),
                    dbc.CardBody([
                        html.Div(
                            id='summary-table',
                            children=[
                                html.P("Select filters to view detailed statistics...", className="text-muted text-center")
                            ]
                        )
                    ])
                ])
            ], width=12)
        ], className="mb-4"),
        
        # Footer
        dbc.Row([
            dbc.Col([
                html.Hr(),
                html.Div([
                    html.P(
                        [
                            "Data source: ",
                            html.A("cBioPortal for Cancer Genomics", 
                                   href="https://www.cbioportal.org/", 
                                   target="_blank"),
                            " | TCGA PanCancer Atlas 2018"
                        ],
                        className="text-center text-muted small"
                    )
                ], className="mb-4")
            ])
        ])
        
    ], fluid=True, style={'maxWidth': '1400px'})
    
    return layout
