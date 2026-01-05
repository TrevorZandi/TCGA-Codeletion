"""
Visualization functions for synthetic lethality target discovery.

Creates Plotly figures for displaying therapeutic opportunities
based on synthetic lethal gene pairs and TCGA deletion data.
"""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from typing import Optional, List
from dash import dash_table, html
import dash_bootstrap_components as dbc


def create_target_ranking_table(
    opportunities_df: pd.DataFrame,
    max_rows: int = 100
) -> dash_table.DataTable:
    """
    Create interactive DataTable showing top therapeutic opportunities.
    
    Args:
        opportunities_df: Output from join_deletion_with_synthetic_lethality()
        max_rows: Maximum number of rows to display
    
    Returns:
        Dash DataTable component
    """
    if opportunities_df.empty:
        return html.Div(
            "No therapeutic opportunities found with current filters.",
            className="text-center text-muted p-5"
        )
    
    # Prepare display data
    display_df = opportunities_df.head(max_rows).copy()
    
    # Debug logging
    import sys
    print(f"[DEBUG] Opportunities columns: {opportunities_df.columns.tolist()}", file=sys.stderr)
    print(f"[DEBUG] 'deleted_gene_cytoband' in columns: {'deleted_gene_cytoband' in opportunities_df.columns}", file=sys.stderr)
    if 'deleted_gene_cytoband' in opportunities_df.columns:
        print(f"[DEBUG] Cytoband values: {opportunities_df['deleted_gene_cytoband'].head()}", file=sys.stderr)

    # Ensure cytoband column exists for display
    if 'deleted_gene_cytoband' not in display_df.columns:
        display_df['deleted_gene_cytoband'] = ''
    display_df['deleted_gene_cytoband'] = display_df['deleted_gene_cytoband'].fillna('')
    
    # Format columns
    columns_config = [
        {'name': 'Deleted Gene', 'id': 'deleted_gene', 'type': 'text'},
        {'name': 'Deleted gene cytoband', 'id': 'deleted_gene_cytoband', 'type': 'text'},
        {'name': 'Target Gene', 'id': 'target_gene', 'type': 'text'},
        {'name': 'Deletion %', 'id': 'deletion_frequency', 'type': 'numeric', 
         'format': {'specifier': '.1%'}},
        {'name': 'GI Score', 'id': 'gi_score', 'type': 'numeric', 
         'format': {'specifier': '.3f'}},
        {'name': 'Essential', 'id': 'target_is_common_essential', 'type': 'text',
         'presentation': 'markdown'},
        {'name': 'Dependent lines (DepMap)', 'id': 'target_depmap_dependent_lines', 'type': 'numeric'},
        {'name': 'FDR', 'id': 'fdr', 'type': 'numeric', 
         'format': {'specifier': '.2e'}},
    ]
    
    # Add hit frequency columns if available
    if 'hit_count' in display_df.columns:
        columns_config.extend([
            {'name': 'Validated In', 'id': 'hit_count', 'type': 'numeric'},
            {'name': 'Cancer Types', 'id': 'cancer_types_validated', 'type': 'text'}
        ])
    
    # Format essential column as Yes/No
    display_df['target_is_common_essential'] = display_df['target_is_common_essential'].map({
        True: '✓ Yes', False: 'No'
    })
    
    # Create DataTable
    table = dash_table.DataTable(
        data=display_df.to_dict('records'),
        columns=columns_config,
        page_size=20,
        page_action='native',
        sort_action='native',
        filter_action='native',
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '13px',
            'minWidth': '80px'
        },
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'borderBottom': '2px solid #dee2e6',
            'textAlign': 'left'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            },
            {
                'if': {
                    'filter_query': '{target_is_common_essential} contains "✓"',
                    'column_id': 'target_is_common_essential'
                },
                'backgroundColor': '#d4edda',
                'color': '#155724',
                'fontWeight': 'bold'
            }
        ]
    )
    
    return html.Div([
        html.P(
            f"Showing top {min(max_rows, len(opportunities_df))} of {len(opportunities_df)} therapeutic opportunities",
            className="text-muted mb-2 small"
        ),
        table
    ])


