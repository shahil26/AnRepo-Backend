from google import generativeai as genai
from gemini.config import model
import os, textwrap, tempfile

def pipeline(request_body: dict):
    files = request_body.get('files')
    custom_query = request_body.get('custom_query')
    viz_type = request_body.get('viz_type')
    previous_viz = request_body.get('previous_viz')
    uploaded_files = create_and_upload_temp_file(files)
    final_query = format_data(uploaded_files, custom_query, viz_type, previous_viz)
    visualization_json = process_data(final_query)
    remove_file_from_gemini(uploaded_files)
    return visualization_json

def create_and_upload_temp_file(files: list[object]):
    uploaded_files = []
    for file in files:
        with tempfile.NamedTemporaryFile(delete=False) as temp_media:
            temp_media.write(file[0].read())
            try:
                upload_file = genai.upload_file(temp_media.name, mime_type=file[1])
                uploaded_files.append(upload_file)
            except Exception as e:
                raise e
            
    if os.path.exists(temp_media.name):
        os.remove(temp_media.name)
    return uploaded_files

def remove_file_from_gemini(uploaded_files: list[object]):
    for file in uploaded_files:
        file.delete()

def format_data(files: list[object], custom_query: str, viz_type: str, previous_viz: str):
    if viz_type.lower() == 'bar_chart':
        prompt = '''
        Assume yourself to be an expert at creating stunning and appealing data visualisations from given data points.

        He wants you to create a bar chart using Chart.js library. He has the library installed and needs your help in filling the parameters.

        He also has some custom requirements which he has given to you:''' + custom_query + '''

        Please return a JSON object with the following requirements:

        - Parameters to fill in the Chart.js library so that it can be used by the client to create visualisations.
        - If the user query is not sufficient or ambiguous, interpret to the best of your abilities and create a bar chart accordingly.
        - You may take some liberty in handling the chart parameters. You may include more parameters which are present in Chart.js library.
        - IMPORTANT: Don’t hallucinate.

        The JSON structure should be strictly as follows:

        {
        "type": "bar",
        "data": {
        "labels": [/* array of labels, e.g., ["January", "February", "March", "April", "May"] */],
        "datasets": [
        {
        "label": "/* Dataset 1 label */",
        "data": [/* array of data values for Dataset 1, e.g., [30, 45, 25, 60, 40] */],
        "backgroundColor": [/* array or single color, e.g., "rgba(255, 99, 132, 0.2)" */],
        "borderColor": [/* array or single color, e.g., "rgba(255, 99, 132, 1)" */],
        "borderWidth": 2,
        "hoverBackgroundColor": "/* hover background color, e.g., 'rgba(255, 159, 64, 0.2)' */",
        "hoverBorderColor": "/* hover border color, e.g., 'rgba(255, 159, 64, 1)' */",
        "hoverBorderWidth": 3,
        "barThickness": 20,
        "maxBarThickness": 30,
        "minBarLength": 5,
        "borderRadius": 4,
        "barPercentage": 0.9,
        "categoryPercentage": 0.8,
        "indexAxis": "x",
        "stack": "/* stack identifier, e.g., 'Stack 1' */"
        },
        {
        "label": "/* Dataset 2 label */",
        "data": [/* array of data values for Dataset 2, e.g., [20, 35, 40, 55, 30] */],
        "backgroundColor": "/* background color, e.g., 'rgba(255, 159, 64, 0.2)' */",
        "borderColor": "/* border color, e.g., 'rgba(255, 159, 64, 1)' */",
        "borderWidth": 2,
        "barPercentage": 0.9,
        "categoryPercentage": 0.8,
        "stack": "/* stack identifier, e.g., 'Stack 1' */"
        }
        ]
        },
        "options": {
        "responsive": true,
        "plugins": {
        "legend": {
        "display": true,
        "position": "/* legend position, e.g., 'top' */"
        },
        "title": {
        "display": true,
        "text": "/* chart title, e.g., 'Custom Bar Chart Example' */"
        }
        },
        "scales": {
        "x": {
        "stacked": true,
        "grid": {
        "offset": true
        }
        },
        "y": {
        "stacked": true,
        "beginAtZero": true
        }
        },
        "elements": {
        "bar": {
        "borderSkipped": "/* border skipped, e.g., 'start' */",
        "inflateAmount": "/* inflate amount, e.g., 'auto' */"
        }
        },
        "interaction": {
        "mode": "index",
        "intersect": false
        }
        }
        }

        IMPORTANT: Only return a single piece of valid JSON text.

        The file given by your client is:
        '''

        final_query = [prompt] + files

    elif viz_type.lower() == 'area_chart':

        prompt = '''
        Assume yourself to be an expert at creating stunning and appealing data visualizations from given data points.

        He wants you to create an area chart using the Chart.js library. He has the library installed and needs your help in filling the parameters.

        Please return a JSON object with the following requirements:''' + custom_query + '''

        Parameters to fill in the Chart.js library so that it can be used by the client to create an area chart visualization. The chart should display areas filled between datasets or between a dataset and a boundary. The JSON structure should be as follows:

        json
        Copy code
        {
        "type": "line",
        "data": {
        "labels": [
        /* array of labels, e.g., ["January", "February", "March"] */
        ],
        "datasets": [
        {
        "label": "/* Dataset label, e.g., 'My First Dataset' */",
        "data": [
        /* array of data points, e.g., [65, 59, 80, 81, 56, 55, 40] */
        ],
        "backgroundColor": "rgba(75, 192, 192, 0.2)",  /* fill color */
        "borderColor": "rgba(75, 192, 192, 1)",        /* border color */
        "borderWidth": 1,
        "fill": {
        "target": "origin",                          /* fill mode: 'origin', dataset index, or boundaries */
        "above": "rgb(75, 192, 192)",                /* fill color above the boundary */
        "below": "rgb(255, 99, 132)"                 /* fill color below the boundary */
        },
        "tension": 0.4                                 /* line tension, controls the curve of the line */
        }
        ]
        },
        "options": {
        "responsive": true,
        "plugins": {
        "legend": {
        "display": true,
        "position": "top"
        },
        "title": {
        "display": true,
        "text": "/* Chart title, e.g., 'Area Chart Example' */"
        },
        "filler": {
        "propagate": true                              /* propagation of the fill to other datasets */
        }
        },
        "scales": {
        "x": {
        "beginAtZero": true
        },
        "y": {
        "beginAtZero": true
        }
        }
        }
        }
        IMPORTANT: Only return a single piece of valid JSON text.

        The file given by your client is:
        '''

        final_query = [prompt] + files
    
    elif viz_type.lower() == 'bubble_chart':

        prompt = '''
        Assume yourself to be an expert at creating stunning and appealing data visualizations from given data points.

        He wants you to create a bubble chart using the Chart.js library. He has the library installed and needs your help in filling the parameters.

        Please return a JSON object with the following requirements:''' + custom_query + '''

        Parameters to fill in the Chart.js library so that it can be used by the client to create a bubble chart visualization. The chart should display data points with three dimensions: x (horizontal), y (vertical), and r (bubble radius). The JSON structure should be as follows:

        json
        Copy code
        {
        "type": "bubble",
        "data": {
        "datasets": [
        {
        "label": "/* Dataset label, e.g., 'First Dataset' */",
        "data": [
        {
        "x": 20,  /* X value */
        "y": 30,  /* Y value */
        "r": 15   /* Bubble radius in pixels */
        },
        {
        "x": 40,
        "y": 10,
        "r": 10
        }
        ],
        "backgroundColor": "rgb(255, 99, 132)",  /* bubble background color */
        "borderColor": "rgba(0, 0, 0, 0.1)",     /* bubble border color */
        "borderWidth": 1                        /* border width in pixels */
        }
        ]
        },
        "options": {
        "responsive": true,
        "plugins": {
        "legend": {
        "display": true,
        "position": "top"
        },
        "title": {
        "display": true,
        "text": "/* Chart title, e.g., 'Bubble Chart Example' */"
        }
        },
        "scales": {
        "x": {
        "beginAtZero": true
        },
        "y": {
        "beginAtZero": true
        }
        },
        "elements": {
        "point": {
        "radius": 5,                          /* default bubble radius */
        "backgroundColor": "rgb(0, 0, 255)",  /* default color */
        "borderColor": "rgb(0, 0, 0)",        /* border color */
        "borderWidth": 1                      /* border width */
        }
        }
        }
        }
        IMPORTANT: Only return a single piece of valid JSON text.

        The file given by your client is:
        '''

        final_query = [prompt] + files
    
    elif viz_type.lower() == 'donut_chart':

        prompt = '''
        Assume yourself to be an expert at creating stunning and appealing data visualizations from given data points.

        He wants you to create a doughnut chart using the Chart.js library. He has the library installed and needs your help in filling the parameters.

        Please return a JSON object with the following requirements:''' + custom_query + '''

        Parameters to fill in the Chart.js library so that it can be used by the client to create visualizations. The chart should display segments with customizable styles. The JSON structure should be as follows:
        {
        "type": "doughnut",
        "data": {
        "labels": [
        /* array of labels, e.g., ["Red", "Blue", "Yellow"] */
        ],
        "datasets": [
        {
        "label": "/* Dataset label, e.g., 'My First Dataset' */",
        "data": [
        /* array of data points, e.g., [300, 50, 100] */
        ],
        "backgroundColor": [
        /* array of segment colors, e.g., ['rgb(255, 99, 132)', 'rgb(54, 162, 235)', 'rgb(255, 205, 86)'] */
        ],
        "hoverOffset": 4,
        "borderColor": "/* border color, e.g., '#fff' */",
        "borderWidth": 2,
        "borderAlign": "/* border alignment, e.g., 'center' or 'inner' */",
        "borderRadius": 0,
        "offset": 0,
        "spacing": 0,
        "weight": 1
        }
        ]
        },
        "options": {
        "responsive": true,
        "plugins": {
        "legend": {
        "display": true,
        "position": "/* legend position, e.g., 'top' */"
        },
        "title": {
        "display": true,
        "text": "/* chart title, e.g., 'Doughnut Chart Example' */"
        }
        },
        "cutout": "50%",
        "rotation": 0,
        "circumference": 360,
        "animation": {
        "animateRotate": true,
        "animateScale": false
        },
        "elements": {
        "arc": {
        "borderCapStyle": "/* border cap style, e.g., 'butt' */",
        "borderDash": [/* array of dash lengths, e.g., [5, 5] */],
        "borderDashOffset": 0.0,
        "borderJoinStyle": "/* border join style, e.g., 'miter' */",
        "borderWidth": 2,
        "hoverBackgroundColor": "/* hover background color, e.g., 'rgba(255, 159, 64, 1)' */",
        "hoverBorderColor": "/* hover border color, e.g., 'rgba(255, 159, 64, 1)' */",
        "hoverBorderWidth": 2,
        "hoverOffset": 4
        }
        }
        }
        }
        IMPORTANT: Only return a single piece of valid JSON text.

        The file given by your client is:
        '''

        final_query = [prompt] + files
    
    elif viz_type.lower() == 'pie_chart':

        prompt = '''
        Assume yourself to be an expert at creating stunning and appealing data visualizations from given data points.

        He wants you to create a pie chart using the Chart.js library. He has the library installed and needs your help in filling the parameters.

        Please return a JSON object with the following requirements:''' + custom_query + '''

        Parameters to fill in the Chart.js library so that it can be used by the client to create visualizations.
        The JSON structure should be strictly as follows:

        json
        Copy code
        {
        "type": "pie",
        "data": {
        "labels": [/* array of labels, e.g., ["Red", "Blue", "Yellow", "Green", "Purple", "Orange"] */],
        "datasets": [
        {
        "label": "/* Dataset label, e.g., 'Pie Dataset' */",
        "data": [/* array of data values, e.g., [10, 20, 30, 15, 25, 35] */],
        "backgroundColor": [/* array of colors for each section, e.g., ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"] */],
        "borderColor": [/* array or single color for border, e.g., ["#FFFFFF"] */],
        "borderWidth": 1,
        "hoverBackgroundColor": [/* array of hover colors for each section, e.g., ["#FF6384", "#36A2EB", "#FFCE56", "#4BC0C0", "#9966FF", "#FF9F40"] */],
        "hoverBorderColor": [/* array or single hover border color, e.g., "#FFFFFF" */],
        "hoverBorderWidth": 2,
        "offset": 0
        }
        ]
        },
        "options": {
        "responsive": true,
        "plugins": {
        "legend": {
        "display": true,
        "position": "top"
        },
        "title": {
        "display": true,
        "text": "/* Chart title, e.g., 'Pie Chart Example' */"
        }
        },
        "animation": {
        "animateScale": true,
        "animateRotate": true
        },
        "interaction": {
        "mode": "index",
        "intersect": false
        }
        }
        }
        IMPORTANT: Only return a single piece of valid JSON text.

        The file given by your client is:
        '''

        final_query = [prompt] + files
    
    elif viz_type.lower() == 'line_chart':

        prompt = '''
        Assume yourself to be an expert at creating stunning and appealing data visualizations from given data points.

        He wants you to create a line chart using the Chart.js library. He has the library installed and needs your help in filling the parameters.

        Please return a JSON object with the following requirements:''' + custom_query + '''

        Parameters to fill in the Chart.js library so that it can be used by the client to create visualizations. The chart should display data points connected by lines, with the option to customize line and point styles. The JSON structure should be as follows:

        json
        Copy code
        {
        "type": "line",
        "data": {
        "labels": [
        /* array of labels, e.g., ["Label1", "Label2", "Label3", "Label4", "Label5", "Label6", "Label7"] */
        ],
        "datasets": [
        {
        "label": "/* Dataset label, e.g., 'My First Dataset' */",
        "data": [
        /* array of data points in the format { "x": value, "y": value }, e.g., [{ "x": 1, "y": 45 }, { "x": 2, "y": 70 }, { "x": 3, "y": 55 }, { "x": 4, "y": 90 }, { "x": 5, "y": 65 }, { "x": 6, "y": 85 }, { "x": 7, "y": 75 }] */
        ],
        "fill": false,
        "borderColor": "/* line color, e.g., 'rgb(75, 192, 192)' */",
        "borderWidth": 2,
        "tension": 0.1,
        "backgroundColor": "/* background color, e.g., 'rgba(75, 192, 192, 0.2)' */",
        "pointBackgroundColor": "/* point background color, e.g., 'rgb(75, 192, 192)' */",
        "pointBorderColor": "/* point border color, e.g., 'rgb(255, 255, 255)' */",
        "pointBorderWidth": 1,
        "pointRadius": 3,
        "pointHoverRadius": 4,
        "pointHoverBackgroundColor": "/* point hover background color, e.g., 'rgba(255, 159, 64, 1)' */",
        "pointHoverBorderColor": "/* point hover border color, e.g., 'rgba(255, 159, 64, 1)' */",
        "pointHoverBorderWidth": 2,
        "showLine": true,
        "spanGaps": false,
        "stepped": false
        }
        ]
        },
        "options": {
        "responsive": true,
        "plugins": {
        "legend": {
        "display": true,
        "position": "/* legend position, e.g., 'top' */"
        },
        "title": {
        "display": true,
        "text": "/* chart title, e.g., 'Line Chart Example' */"
        }
        },
        "scales": {
        "x": {
        "type": "linear",
        "title": {
        "display": true,
        "text": "/* X-axis label, e.g., 'Month' */"
        }
        },
        "y": {
        "type": "linear",
        "title": {
        "display": true,
        "text": "/* Y-axis label, e.g., 'Value' */"
        },
        "stacked": false
        }
        },
        "elements": {
        "line": {
        "borderCapStyle": "/* border cap style, e.g., 'butt' */",
        "borderDash": [/* array of dash lengths, e.g., [5, 5] */],
        "borderDashOffset": 0.0,
        "borderJoinStyle": "/* border join style, e.g., 'miter' */",
        "cubicInterpolationMode": "/* interpolation mode, e.g., 'default' */"
        },
        "point": {
        "radius": 3,
        "hitRadius": 10
        }
        }
        }
        }
        IMPORTANT: Only return a single piece of valid JSON text.

        The file given by your client is:
        '''

        final_query = [prompt] + files
    
    elif viz_type.lower() == 'scatter_chart':

        prompt = '''
        Assume yourself to be an expert at creating stunning and appealing data visualizations from given data points.

        He wants you to create a scatter plot using the Chart.js library. He has the library installed and needs your help in filling the parameters.

        Please return a JSON object with the following requirements:''' + custom_query + '''

        - Parameters to fill in the Chart.js library so that it can be used by the client to create visualizations.
        - The chart should display data points where each point is represented as an object containing `x` and `y` properties.
        - The x-axis should be linear by default, and the chart should not have connecting lines between the points.

        The JSON structure should be as follows:

        {
        "type": "scatter",
        "data": {
        "datasets": [
        {
        "label": "/* Dataset label, e.g., 'Scatter Dataset' */",
        "data": [
        /* array of data points as objects, e.g.,
        { "x": -10, "y": 0 },
        { "x": 0, "y": 10 },
        { "x": 10, "y": 5 },
        { "x": 0.5, "y": 5.5 } */
        ],
        "backgroundColor": "/* point background color, e.g., 'rgb(255, 99, 132)' */",
        "borderColor": "/* point border color, e.g., 'rgba(75, 192, 192, 1)' */",
        "borderWidth": 1,
        "hoverBackgroundColor": "/* point hover background color, e.g., 'rgba(255, 159, 64, 1)' */",
        "hoverBorderColor": "/* point hover border color, e.g., 'rgba(255, 159, 64, 1)' */",
        "hoverBorderWidth": 2,
        "pointRadius": 5,
        "pointHoverRadius": 7
        }
        ]
        },
        "options": {
        "responsive": true,
        "plugins": {
        "legend": {
        "display": true,
        "position": "top"
        },
        "title": {
        "display": true,
        "text": "/* Chart title, e.g., 'Scatter Plot Example' */"
        }
        },
        "scales": {
        "x": {
        "type": "linear",
        "position": "bottom",
        "title": {
        "display": true,
        "text": "/* X-axis label, e.g., 'X Axis' */"
        }
        },
        "y": {
        "type": "linear",
        "title": {
        "display": true,
        "text": "/* Y-axis label, e.g., 'Y Axis' */"
        }
        }
        }
        }
        }

        {
        "type": "scatter",
        "data": {
            "datasets": [
            {
                "label": "/* Dataset label, e.g., 'Scatter Dataset' */",
                "data": [
                /* array of data points as objects, e.g.,
                { "x": -10, "y": 0 },
                { "x": 0, "y": 10 },
                { "x": 10, "y": 5 },
                { "x": 0.5, "y": 5.5 } */
                ],
                "backgroundColor": "/* point background color, e.g., 'rgb(255, 99, 132)' */",
                "borderColor": "/* point border color, e.g., 'rgba(75, 192, 192, 1)' */",
                "borderWidth": 1,
                "hoverBackgroundColor": "/* point hover background color, e.g., 'rgba(255, 159, 64, 1)' */",
                "hoverBorderColor": "/* point hover border color, e.g., 'rgba(255, 159, 64, 1)' */",
                "hoverBorderWidth": 2,
                "pointRadius": 5,
                "pointHoverRadius": 7
            }
            ]
        },
        "options": {
            "responsive": true,
            "plugins": {
            "legend": {
                "display": true,
                "position": "top"
            },
            "title": {
                "display": true,
                "text": "/* Chart title, e.g., 'Scatter Plot Example' */"
            }
            },
            "scales": {
            "x": {
                "type": "linear",
                "position": "bottom",
                "title": {
                "display": true,
                "text": "/* X-axis label, e.g., 'X Axis' */"
                }
            },
            "y": {
                "type": "linear",
                "title": {
                "display": true,
                "text": "/* Y-axis label, e.g., 'Y Axis' */"
                }
            }
            }
        }
        }

        IMPORTANT: Only return a single piece of valid JSON text.

        The file given by your client is:
        '''

        final_query = [prompt] + files
    
    elif viz_type.lower() == 'polar_area_chart':

        prompt = ''''''

        final_query = [prompt] + files
    
    elif viz_type.lower() == 'radar_chart':

        prompt = ''''''

        final_query = [prompt] + files
        
    elif viz_type.lower() == 'timeline_chart':

        prompt = ''''''

        final_query = [prompt] + files
    
    elif viz_type.lower() == 'organization_chart':

        prompt = ''''''

        final_query = [prompt] + files

    elif viz_type.lower() == 'table':

        prompt = ''''''

        final_query = [prompt] + files
    
    else:

        prompt = ''''''

        final_query = [prompt] + files
    
    if previous_viz:
        new_prompt = '''
        The previous json data generated by you is attached below. Please modify it accordingly and DO NOT HALUCINATE./n
        ''' + str(previous_viz)

        prompt = prompt + new_prompt

        final_query = [prompt] + files
    
    return final_query


def process_data(query: list[str, object]):
    visualization = model.generate_content(query, generation_config={'response_mime_type': 'application/json'})
    return visualization.text