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


def create_top_pairs_table_data(conditional_matrix, deletion_freqs, joint_data, gene_metadata=None, n=20, gene_filter=None,
                                min_distance=None, max_distance=None, min_freq=None, min_pab=None, min_pba=None, min_joint=None):
    """
    Create a table showing top gene pairs with detailed statistics.
    
    Args:
        conditional_matrix: DataFrame where entry [i,j] represents P(gene_i deleted | gene_j deleted)
        deletion_freqs: Series with individual gene deletion frequencies
        joint_data: DataFrame with joint probabilities (codeletion pairs)
        gene_metadata: DataFrame with gene positions (entrezGeneId, hugoGeneSymbol, start, end)
        n: Number of top pairs to display (default: 20)
        gene_filter: Optional gene name to filter results (case-insensitive)
        min_distance: Minimum genomic distance in bp
        max_distance: Maximum genomic distance in bp
        min_freq: Minimum individual deletion frequency (for both genes)
        min_pab: Minimum P(A|B) value
        min_pba: Minimum P(B|A) value
        min_joint: Minimum P(A,B) joint probability
        
    Returns:
        Dash DataTable component
    """
    from dash import dash_table, html
    import numpy as np
    
    # Create gene position lookup if metadata provided
    gene_positions = {}
    if gene_metadata is not None and 'start' in gene_metadata.columns:
        for _, row in gene_metadata.iterrows():
            # Match genes by symbol with Entrez ID format: "SYMBOL (ENTREZ)"
            symbol = row['hugoGeneSymbol']
            entrez = int(row['entrezGeneId'])  # Ensure integer
            gene_key = f"{symbol} ({entrez})"
            gene_positions[gene_key] = {
                'start': int(row['start']),
                'end': int(row['end'])
            }
    
    # Debug: print first few gene keys and matrix columns to verify matching
    if gene_metadata is not None and len(gene_positions) > 0:
        genes = conditional_matrix.columns.tolist()
        print(f"DEBUG: First 3 metadata keys: {list(gene_positions.keys())[:3]}")
        print(f"DEBUG: First 3 matrix columns: {genes[:3]}")
        print(f"DEBUG: Total genes in positions: {len(gene_positions)}")
        print(f"DEBUG: Total genes in matrix: {len(genes)}")

    
    # Extract gene pairs with conditional probabilities
    pairs_list = []
    genes = conditional_matrix.columns.tolist()
    
    # Create a lookup dictionary for joint probabilities
    joint_lookup = {}
    if joint_data is not None and not joint_data.empty:
        for _, row in joint_data.iterrows():
            gene_i = row['gene_i']
            gene_j = row['gene_j']
            joint_prob = row['co_deletion_frequency']
            joint_lookup[(gene_i, gene_j)] = joint_prob
            joint_lookup[(gene_j, gene_i)] = joint_prob  # Symmetric
    
    for i in range(len(genes)):
        for j in range(i+1, len(genes)):  # Upper triangle only
            gene_i = genes[i]
            gene_j = genes[j]
            
            # Get conditional probabilities
            prob_i_given_j = conditional_matrix.iloc[i, j]
            prob_j_given_i = conditional_matrix.iloc[j, i]
            
            # Skip if both are NaN
            if pd.isna(prob_i_given_j) and pd.isna(prob_j_given_i):
                continue
            
            # Get individual deletion frequencies
            freq_i = deletion_freqs.get(gene_i, np.nan)
            freq_j = deletion_freqs.get(gene_j, np.nan)
            
            # Skip pairs where either gene is never deleted
            if pd.isna(freq_i) or pd.isna(freq_j) or freq_i == 0 or freq_j == 0:
                continue
            
            # Get joint probability
            joint_prob = joint_lookup.get((gene_i, gene_j), np.nan)
            
            # Calculate genomic distance
            distance_bp = np.nan
            if gene_i in gene_positions and gene_j in gene_positions:
                pos_i = gene_positions[gene_i]
                pos_j = gene_positions[gene_j]
                # Distance from start of one gene to start of the other
                distance_bp = abs(pos_i['start'] - pos_j['start'])
            
            # Use maximum conditional probability for ranking
            max_cond_prob = max(
                prob_i_given_j if not pd.isna(prob_i_given_j) else 0,
                prob_j_given_i if not pd.isna(prob_j_given_i) else 0
            )
            
            pairs_list.append({
                'Gene A': gene_i,
                'Gene B': gene_j,
                'Freq A': freq_i,
                'Freq B': freq_j,
                'P(A|B)': prob_i_given_j,
                'P(B|A)': prob_j_given_i,
                'P(A,B)': joint_prob,
                'Distance (bp)': distance_bp,
                'max_cond': max_cond_prob
            })
    
    # Convert to DataFrame
    pairs_df = pd.DataFrame(pairs_list)
    
    if pairs_df.empty:
        return html.Div(
            "No co-deletion data available",
            className="text-center text-muted p-4"
        )
    
    # Apply gene filter if provided
    if gene_filter and gene_filter.strip():
        gene_filter_upper = gene_filter.strip().upper()
        mask = (
            pairs_df['Gene A'].str.upper().str.contains(gene_filter_upper, na=False) |
            pairs_df['Gene B'].str.upper().str.contains(gene_filter_upper, na=False)
        )
        pairs_df = pairs_df[mask]
        
        if pairs_df.empty:
            return html.Div(
                f"No gene pairs found containing '{gene_filter}'",
                className="text-center text-muted p-4"
            )
    
    # Apply numerical filters
    if min_distance is not None:
        pairs_df = pairs_df[pairs_df['Distance (bp)'] >= min_distance]
    if max_distance is not None:
        pairs_df = pairs_df[pairs_df['Distance (bp)'] <= max_distance]
    if min_freq is not None:
        pairs_df = pairs_df[(pairs_df['Freq A'] >= min_freq) & (pairs_df['Freq B'] >= min_freq)]
    if min_pab is not None:
        pairs_df = pairs_df[pairs_df['P(A|B)'] >= min_pab]
    if min_pba is not None:
        pairs_df = pairs_df[pairs_df['P(B|A)'] >= min_pba]
    if min_joint is not None:
        pairs_df = pairs_df[pairs_df['P(A,B)'] >= min_joint]
    
    if pairs_df.empty:
        return html.Div(
            "No gene pairs match the specified filters",
            className="text-center text-muted p-4"
        )
    
    # Sort by maximum conditional probability
    pairs_df = pairs_df.sort_values('max_cond', ascending=False)
    
    # Drop the sorting column for display
    display_data = pairs_df.drop(columns=['max_cond']).copy()
    
    # Convert to dict for DataTable (keep numeric values)
    table_records = display_data.to_dict('records')
    
    # Create DataTable with all data, but display only n rows per page
    table = dash_table.DataTable(
        data=table_records,
        columns=[
            {'name': 'Gene A', 'id': 'Gene A', 'type': 'text'},
            {'name': 'Gene B', 'id': 'Gene B', 'type': 'text'},
            {'name': 'Distance (bp)', 'id': 'Distance (bp)', 'type': 'numeric', 'format': {'specifier': '.2e'}},
            {'name': 'Freq Gene A', 'id': 'Freq A', 'type': 'numeric', 'format': {'specifier': '.2%'}},
            {'name': 'Freq Gene B', 'id': 'Freq B', 'type': 'numeric', 'format': {'specifier': '.2%'}},
            {'name': 'P(A|B)', 'id': 'P(A|B)', 'type': 'numeric', 'format': {'specifier': '.2%'}},
            {'name': 'P(B|A)', 'id': 'P(B|A)', 'type': 'numeric', 'format': {'specifier': '.2%'}},
            {'name': 'P(A,B)', 'id': 'P(A,B)', 'type': 'numeric', 'format': {'specifier': '.2%'}}
        ],
        style_table={'overflowX': 'auto'},
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '14px'
        },
        style_header={
            'backgroundColor': '#f8f9fa',
            'fontWeight': 'bold',
            'borderBottom': '2px solid #dee2e6'
        },
        style_data_conditional=[
            {
                'if': {'row_index': 'odd'},
                'backgroundColor': '#f8f9fa'
            }
        ],
        page_size=n,
        page_action='native',
        sort_action='native',
        filter_action='native'
    )
    
    return table