def create_gi_score_scatter(
    opportunities_df: pd.DataFrame,
    color_by: str = 'target_is_common_essential'
) -> go.Figure:
    """
    Create scatter plot of deletion frequency vs GI score, colored by essentiality.
    
    Args:
        opportunities_df: Output from join_deletion_with_synthetic_lethality()
        color_by: Column to use for coloring ('target_is_common_essential' or 'hit_fraction')
    
    Returns:
        Plotly Figure
    """
    if opportunities_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available with current filters",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color='gray')
        )
        return fig
    
    # Create hover text
    hover_text = []
    for _, row in opportunities_df.iterrows():
        text = f"<b>{row['deleted_gene']} deleted → target {row['target_gene']}</b><br>"
        text += f"Deletion: {row['deletion_frequency']:.1%}<br>"
        text += f"GI Score: {row['gi_score']:.3f}<br>"
        text += f"FDR: {row['fdr']:.2e}<br>"
        text += f"DepMap: {row['target_depmap_dependent_lines']}/1086<br>"
        
        if 'hit_count' in row and not pd.isna(row.get('hit_count')):
            text += f"Validated: {int(row['hit_count'])}/27 lines<br>"
            text += f"Cancer types: {row.get('cancer_types_validated', 'N/A')}"
        
        hover_text.append(text)
    
    # Determine color scheme
    if color_by == 'target_is_common_essential':
        color_map = {True: '#28a745', False: '#6c757d'}
        colors = opportunities_df['target_is_common_essential'].map(color_map)
        legend_title = 'Target Essentiality'
        
        # Create figure with separate traces for legend
        fig = go.Figure()
        
        for is_essential, color, label in [(True, '#28a745', 'Core Essential'), 
                                            (False, '#6c757d', 'Context-Specific')]:
            mask = opportunities_df['target_is_common_essential'] == is_essential
            if mask.any():
                subset = opportunities_df[mask]
                subset_hover = [hover_text[i] for i, m in enumerate(mask) if m]
                
                fig.add_trace(go.Scatter(
                    x=subset['deletion_frequency'],
                    y=subset['gi_score'],
                    mode='markers',
                    name=label,
                    marker=dict(
                        color=color,
                        size=subset['deletion_frequency'] * 50,  # Scale for visibility
                        sizemin=4,
                        opacity=0.7,
                        line=dict(width=0.5, color='white')
                    ),
                    customdata=subset_hover,
                    hovertemplate='%{customdata}<extra></extra>'
                ))
    elif color_by == 'hit_fraction' and 'hit_fraction' in opportunities_df.columns:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=opportunities_df['deletion_frequency'],
            y=opportunities_df['gi_score'],
            mode='markers',
            marker=dict(
                color=opportunities_df['hit_fraction'],
                colorscale='Viridis',
                size=opportunities_df['deletion_frequency'] * 50,
                sizemin=4,
                opacity=0.7,
                colorbar=dict(title='Validation<br>Frequency'),
                line=dict(width=0.5, color='white')
            ),
            customdata=hover_text,
            hovertemplate='%{customdata}<extra></extra>',
            showlegend=False
        ))
        legend_title = None
    else:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=opportunities_df['deletion_frequency'],
            y=opportunities_df['gi_score'],
            mode='markers',
            marker=dict(
                color='blue',
                size=opportunities_df['deletion_frequency'] * 50,
                sizemin=4,
                opacity=0.7,
                line=dict(width=0.5, color='white')
            ),
            customdata=hover_text,
            hovertemplate='%{customdata}<extra></extra>',
            showlegend=False
        ))
        legend_title = None
    
    # Layout
    fig.update_layout(
        title='Therapeutic Opportunities: Deletion Frequency vs Synthetic Lethality Strength',
        xaxis_title='Deletion Frequency',
        yaxis_title='GI Score',
        legend_title=legend_title,
        hovermode='closest',
        height=600,
        template='plotly_white'
    )
    
    # Format axes
    fig.update_xaxes(tickformat='.0%')
    
    return fig


