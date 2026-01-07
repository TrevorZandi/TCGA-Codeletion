"""
Synthetic Lethality Target Discovery tab for co-deletion page.

Integrates Harle 2025 synthetic lethality data with TCGA deletion frequencies
to identify therapeutic opportunities.
"""

from dash import dcc, html
import dash_bootstrap_components as dbc


def create_target_discovery_tab():
    """Create the Synthetic Lethality Target Discovery tab content."""
    return dbc.Row([
        # Controls column
        dbc.Col([
            dbc.Card([
                dbc.CardHeader(html.H5("Target Discovery Controls", className="mb-0")),
                dbc.CardBody([
                    # Study selector
                    html.Label("Select Study:", className="fw-bold mt-2"),
                    dcc.Dropdown(
                        id='target-study-dropdown',
                        placeholder="Select a TCGA study",
                        className="mb-3"
                    ),
                    
                    # FDR threshold
                    html.Label("FDR Threshold:", className="fw-bold"),
                    dcc.Slider(
                        id='fdr-threshold-slider',
                        min=0.001,
                        max=0.1,
                        value=0.05,
                        step=0.001,
                        marks={
                            0.001: '0.1%',
                            0.01: '1%',
                            0.05: '5%',
                            0.1: '10%'
                        },
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    html.Small("Maximum false discovery rate for SL pairs", 
                              className="text-muted mb-3 d-block"),
                    
                    # Minimum deletion frequency
                    html.Label("Min Deletion Frequency:", className="fw-bold"),
                    dcc.Slider(
                        id='min-del-freq-slider',
                        min=0.01,
                        max=0.5,
                        value=0.05,
                        step=0.01,
                        marks={
                            0.01: '1%',
                            0.05: '5%',
                            0.1: '10%',
                            0.25: '25%',
                            0.5: '50%'
                        },
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    html.Small("Minimum frequency to consider gene deleted", 
                              className="text-muted mb-3 d-block"),
                    
                    # Essentiality filter
                    html.Label("Filter by Essentiality:", className="fw-bold"),
                    dcc.RadioItems(
                        id='essentiality-filter',
                        options=[
                            {'label': ' All Targets', 'value': 'all'},
                            {'label': ' Common Essential Only', 'value': 'essential'},
                            {'label': ' Non-Essential Only', 'value': 'non-essential'}
                        ],
                        value='all',
                        className="mb-3",
                        labelStyle={'display': 'block'}
                    ),
                    
                    # Info box
                    dbc.Alert([
                        html.H6("About Synthetic Lethality", className="alert-heading"),
                        html.P([
                            "Synthetic lethal gene pairs offer therapeutic opportunities: ",
                            "when one gene is deleted by cancer, inhibiting its SL partner ",
                            "selectively kills cancer cells while sparing normal cells."
                        ], className="mb-2 small"),
                        html.Hr(),
                        html.P([
                            html.Strong("Data source: "),
                            "Harle et al. 2025 - 472 gene pairs tested across 27 cancer cell lines ",
                            "(8 melanoma, 10 NSCLC, 9 pancreatic)"
                        ], className="mb-2 small"),
                        html.P([
                            html.Strong("Note: "),
                            "Most SL relationships (>50%) were context-dependent in the original screen, ",
                            "but may apply to other cancer types not tested."
                        ], className="mb-0 small text-muted")
                    ], color="info", className="mt-4")
                ])
            ])
        ], width=3),
        
        # Visualizations column
        dbc.Col([
            # Tab selector for different views
            dbc.Tabs([
                dbc.Tab(label="Top Opportunities", tab_id="tab-sl-opportunities"),
                dbc.Tab(label="Therapeutic Score Plot", tab_id="tab-sl-scatter"),
            ], id="target-viz-tabs", active_tab="tab-sl-opportunities", className="mb-3"),
            
            # Loading wrapper
            dcc.Loading(
                id="target-loading",
                type="default",
                children=html.Div(id="target-viz-content")
            )
        ], width=9)
    ])