def create_top_conditional_pairs_figure(conditional_matrix, n=10, gene_filter=None):
    """
    Create a bar plot showing top gene pairs by conditional co-deletion frequency.
    
    This function extracts the top N gene pairs from the conditional probability 
    matrix P(gene_i | gene_j) and displays them as a horizontal bar chart.
    
    Args:
        conditional_matrix: DataFrame where entry [i,j] represents P(gene_i deleted | gene_j deleted)
        n: Number of top pairs to display (default: 10)
        gene_filter: Optional gene name to filter results (case-insensitive)
        
    Returns:
        Plotly Figure object
    """
    import numpy as np
    
    # Extract upper triangle (excluding diagonal) to avoid duplicates
    # For conditional matrix, P(A|B) != P(B|A), so we'll take the maximum of the two
    pairs_list = []
    
    genes = conditional_matrix.columns.tolist()
    
    for i in range(len(genes)):
        for j in range(i+1, len(genes)):  # Upper triangle only
            gene_i = genes[i]
            gene_j = genes[j]
            
            # Get both conditional probabilities
            prob_i_given_j = conditional_matrix.iloc[i, j]
            prob_j_given_i = conditional_matrix.iloc[j, i]
            
            # Skip NaN values
            if pd.isna(prob_i_given_j) and pd.isna(prob_j_given_i):
                continue
            
            # Use the maximum conditional probability and note the direction
            if pd.isna(prob_i_given_j):
                max_prob = prob_j_given_i
                primary_gene = gene_j
                secondary_gene = gene_i
            elif pd.isna(prob_j_given_i):
                max_prob = prob_i_given_j
                primary_gene = gene_i
                secondary_gene = gene_j
            elif prob_i_given_j >= prob_j_given_i:
                max_prob = prob_i_given_j
                primary_gene = gene_i
                secondary_gene = gene_j
            else:
                max_prob = prob_j_given_i
                primary_gene = gene_j
                secondary_gene = gene_i
            
            pairs_list.append({
                'primary_gene': primary_gene,
                'secondary_gene': secondary_gene,
                'conditional_probability': max_prob,
                'pair_label': f"{primary_gene} | {secondary_gene}"
            })
    
    # Convert to DataFrame and sort by conditional probability
    pairs_df = pd.DataFrame(pairs_list)
    
    if pairs_df.empty:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No co-deletion data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Apply gene filter if provided
    if gene_filter and gene_filter.strip():
        gene_filter_upper = gene_filter.strip().upper()
        # Filter for pairs where either gene contains the search term
        mask = (
            pairs_df['primary_gene'].str.upper().str.contains(gene_filter_upper, na=False) |
            pairs_df['secondary_gene'].str.upper().str.contains(gene_filter_upper, na=False)
        )
        pairs_df = pairs_df[mask]
        
        if pairs_df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text=f"No gene pairs found containing '{gene_filter}'",
                xref="paper", yref="paper",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=16)
            )
            return fig
    
    top_pairs = pairs_df.sort_values("conditional_probability", ascending=False).head(n)
    
    # Create horizontal bar plot
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=top_pairs['conditional_probability'],
        y=top_pairs['pair_label'],
        orientation='h',
        marker=dict(
            color=top_pairs['conditional_probability'],
            colorscale='Blues',
            showscale=True,
            colorbar=dict(title="P(A|B)")
        ),
        hovertemplate='<b>%{y}</b><br>Conditional Probability: %{x:.3f}<extra></extra>'
    ))
    
    # Update title based on whether filter is applied
    if gene_filter and gene_filter.strip():
        title = f"Top {n} Gene Pairs Containing '{gene_filter}' by Conditional Co-deletion Frequency"
    else:
        title = f"Top {n} Gene Pairs by Conditional Co-deletion Frequency"
    
    fig.update_layout(
        title=title,
        xaxis_title="Conditional Probability P(Gene A deleted | Gene B deleted)",
        yaxis_title="Gene Pair (A | B)",
        yaxis={'categoryorder': 'total ascending'},
        template='plotly_white',
        height=max(400, n * 30 + 100),
        margin=dict(l=200, r=50, t=80, b=80)
    )
    
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


