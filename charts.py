from flask import Flask, jsonify, render_template_string, request
import plotly.graph_objs as go
from plotly.utils import PlotlyJSONEncoder
import infrastucture.queries as queries
import json
from infrastucture.database import Database



app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Previsão LCA x Dados INMET</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <h1>Previsão LCA x Dados INMET</h1>
    <form method="get" action="/">
        <label for="station">Selecione a estação:</label>
        <select name="station" id="station">
            {% for station in stations %}
                <option value="{{ station.codigo }}" {% if station.codigo == selected_station %}selected{% endif %}>
                    {{ station.estacao }}
                </option>
            {% endfor %}
        </select>
        <label for="forecast-date">Selecione a data:</label>
        <select name="forecast-date" id="forecast-date">
            {% for forecast_date in forecast_dates %}
                 <option value="{{ forecast_date.data }}" {% if forecast_date.data|string == selected_forecast_date|string %}selected{% endif %}>
                    {{ forecast_date.data }}
                </option>        
            {% endfor %}
        </select>
        <label for="metric">Selecione a métrica:</label>
        <select name="metric" id="metric">
            <option value="temperatura" {% if selected_metric == 'temperatura' %}selected{% endif %}>Temperatura (°C)</option>
            <option value="umidade" {% if selected_metric == 'umidade' %}selected{% endif %}>Umidade (%)</option>
            <option value="chuva" {% if selected_metric == 'chuva' %}selected{% endif %}>Precipitação/Chuva (mm)</option>
        </select>
        <button type="submit">Generate Graph</button>
    </form>
    <div id="chart"></div>
    <script>
        var chartData = {{ chart_data | safe }};
        var layout = {
            title: '{{ chart_title }}',
            xaxis: {
                title: 'Data/Hora'
            },
            yaxis: {
                title: '{{ y_axis_title }}'
            },
            legend: {
                orientation: 'h',
                yanchor: 'bottom',
                y: -0.3,
                xanchor: 'center',
                x: 0.5
            },
            hovermode: 'x unified'
        };
        Plotly.newPlot('chart', chartData, layout);
    </script>
</body>
</html>
"""
STATIONS = []
FORECAST_DATES = []
with Database() as db:
    STATIONS = db.execute_query(queries.QUERY_STATIONS)
    FORECAST_DATES
    
prevision_data = []
inmet_data = []
@app.route("/", methods=["GET"])
def index():
    with Database() as db:
        changed = False
        selected_station = request.args.get("station", STATIONS[0]["codigo"])
        FORECAST_DATES = db.execute_query(queries.QUERY_LAST_PREVISION)
        
        selected_forecast_date = request.args.get("forecast-date", FORECAST_DATES[0]["data"])
        selected_metric = request.args.get("metric", "temperatura")
        
        params = { 'start_date': selected_forecast_date, 'station': selected_station }
        prevision_data = db.execute_query(queries.QUERY_PREVISION_DATA, params)
        
        inmet_data = db.execute_query(queries.QUERY_INMET_DATA, params)

    # Extract data for Previsão (forecast)
    x1 = [row['data'] for row in prevision_data]
    x2 = [row['data'] for row in inmet_data]
    
    # Define color pairs and labels for each metric
    metric_config = {
        'temperatura': {
            'color_prevision': 'blue',
            'color_inmet': 'gold',
            'label': 'Temperatura',
            'unit': '°C',
            'column': 'temperatura'
        },
        'umidade': {
            'color_prevision': 'darkgreen',
            'color_inmet': 'limegreen',
            'label': 'Umidade',
            'unit': '%',
            'column': 'umidade'
        },
        'chuva': {
            'color_prevision': 'darkviolet',
            'color_inmet': 'hotpink',
            'label': 'Precipitação/Chuva',
            'unit': 'mm',
            'column': 'chuva'
        }
    }
    
    config = metric_config[selected_metric]
    
    # Extract values for selected metric
    y1 = [row[config['column']] for row in prevision_data]
    y2 = [row[config['column']] for row in inmet_data]
    
    # Create traces for selected metric only
    # Use bar chart for precipitation/rain, line chart for others
    if selected_metric == 'chuva':
        trace1 = go.Bar(
            x=x1, 
            y=y1, 
            name=f'Previsão - {config["label"]}',
            marker=dict(color=config['color_prevision']),
            opacity=0.7
        )
        trace2 = go.Bar(
            x=x2, 
            y=y2, 
            name=f'INMET - {config["label"]}',
            marker=dict(color=config['color_inmet']),
            opacity=0.7
        )
    else:
        trace1 = go.Scatter(
            x=x1, 
            y=y1, 
            mode='lines', 
            name=f'Previsão - {config["label"]}',
            line=dict(color=config['color_prevision'], width=2)
        )
        trace2 = go.Scatter(
            x=x2, 
            y=y2, 
            mode='lines', 
            name=f'INMET - {config["label"]}',
            line=dict(color=config['color_inmet'], width=2)
        )
    
    chart_data = [trace1, trace2]
    chart_title = f'Comparação: Previsão vs INMET - {config["label"]}'
    y_axis_title = f'{config["label"]} ({config["unit"]})'
    
    return render_template_string(
        HTML_TEMPLATE, 
        chart_data=json.dumps(chart_data, cls=PlotlyJSONEncoder),
        chart_title=chart_title,
        y_axis_title=y_axis_title,
        stations=STATIONS,
        forecast_dates=FORECAST_DATES,
        selected_forecast_date=selected_forecast_date,
        selected_station=selected_station,
        selected_metric=selected_metric
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3443)