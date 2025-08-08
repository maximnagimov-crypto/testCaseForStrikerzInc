import pandas as pd
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
from datetime import datetime
import os
def prepare_file(input_file, output_file):
    replacements = [
        (" [", "|"),
        ("] (", "|"),
        (") | IP: ", "|"),
        (" | UA: ", "|"),
        (" | Event: ", "|"),
        (" /a", "|a"),
        (" - ", "|"),
        (" | Payload: {\"\"status\"\": \"\"", "|"),
        ("\"\", \"\"", "|"),
        ("data\"\": {\"\"items\"\": ", ""),
        ("}", ""),
        ("\"", "")
    ]

    with open(input_file, 'r', encoding='utf-8') as infile, \
         open(output_file, 'w', encoding='utf-8') as outfile:
        next(infile)
        for line in infile:
            for old, new in replacements:
                line = line.replace(old, new)
            outfile.write(line)

def parse_and_plot_logs(file_path):
    df = pd.read_csv(
        file_path,
        sep='|',
        header=None,
        usecols=[0, 1, 2, 5, 6, 7],
        dtype={1: str, 2: str, 5: str, 6: str, 7: str}
    )
    columns = {0: 'timestamp',1: 'level',2: 'source',5: 'method',6: 'url',7: 'code'}
    df = df.rename(columns=columns)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    fields = ['level', 'source', 'method', 'url', 'code']
    figures = []
    for field in fields:
        plot_df = df[['timestamp', field]].copy()
        plot_df[field] = plot_df[field].fillna('N/A').astype(str)
        top_values = plot_df[field].value_counts().nlargest(15).index
        plot_df = plot_df[plot_df[field].isin(top_values)]
        plot_df = plot_df.groupby(
            [pd.Grouper(key='timestamp', freq='1min'), field]
        ).size().reset_index(name='count')
        
        fig = px.line(
            plot_df,
            x='timestamp',
            y='count',
            color=field,
            labels={
                'timestamp': 'Время',
                'count': 'Количество',
                field: 'Значение поля'
            },
            template='plotly_white'
        )
        
        fig.update_layout(
            hovermode='x unified',
            legend_title_text=field,
            xaxis_title='Время',
            yaxis_title='Количество',
            height=400,
            width=1200,
            margin=dict(t=40, b=20, l=20, r=20)
        )
        
        fig.update_traces(hovertemplate='<b>%{x|%Y-%m-%d %H:%M}</b><br>Событий: %{y}')
        fig.update_xaxes(
            tickformat='%Y-%m-%d %H:%M',
            rangeslider_visible=True,
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1 час", step="hour", stepmode="backward"),
                    dict(count=6, label="6 часов", step="hour", stepmode="backward"),
                    dict(count=1, label="1 день", step="day", stepmode="backward"),
                    dict(step="all")
                ])
            )
        )
        figures.append(fig)

    with open(f'{'log_graphics.html'}', 'w', encoding='utf-8') as f:
        f.write('<html><head><meta charset="utf-8"><title>Логи</title></head><body>')
        f.write('<h1 style="text-align: center; font-family: Arial;">Логи</h1>')
        for i, fig in enumerate(figures):
            f.write(fig.to_html(full_html=False, include_plotlyjs='cdn' if i == 0 else False))
            f.write('<hr style="margin: 40px 0;">')
        f.write('</body></html>')

def parse_and_plot_metrics(file_path):
    df = pd.read_csv(
        file_path,
        parse_dates=['timestamp'],
        date_parser=lambda x: pd.to_datetime(x, format='%Y-%m-%d %H:%M:%S')
    )
    numeric_cols = ['rps', 'cpu_usage', 'latency_ms', 'errors_per_minute']
    df[numeric_cols] = df[numeric_cols].round(2)
    fig = make_subplots(
        rows=4, 
        cols=1,
        shared_xaxes=True,
        vertical_spacing=0.05,
        subplot_titles=(
            'Requests per second', 
            'CPU Usage (%)', 
            'Latency (ms)', 
            'Errors per minute'
        )
    )
    colors = ['blue', 'red', 'green', 'orange']
    metrics = ['rps', 'cpu_usage', 'latency_ms', 'errors_per_minute']
    for i, (col, color) in enumerate(zip(metrics, colors)):
        fig.add_trace(
            go.Scatter(
                x=df['timestamp'],
                y=df[col],
                mode='lines',
                line=dict(color=color, width=1.5),
                name=col
            ),
            row=i+1,
            col=1
        )
    fig.update_layout(
        title_text='Метрики производительности',
        height=900,
        showlegend=False,
        hovermode='x unified'
    )
    fig.update_xaxes(tickformat='%m-%d %H:%M')
    fig.write_html('metrics_graphics.html')

if __name__ == "__main__":
    prepare_file("enriched_service_logs.csv", "enriched_service_logs_prepared.csv")
    parse_and_plot_metrics("load_test_metrics.csv")
    parse_and_plot_logs("enriched_service_logs_prepared.csv")