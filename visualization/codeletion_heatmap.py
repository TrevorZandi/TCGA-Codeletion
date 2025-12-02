"""
Visualization functions for co-deletion analysis.

This module provides functions to create interactive heatmaps and other visualizations
for co-deletion frequency matrices using Plotly (Dash-compatible).
"""

import os
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px


def create_heatmap_figure(mat, title="Conditional Co-Deletion Matrix", colorscale="Viridis", cytobands=None, n_labels=20):
    """
    Create an interactive Plotly heatmap figure (Dash-compatible, no file saving).
    
    Args:
        mat: DataFrame with co-deletion data (genes x genes)
        title: Title for the plot
        colorscale: Plotly colorscale name (e.g., 'Viridis', 'YlOrRd', 'Blues')
        cytobands: Optional list of cytobands corresponding to genes (if provided, used instead of gene names)
        n_labels: Number of labels to show on axes (default: 20, evenly spaced)
        
    Returns:
        Plotly Figure object
    """
    # Determine labels to display
    if cytobands is not None:
        # Use cytobands instead of gene names
        labels = cytobands
    else:
        # Use gene names from matrix
        labels = list(mat.columns)
    
    # Select evenly spaced indices for n_labels
    n_genes = mat.shape[0]
    if n_genes <= n_labels:
        # Show all labels if fewer than requested
        tick_indices = list(range(n_genes))
        tick_labels = [labels[i] for i in tick_indices]
    else:
        # Show evenly spaced labels
        tick_indices = np.linspace(0, n_genes - 1, n_labels, dtype=int).tolist()
        tick_labels = [labels[i] for i in tick_indices]
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=mat.values,
        x=list(range(n_genes)),
        y=list(range(n_genes)),
        colorscale=colorscale,
        colorbar=dict(
            title=dict(
                text="P(i | j)<br>Conditional<br>co-deletion<br>probability",
                side="right"
            )
        ),
        hovertemplate='Row: %{y}<br>Col: %{x}<br>P(i|j): %{z:.3f}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(text=title, x=0.5, xanchor='center', font=dict(size=16)),
        xaxis=dict(
            title="Gene Position (Chromosomal Order)",
            tickmode='array',
            tickvals=tick_indices,
            ticktext=tick_labels,
            tickangle=90,
            tickfont=dict(size=10)
        ),
        yaxis=dict(
            title="Gene Position (Chromosomal Order)",
            tickmode='array',
            tickvals=tick_indices,
            ticktext=tick_labels,
            tickfont=dict(size=10)
        ),
        width=900,
        height=800,
        plot_bgcolor='white'
    )
    
    return fig


def plot_heatmap(mat, title="Conditional Co-Deletion Matrix", colorscale="Viridis", output_path=None, cytobands=None, n_labels=20):
    """
    Create and save an interactive Plotly heatmap visualization (for standalone use).
    
    Args:
        mat: DataFrame with co-deletion data (genes x genes)
        title: Title for the plot
        colorscale: Plotly colorscale name (e.g., 'Viridis', 'YlOrRd', 'Blues')
        output_path: Optional path to save the figure as HTML (if None, uses default location)
        cytobands: Optional list of cytobands corresponding to genes (if provided, used instead of gene names)
        n_labels: Number of labels to show on axes (default: 20, evenly spaced)
        
    Returns:
        Plotly Figure object
    """
    fig = create_heatmap_figure(mat, title, colorscale, cytobands, n_labels)
    
    # Save plot
    if output_path is None:
        # Default: save to ../data/processed/
        script_dir = os.path.dirname(__file__)
        output_dir = os.path.join(script_dir, "..", "data", "processed")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "chr13_conditional_codeletion_heatmap.html")
    
    fig.write_html(output_path)
    
    return fig


def create_frequency_heatmap_figure(mat, title="Co-Deletion Frequency Matrix", cytobands=None, n_labels=20):
    """
    Create an interactive heatmap figure for co-deletion frequencies (Dash-compatible).
    
    Args:
        mat: DataFrame with co-deletion frequency data (genes x genes)
        title: Title for the plot
        cytobands: Optional list of cytobands corresponding to genes
        n_labels: Number of labels to show (default: 20)
        
    Returns:
        Plotly Figure object
    """
    return create_heatmap_figure(mat, title=title, colorscale="YlOrRd", cytobands=cytobands, n_labels=n_labels)


def plot_frequency_heatmap(mat, title="Co-Deletion Frequency Matrix", output_path=None, cytobands=None, n_labels=20):
    """
    Create and save an interactive heatmap for co-deletion frequencies (for standalone use).
    
    Args:
        mat: DataFrame with co-deletion frequency data (genes x genes)
        title: Title for the plot
        output_path: Optional path to save the figure as HTML
        cytobands: Optional list of cytobands corresponding to genes
        n_labels: Number of labels to show (default: 20)
        
    Returns:
        Plotly Figure object
    """
    return plot_heatmap(mat, title=title, colorscale="YlOrRd", output_path=output_path, cytobands=cytobands, n_labels=n_labels)


