from flask import Flask, jsonify, render_template_string, request
import plotly.graph_objs as go
from plotly.utils import PlotlyJSONEncoder
import json
from database import Database
from datetime import datetime
app = Flask(__name__)

# HTML template for rendering the chart with a station filter
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Temperature Chart</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
</head>
<body>
    <h1>Temperature Chart</h1>
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
                 <option value="{{ forecast_date.data }}" {% if forecast_date.data == selected_forecast_date %}selected{% endif %}>
                    {{ forecast_date.data }}
                </option>        
            {% endfor %}
        </select>
        <button type="submit">Generate Graph</button>
    </form>
    <div id="chart"></div>
    <script>
        var chartData = {{ chart_data | safe }};
        Plotly.newPlot('chart', chartData);
    </script>
</body>
</html>
"""

@app.route("/", methods=["GET"])
def index():
    # Initialize the database connection
    with Database() as db:
        # Fetch the list of stations
        station_query = """
        SELECT codigo, nome as estacao FROM inmet.estacoes
        WHERE EXISTS(SELECT 1 FROM inmet.dados_estacoes WHERE estacao = codigo)
        ORDER BY nome
        """
        stations = db.execute_query(station_query)
        
        selected_station = request.args.get("station", stations[0]["codigo"])
        
        forecast_dates_query = """
        SELECT data_inicio data FROM inmet.previsao ORDER BY data_inicio DESC;
        """
        
        forecast_dates = db.execute_query(forecast_dates_query)
        
        selected_forecast_date = request.args.get("forecast-date", forecast_dates[0]["data"])
        
        
        query1 = f"""
        SELECT
            make_timestamp(
                    EXTRACT(YEAR FROM data)::int,
                    EXTRACT(month FROM data)::int,
                    EXTRACT(day FROM data)::int,
                    SUBSTRING(utc, 1, 2)::int,
                    SUBSTRING(utc, 3, 4)::int,
                    0) data,
            temperatura
        FROM inmet.dados_detalhados_previsao ddp
        INNER JOIN inmet.previsao p on ddp.previsao_id = p.id
        WHERE p.data_inicio = '{selected_forecast_date}' AND estacao = '{selected_station}';
        """
        data1 = db.execute_query(query1)
        
        query2 = f"""
        SELECT
            make_timestamp(
                    EXTRACT(YEAR FROM data)::int,
                    EXTRACT(month FROM data)::int,
                    EXTRACT(day FROM data)::int,
                    SUBSTRING(utc, 1, 2)::int,
                    SUBSTRING(utc, 3, 4)::int,
                    0
            ) data,
            temperatura
        FROM inmet.dados_estacoes
        WHERE estacao = '{selected_station}' AND data BETWEEN '{selected_forecast_date}' AND  '{selected_forecast_date}'::date + INTERVAL '7 DAYS';;
        """
        data2 = db.execute_query(query2)
    
    x1 = [row['data'] for row in data1]
    y1 = [row['temperatura'] for row in data1]
    x2 = [row['data'] for row in data2]
    y2 = [row['temperatura'] for row in data2]
    
    trace1 = go.Scatter(x=x1, y=y1, mode='lines', name='Previsão')
    trace2 = go.Scatter(x=x2, y=y2, mode='lines', name='INMET')
    
    chart_data = [trace1, trace2]
    
    return render_template_string(
        HTML_TEMPLATE, 
        chart_data=json.dumps(chart_data, cls=PlotlyJSONEncoder),
        stations=stations,
        forecast_dates=forecast_dates,
        selected_forecast_date= selected_forecast_date,
        selected_station=selected_station
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3443)