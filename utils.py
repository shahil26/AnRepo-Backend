def convert_one_login_creds(cred):
    return {
        "id": str(cred['_id']),
        "institute_id": cred['institute_id'],
        "email_id": cred['email_id'],
        "password": cred['password'],
        "roles": cred['roles']
    }

def convert_many_login_creds(creds):
    return [convert_one_login_creds(cred) for cred in creds]

def convert_one_list_file(file):
    return {
        "file_id": file['file_id'],
        "file_name": file['file_name'],
        "file_type": file['file_type'],
        "content_type": file['content_type'],
        "date_uploaded": file['date_uploaded'],
        "description": file['description'],
        "uploader": file['uploader'],
        "is_deleted": file['is_deleted'],
    }

def convert_many_list_files(files):
    return [convert_one_list_file(file) for file in files]

def convert_one_visualization(visualization):
    return {
        "visualization_id": str(visualization['_id']),
        "uploader": visualization['uploader'],
        "roles": visualization['roles'],
        "title": visualization['title'],
        "description": visualization['description'],
        "visualization_json": visualization['visualization_json'],
        "html_template": visualization['html_template'],
        "viz_type": visualization['viz_type'],
        "roles_access": visualization['roles_access'],
        "viz_format": visualization['viz_format'],
        "date_uploaded": visualization['date_uploaded'],
        "is_deleted": visualization['is_deleted'],
    }

def convert_many_visualizations(visualizations):
    return [convert_one_visualization(visualization) for visualization in visualizations]

def convert_visualizations_to_html(visualization_json):
    html_template = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Visualization</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    </head>
    <body>
        <canvas></canvas>
        <script>
            const chardata = JSON.parse(''' + visualization_json + ''');
            const ctx = document.querySelector("canvas");
            const myChart = new Chart(ctx, chardata);
        </script>
    </body>
    </html>
    '''
    return html_template


# setTimeout(() => {
#                 fetch('/save_image', {
#                     method: 'POST',
#                     headers: { 'Content-Type': 'application/json' },
#                     body: JSON.stringify({ imageDataURL })
#                 });
#             }, 5000);