def create_top_pairs_figure(long_table, n=20):
    """
    Create an interactive bar plot figure of the top N co-deleted gene pairs (Dash-compatible).
    
    Args:
        long_table: Long-format DataFrame with co-deletion frequencies
        n: Number of top pairs to plot
        
    Returns:
        Plotly Figure object
    """
    top_pairs = long_table.sort_values("co_deletion_frequency", ascending=False).head(n)
    
    # Create labels for gene pairs
    pair_labels = [f"{row['gene_i'].split()[0]} - {row['gene_j'].split()[0]}" 
                   for _, row in top_pairs.iterrows()]
    
    # Create horizontal bar chart
    fig = go.Figure(data=go.Bar(
        x=top_pairs["co_deletion_frequency"],
        y=pair_labels,
        orientation='h',
        marker=dict(
            color=top_pairs["co_deletion_frequency"],
            colorscale='Blues',
            showscale=True,
            colorbar=dict(title="Frequency")
        ),
        hovertemplate='%{y}<br>Frequency: %{x:.3f}<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(text=f"Top {n} Co-deleted Gene Pairs", x=0.5, xanchor='center', font=dict(size=14)),
        xaxis_title="Co-deletion Frequency",
        yaxis_title="Gene Pairs",
        yaxis=dict(autorange="reversed"),
        width=800,
        height=600,
        plot_bgcolor='white'
    )
    
    return fig


def plot_top_pairs_barplot(long_table, n=20, output_path=None):
    """
    Create and save an interactive bar plot of the top N co-deleted gene pairs (for standalone use).
    
    Args:
        long_table: Long-format DataFrame with co-deletion frequencies
        n: Number of top pairs to plot
        output_path: Optional path to save the figure as HTML
        
    Returns:
        Plotly Figure object
    """
    fig = create_top_pairs_figure(long_table, n)
    
    if output_path:
        fig.write_html(output_path)
    
    return fig


def create_deletion_frequency_scatter(deletion_freqs, gene_metadata=None):
    """
    Create an interactive scatter plot of individual gene deletion frequencies (Dash-compatible).
    
    Args:
        deletion_freqs: Series with gene deletion frequencies (index = gene names, values = frequencies)
        gene_metadata: Optional DataFrame with columns ['hugoGeneSymbol', 'cytoband'] for ordering
        
    Returns:
        Plotly Figure object
    """
    # Prepare data
    if gene_metadata is not None:
        # Create mapping from gene name (with Entrez ID) to cytoband
        gene_to_cytoband = {}
        gene_to_symbol = {}
        
        for _, row in gene_metadata.iterrows():
            symbol = row['hugoGeneSymbol']
            cytoband = row['cytoband']
            # Find matching column in deletion_freqs (formatted as "SYMBOL (ENTREZ)")
            for col in deletion_freqs.index:
                if col.startswith(symbol + ' '):
                    gene_to_cytoband[col] = cytoband
                    gene_to_symbol[col] = symbol
                    break
        
        # Create DataFrame for plotting
        plot_data = pd.DataFrame({
            'gene': deletion_freqs.index,
            'frequency': deletion_freqs.values,
            'cytoband': [gene_to_cytoband.get(g, 'unknown') for g in deletion_freqs.index],
            'symbol': [gene_to_symbol.get(g, g.split(' ')[0]) for g in deletion_freqs.index]
        })
        
        # Sort by cytoband (already in chromosomal order from gene_metadata)
        cytoband_order = {cb: i for i, cb in enumerate(gene_metadata['cytoband'].tolist())}
        plot_data['cytoband_order'] = plot_data['cytoband'].map(lambda x: cytoband_order.get(x, 999999))
        plot_data = plot_data.sort_values('cytoband_order').reset_index(drop=True)
        
    else:
        # No metadata, just use gene index
        plot_data = pd.DataFrame({
            'gene': deletion_freqs.index,
            'frequency': deletion_freqs.values,
            'symbol': [g.split(' ')[0] for g in deletion_freqs.index]
        })
        plot_data['position'] = range(len(plot_data))
    
    # Create scatter plot
    fig = go.Figure(data=go.Scatter(
        x=list(range(len(plot_data))),
        y=plot_data['frequency'],
        mode='markers',
        marker=dict(
            size=6,
            color=plot_data['frequency'],
            colorscale='Reds',
            showscale=True,
            colorbar=dict(title='Deletion<br>Frequency'),
            line=dict(width=0.5, color='darkred')
        ),
        text=plot_data['symbol'],
        customdata=plot_data[['gene', 'cytoband']] if gene_metadata is not None else plot_data[['gene']],
        hovertemplate='<b>%{text}</b><br>' +
                      'Deletion Frequency: %{y:.3f}<br>' +
                      ('Cytoband: %{customdata[1]}<br>' if gene_metadata is not None else '') +
                      '<extra></extra>'
    ))
    
    # Update layout
    if gene_metadata is not None:
        # Show cytoband labels on x-axis (subset for readability)
        n_labels = min(20, len(plot_data))
        tick_indices = np.linspace(0, len(plot_data) - 1, n_labels, dtype=int).tolist()
        tick_labels = [plot_data.iloc[i]['cytoband'] for i in tick_indices]
        
        fig.update_xaxes(
            title="Gene Position (Chromosomal Order)",
            tickmode='array',
            tickvals=tick_indices,
            ticktext=tick_labels,
            tickangle=90
        )
    else:
        fig.update_xaxes(title="Gene Index")
    
    fig.update_yaxes(title="Deletion Frequency", range=[0, 1])
    
    fig.update_layout(
        title=dict(text="Individual Gene Deletion Frequencies", x=0.5, xanchor='center', font=dict(size=16)),
        height=400,
        plot_bgcolor='white',
        hovermode='closest'
    )
    
    return fig


def plot_deletion_frequency_scatter(deletion_freqs, gene_metadata=None, output_path=None):
    """
    Create and save an interactive scatter plot of gene deletion frequencies (for standalone use).
    
    Args:
        deletion_freqs: Series with gene deletion frequencies
        gene_metadata: Optional DataFrame with gene metadata
        output_path: Optional path to save the figure as HTML
        
    Returns:
        Plotly Figure object
    """
    fig = create_deletion_frequency_scatter(deletion_freqs, gene_metadata)
    
    if output_path:
        fig.write_html(output_path)
    
    return fig