def create_distance_frequency_scatter(conditional_matrix, gene_metadata, min_distance=0, gene_filter=None,
                                       max_distance=None, min_pba=None, max_pba=None):
    """
    Create a scatter plot showing relationship between genomic distance and conditional co-deletion probability.
    
    Plots Distance (bp) vs P(B|A) for all gene pairs where both metrics are available.
    Excludes pairs where P(B|A) = 0 to reduce dataset size and focus on actual co-deletions.
    
    Args:
        conditional_matrix: DataFrame where entry [i,j] represents P(gene_i deleted | gene_j deleted)
        gene_metadata: DataFrame with gene positions (entrezGeneId, hugoGeneSymbol, start, end)
        min_distance: Minimum distance in bp to include (default: 0)
        gene_filter: Optional gene symbol to filter for (shows only pairs where this is gene A)
        max_distance: Maximum distance in bp to include
        min_pba: Minimum P(B|A) value to include
        max_pba: Maximum P(B|A) value to include
        
    Returns:
        Plotly Figure object
    """
    # Create gene position lookup
    gene_positions = {}
    if gene_metadata is not None and 'start' in gene_metadata.columns:
        for _, row in gene_metadata.iterrows():
            symbol = row['hugoGeneSymbol']
            entrez = int(row['entrezGeneId'])
            gene_key = f"{symbol} ({entrez})"
            gene_positions[gene_key] = {
                'start': int(row['start']),
                'end': int(row['end'])
            }
    
    if not gene_positions:
        # Return empty figure with message
        fig = go.Figure()
        fig.add_annotation(
            text="No genomic position data available",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Extract gene pairs with both distance and conditional probability
    pairs_data = []
    genes = conditional_matrix.columns.tolist()
    
    for i in range(len(genes)):
        for j in range(i+1, len(genes)):  # Upper triangle only to avoid duplicates
            gene_i = genes[i]
            gene_j = genes[j]
            
            # Get conditional probabilities (both directions)
            # Matrix entry [row, col] = P(row | col) = P(row deleted | col deleted)
            # So conditional_matrix.iloc[i, j] = P(gene_i | gene_j)
            # And conditional_matrix.iloc[j, i] = P(gene_j | gene_i)
            prob_i_given_j = conditional_matrix.iloc[i, j]  # P(gene_i | gene_j)
            prob_j_given_i = conditional_matrix.iloc[j, i]  # P(gene_j | gene_i)
            
            # Skip if both are NaN or both are 0
            if (pd.isna(prob_i_given_j) or prob_i_given_j == 0) and \
               (pd.isna(prob_j_given_i) or prob_j_given_i == 0):
                continue
            
            # Calculate genomic distance
            if gene_i in gene_positions and gene_j in gene_positions:
                pos_i = gene_positions[gene_i]['start']
                pos_j = gene_positions[gene_j]['start']
                
                # Skip if either position is 0 (no coordinate data)
                if pos_i == 0 or pos_j == 0:
                    continue
                
                distance_bp = abs(pos_i - pos_j)
                
                # Add data point for P(gene_j | gene_i) if non-zero
                # When gene_i is "A", we want P(B|A) which is P(gene_j | gene_i)
                if not pd.isna(prob_j_given_i) and prob_j_given_i > 0:
                    gene_a_symbol = gene_i.split()[0]
                    gene_b_symbol = gene_j.split()[0]
                    # Apply gene filter if specified (filter for gene A)
                    if gene_filter is None or gene_a_symbol.upper() == gene_filter.upper():
                        # Apply deletion frequency filter for gene A
                        if freq_a is not None and deletion_freqs is not None:
                            gene_a_freq = deletion_freqs.get(gene_i, 0)
                            if gene_a_freq < freq_a:
                                pass  # Skip this point
                            else:
                                pairs_data.append({
                                    'gene_a': gene_i,
                                    'gene_b': gene_j,
                                    'distance_bp': distance_bp,
                                    'conditional_prob': prob_j_given_i,
                                    'direction': f"{gene_b_symbol} | {gene_a_symbol}"
                                })
                        else:
                            pairs_data.append({
                                'gene_a': gene_i,
                                'gene_b': gene_j,
                                'distance_bp': distance_bp,
                                'conditional_prob': prob_j_given_i,
                                'direction': f"{gene_b_symbol} | {gene_a_symbol}"
                            })
                
                # Add data point for P(gene_i | gene_j) if non-zero
                # When gene_j is "A", we want P(B|A) which is P(gene_i | gene_j)
                if not pd.isna(prob_i_given_j) and prob_i_given_j > 0:
                    gene_a_symbol = gene_j.split()[0]
                    gene_b_symbol = gene_i.split()[0]
                    # Apply gene filter if specified (filter for gene A)
                    if gene_filter is None or gene_a_symbol.upper() == gene_filter.upper():
                        # Apply deletion frequency filter for gene A
                        if freq_a is not None and deletion_freqs is not None:
                            gene_a_freq = deletion_freqs.get(gene_j, 0)
                            if gene_a_freq < freq_a:
                                pass  # Skip this point
                            else:
                                pairs_data.append({
                                    'gene_a': gene_j,
                                    'gene_b': gene_i,
                                    'distance_bp': distance_bp,
                                    'conditional_prob': prob_i_given_j,
                                    'direction': f"{gene_b_symbol} | {gene_a_symbol}"
                                })
                        else:
                            pairs_data.append({
                                'gene_a': gene_j,
                                'gene_b': gene_i,
                                'distance_bp': distance_bp,
                                'conditional_prob': prob_i_given_j,
                                'direction': f"{gene_b_symbol} | {gene_a_symbol}"
                            })
    
    if not pairs_data:
        fig = go.Figure()
        fig.add_annotation(
            text="No data points with both distance and non-zero conditional probability",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16)
        )
        return fig
    
    # Convert to DataFrame
    pairs_df = pd.DataFrame(pairs_data)
    
    # Create scatter plot
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=pairs_df['distance_bp'],
        y=pairs_df['conditional_prob'],
        mode='markers',
        marker=dict(
            size=4,
            color=pairs_df['conditional_prob'],
            colorscale='Viridis',
            showscale=True,
            colorbar=dict(title='P(B|A)'),
            opacity=0.6,
            line=dict(width=0.5, color='white')
        ),
        text=pairs_df['direction'],
        hovertemplate='<b>%{text}</b><br>' +
                      'Distance: %{x:.2e} bp<br>' +
                      'P(B|A): %{y:.3f}<br>' +
                      '<extra></extra>'
    ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text="Genomic Distance vs Conditional Co-deletion Probability",
            x=0.5,
            xanchor='center',
            font=dict(size=16)
        ),
        xaxis=dict(
            title="Genomic Distance (bp)",
            type='log',  # Log scale often better for genomic distances
            tickformat='.0f'
        ),
        yaxis=dict(
            title="Conditional Probability P(B|A)",
            range=[0, 1]
        ),
        height=600,
        width=900,
        plot_bgcolor='white',
        hovermode='closest',
        showlegend=False
    )
    
    # Add annotation with data point count
    fig.add_annotation(
        text=f"n = {len(pairs_df):,} gene pairs (P(B|A) > 0)",
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        showarrow=False,
        font=dict(size=12),
        bgcolor="rgba(255,255,255,0.8)",
        bordercolor="black",
        borderwidth=1
    )
    
    return fig


def plot_distance_frequency_scatter(conditional_matrix, gene_metadata, min_distance=0, output_path=None):
    """
    Create and save a scatter plot of genomic distance vs conditional probability (for standalone use).
    
    Args:
        conditional_matrix: DataFrame where entry [i,j] represents P(gene_i deleted | gene_j deleted)
        gene_metadata: DataFrame with gene positions
        min_distance: Minimum distance in bp to include (default: 0)
        output_path: Optional path to save the figure as HTML
        
    Returns:
        Plotly Figure object
    """
    fig = create_distance_frequency_scatter(conditional_matrix, gene_metadata, min_distance)
    
    if output_path:
        fig.write_html(output_path)
    
    return fig
