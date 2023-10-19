import os
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
# from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource.resources.models import Deployment, DeploymentMode
from azure.mgmt.resource.resources.models import DeploymentProperties
from msrestazure.azure_exceptions import CloudError

from flask import Flask, render_template, request, redirect, url_for
import json

app = Flask(__name__)

AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", default=None)
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", default=None)
AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", default=None)
AZURE_SUBSCRIPTION_ID = os.getenv("AZURE_SUBSCRIPTION_ID", default=None)

deployment_name='flasksre'
resource_group='felixRG'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/deploy', methods=['GET', 'POST'])
def deploy():
    if  request.method == 'POST':
        vnet_name = request.form['vnet_name']
        subnet_name = request.form['subnet_name']
        subnet_prefix = request.form['subnet_prefix']
        nsg_name = request.form['nsg_name']
        num_windows_vms = request.form['num_windows_vms']
        num_linux_vms = request.form['num_linux_vms']
        vm_size = request.form['vm_size']
        windows_admin_username = request.form['windows_admin_username']
        windows_admin_password = request.form['windows_admin_password']
        linux_admin_username = request.form['linux_admin_username']
        linux_admin_password = request.form['linux_admin_password']
        ssh_source_ips = request.form['ssh_source_ips']
        rdp_source_ips = request.form['rdp_source_ips']
        authentication_type = request.form['authentication_type']

        parameters = {
            "vnetName": {"value": vnet_name},
            "subnetName": {"value": subnet_name},
            "subnetPrefix": {"value": subnet_prefix},
            "nsgName": {"value": nsg_name},
            "numberOfWindowsVMs": {"value": int(num_windows_vms)},
            "numberOfLinuxVMs": {"value": int(num_linux_vms)},
            "vmSize": {"value": vm_size},
            "windowsAdminUsername": {"value": windows_admin_username},
            "windowsAdminPassword": {"value": windows_admin_password},
            "linuxAdminUsername": {"value": linux_admin_username},
            "linuxAdminPassword": {"value": linux_admin_password},
            "sshSourceIPAddresses": {"value": ssh_source_ips.split(",")},
            "rdpSourceIPAddresses": {"value": rdp_source_ips.split(",")},
            "authenticationType": {"value": authentication_type}
        }

        parameters_path = os.path.join(os.getcwd(), 'app', 'arm_template', 'srelab.vm.parameters.json')
        with open(parameters_path, "w") as file:
            json.dump(parameters, file, indent=4)

        credentials = ClientSecretCredential(
            # client_id=os.environ['AZURE_CLIENT_ID'],
            # client_secret=os.environ['AZURE_CLIENT_SECRET'],
            # tenant_id=os.environ['AZURE_TENANT_ID']
            client_id=AZURE_CLIENT_ID,
            client_secret=AZURE_CLIENT_SECRET,
            tenant_id=AZURE_TENANT_ID
        )

        resource_client = ResourceManagementClient(credentials, AZURE_SUBSCRIPTION_ID)

        # compute_client = ComputeManagementClient(credentials, AZURE_SUBSCRIPTION_ID)

        template_path = os.path.join(os.getcwd(), 'app', 'arm_template', 'srelab.vm.json')
        with open(template_path, 'r') as template_file:
            template_file = json.load(template_file)

        with open(parameters_path, 'r') as parameters_file:
            parameters_file = json.load(parameters_file)

        try:
            deployment_properties = DeploymentProperties(
                mode=DeploymentMode.incremental, 
                template=template_file, 
                parameters=parameters_file
            )
            
            deployment_async_operation = resource_client.deployments.begin_create_or_update(
                resource_group,
                deployment_name,
                Deployment(properties=deployment_properties)
            )
            deployment_async_operation.wait()

            print('Deployment succeeded.')
        except CloudError as ex:
            print(f"Deployment failed with error message: {ex}")


        return redirect(url_for('result', deployment_name=deployment_name))

    return render_template('deploy.html')

@app.route('/result/<deployment_name>')
def result(deployment_name):
    credentials = ClientSecretCredential(
        # client_id=os.environ['AZURE_CLIENT_ID'],
        # client_secret=os.environ['AZURE_CLIENT_SECRET'],
        # tenant_id=os.environ['AZURE_TENANT_ID']
        client_id=AZURE_CLIENT_ID,
        client_secret=AZURE_CLIENT_SECRET,
        tenant_id=AZURE_TENANT_ID
    )

    # resource_client = ResourceManagementClient(credentials, os.environ['AZURE_SUBSCRIPTION_ID'])
    resource_client = ResourceManagementClient(credentials, AZURE_SUBSCRIPTION_ID)

    deployment = resource_client.deployments.get(resource_group, deployment_name)
    status = deployment.properties.provisioning_state
    output = deployment.properties.outputs

    return render_template('result.html', status=status, output=output)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port='8080', debug=True)
