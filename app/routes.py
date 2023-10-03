import os
# from azure.common.credentials import ServicePrincipalCredentials
# from azure.mgmt.resource import ResourceManagementClient
# from azure.mgmt.compute import ComputeManagementClient
from flask import Flask, render_template, request, redirect, url_for
from app import app

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/deploy', methods=['GET', 'POST'])
def deploy():
    if request.method == 'POST':
        location = request.form['location']
        resource_group = request.form['resource_group']
        vm_name = request.form['vm_name']
        admin_username = request.form['admin_username']
        admin_password = request.form['admin_password']
        vm_size = request.form['vm_size']

        credentials = ServicePrincipalCredentials(
            client_id=os.environ['AZURE_CLIENT_ID'],
            secret=os.environ['AZURE_CLIENT_SECRET'],
            tenant=os.environ['AZURE_TENANT_ID']
        )

        resource_client = ResourceManagementClient(credentials, os.environ['AZURE_SUBSCRIPTION_ID'])
        compute_client = ComputeManagementClient(credentials, os.environ['AZURE_SUBSCRIPTION_ID'])

        parameters = {
            'location': {
                'value': location
            },
            'vmName': {
                'value': vm_name
            },
            'vmSize': {
                'value': vm_size
            },
            'adminUsername': {
                'value': admin_username
            },
            'adminPassword': {
                'value': admin_password
            }
        }

        template_path = os.path.join(os.getcwd(), 'azure', 'templates', 'deploy.json')
        with open(template_path, 'r') as template_file:
            template = template_file.read()

        deployment_properties = {
            'mode': 'incremental',
            'template': template,
            'parameters': parameters
        }

        deployment_name = f'{vm_name}-deployment'
        resource_client.deployments.create_or_update(resource_group, deployment_name, deployment_properties)

        return redirect(url_for('result', deployment_name=deployment_name))

    return render_template('deploy.html')

@app.route('/result/<deployment_name>')
def result(deployment_name):
    credentials = ServicePrincipalCredentials(
        client_id=os.environ['AZURE_CLIENT_ID'],
        secret=os.environ['AZURE_CLIENT_SECRET'],
        tenant=os.environ['AZURE_TENANT_ID']
    )

    resource_client = ResourceManagementClient(credentials, os.environ['AZURE_SUBSCRIPTION_ID'])

    deployment = resource_client.deployments.get(deployment_name.split('/')[0], deployment_name.split('/')[1])
    status = deployment.properties.provisioning_state
    output = deployment.properties.outputs

    return render_template('result.html', status=status, output=output)

if __name__ == '__main__':
    app.run()