def create_target_gene_ranking_bar(
    opportunities_df: pd.DataFrame,
    top_n: int = 20
) -> go.Figure:
    """
    Create bar chart showing top target genes by aggregated therapeutic score.
    
    Args:
        opportunities_df: Output from join_deletion_with_synthetic_lethality()
        top_n: Number of top targets to show
    
    Returns:
        Plotly Figure
    """
    if opportunities_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available with current filters",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color='gray')
        )
        return fig
    
    # Aggregate by target gene
    target_summary = opportunities_df.groupby('target_gene').agg({
        'deleted_gene': 'count',  # Number of distinct SL pairs
        'deletion_frequency': 'mean',
        'gi_score': lambda x: (x.abs()).mean(),  # Average absolute GI score
        'target_is_common_essential': 'first',
        'target_depmap_dependent_lines': 'first'
    }).reset_index()
    
    target_summary.columns = ['target_gene', 'opportunity_count', 'avg_deletion_freq', 'avg_gi_score',
                               'target_is_common_essential', 'target_depmap_dependent_lines']
    target_summary = target_summary.sort_values('avg_gi_score', ascending=False).head(top_n)
    
    # Color by essentiality
    colors = target_summary['target_is_common_essential'].map({
        True: '#28a745',
        False: '#6c757d'
    })
    
    # Create hover text
    hover_text = []
    for _, row in target_summary.iterrows():
        text = f"<b>{row['target_gene']}</b><br>"
        text += f"Avg |GI Score|: {row['avg_gi_score']:.3f}<br>"
        text += f"Opportunities: {row['opportunity_count']}<br>"
        text += f"Avg Deletion: {row['avg_deletion_freq']:.1%}<br>"
        text += f"Essential: {'Yes' if row['target_is_common_essential'] else 'No'}<br>"
        text += f"DepMap: {row['target_depmap_dependent_lines']}/1086 lines"
        hover_text.append(text)
    
    # Create figure
    fig = go.Figure(data=[
        go.Bar(
            x=target_summary['target_gene'],
            y=target_summary['avg_gi_score'],
            marker_color=colors,
            hovertemplate='%{customdata}<extra></extra>',
            customdata=hover_text,
            name=''
        )
    ])
    
    # Layout
    fig.update_layout(
        title=f'Top {top_n} Target Genes by Average Absolute GI Score',
        xaxis_title='Target Gene',
        yaxis_title='Average Absolute GI Score',
        showlegend=False,
        height=500,
        template='plotly_white'
    )
    
    # Rotate x-axis labels
    fig.update_xaxes(tickangle=-45)
    
    return fig


def create_study_comparison_heatmap(
    comparison_df: pd.DataFrame,
    top_n_targets: int = 20
) -> go.Figure:
    """
    Create heatmap comparing therapeutic scores across studies.
    
    Args:
        comparison_df: Output from compare_across_studies()
        top_n_targets: Number of top targets to show
    
    Returns:
        Plotly Figure
    """
    if comparison_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color='gray')
        )
        return fig
    
    # Get top target genes overall
    top_targets = (comparison_df.groupby('target_gene')['deleted_gene']
                   .count()
                   .sort_values(ascending=False)
                   .head(top_n_targets)
                   .index.tolist())
    
    # Pivot to create matrix
    matrix_df = comparison_df[comparison_df['target_gene'].isin(top_targets)].pivot_table(
        index='target_gene',
        columns='study_name',
        values='deletion_frequency',
        aggfunc='mean',
        fill_value=0
    )
    
    # Sort by average deletion frequency
    matrix_df['total'] = matrix_df.sum(axis=1)
    matrix_df = matrix_df.sort_values('total', ascending=False).drop('total', axis=1)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=matrix_df.values,
        x=[name.replace('(TCGA, PanCancer Atlas)', '').strip() for name in matrix_df.columns],
        y=matrix_df.index,
        colorscale='Viridis',
        hovertemplate='Target: %{y}<br>Study: %{x}<br>Score: %{z:.3f}<extra></extra>'
    ))
    
    # Layout
    fig.update_layout(
        title=f'Top {top_n_targets} Targets Across TCGA Studies',
        xaxis_title='TCGA Study',
        yaxis_title='Target Gene',
        height=600,
        template='plotly_white'
    )
    
    # Rotate x-axis labels
    fig.update_xaxes(tickangle=-45)
    
    return fig
