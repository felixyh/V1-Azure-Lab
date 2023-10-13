import os
import time
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.resource.resources.models import Deployment, DeploymentMode, DeploymentProperties
from msrestazure.azure_exceptions import CloudError
from flask import Flask, render_template, request, redirect, url_for, Response, stream_with_context, flash
from datetime import datetime
import json

app = Flask(__name__)

AZURE_CLIENT_ID = "XXX"
AZURE_CLIENT_SECRET = "XXX"
AZURE_TENANT_ID = "XXX"
AZURE_SUBSCRIPTION_ID = "XXX"

deployment_name = "flasksre"
resource_group = "felixRG"

app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/deploy", methods=["GET", "POST"])
def deploy():

    if request.method == "POST":
        if request.form["action"] == "save":
            vnet_name = request.form["vnet_name"]
            subnet_name = request.form["subnet_name"]
            subnet_prefix = request.form["subnet_prefix"]
            nsg_name = request.form["nsg_name"]
            num_windows_vms = request.form["num_windows_vms"]
            num_linux_vms = request.form["num_linux_vms"]
            vm_size = request.form["vm_size"]
            windows_admin_username = request.form["windows_admin_username"]
            windows_admin_password = request.form["windows_admin_password"]
            linux_admin_username = request.form["linux_admin_username"]
            linux_admin_password = request.form["linux_admin_password"]
            ssh_source_ips = request.form["ssh_source_ips"]
            rdp_source_ips = request.form["rdp_source_ips"]
            authentication_type = request.form["authentication_type"]

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
                "authenticationType": {"value": authentication_type},
            }

            parameters_path = os.path.join(
                os.getcwd(), "app", "arm_template", "srelab.vm.parameters.json"
            )
            with open(parameters_path, "w") as file:
                json.dump(parameters, file, indent=4)
            # flash('Parameters saved successfully!', 'success')

            return redirect(url_for("deploy"))
        
        ####### Start the deployment if deploy button clicked #####
        else:
            parameters_path = os.path.join(
                os.getcwd(), "app", "arm_template", "srelab.vm.parameters.json"
            )

            if not os.path.isfile(parameters_path):
                flash('Please save the parameters before deploying.', 'warning')
                return render_template('deploy.html')

            credentials = ClientSecretCredential(
                client_id=AZURE_CLIENT_ID,
                client_secret=AZURE_CLIENT_SECRET,
                tenant_id=AZURE_TENANT_ID,
            )

            resource_client = ResourceManagementClient(
                credentials, AZURE_SUBSCRIPTION_ID
            )

            template_path = os.path.join(
                os.getcwd(), "app", "arm_template", "srelab.vm.json"
            )
            with open(template_path, "r") as template_file:
                template_file = json.load(template_file)

            parameters_path = os.path.join(
                os.getcwd(), "app", "arm_template", "srelab.vm.parameters.json"
            )

            with open(parameters_path, "r") as parameters_file:
                parameters_file = json.load(parameters_file)
            try:
                deployment_properties = DeploymentProperties(
                    mode=DeploymentMode.incremental,
                    template=template_file,
                    parameters=parameters_file,
                )
                deployment_async_operation = resource_client.deployments.begin_create_or_update(
                    resource_group,
                    deployment_name,
                    Deployment(properties=deployment_properties),
                )
                return redirect(url_for("deploy_status"))
            except CloudError as ex:
                print(f"Deployment failed with error message: {ex}")
                return render_template('deploy.html', Warning=f"Deployment failed with error message: {ex}")


    #### If it is not POST request, will just show the page with GET      
    parameters_path = os.path.join(os.getcwd(), "app", "arm_template", "srelab.vm.parameters.json")

    parameters_mapping = {
        "vnet_name": "vnetName",
        "subnet_name": "subnetName",
        "subnet_prefix": "subnetPrefix",
        "nsg_name": "nsgName",
        "num_windows_vms": "numberOfWindowsVMs",
        "num_linux_vms": "numberOfLinuxVMs",
        "vm_size": "vmSize",
        "windows_admin_username": "windowsAdminUsername",
        "windows_admin_password": "windowsAdminPassword",
        "linux_admin_username": "linuxAdminUsername",
        "linux_admin_password": "linuxAdminPassword",
        "ssh_source_ips": "sshSourceIPAddresses",
        "rdp_source_ips": "rdpSourceIPAddresses",
        "authentication_type": "authenticationType"
    }

    try:
        with open(parameters_path, "r") as parameters_file:
                parameters_dict = json.load(parameters_file)
    except FileNotFoundError:
        parameters_dict = {}
        parameters_mapping = {}

    return render_template("deploy.html", parameters_mapping=parameters_mapping, parameters_dict=parameters_dict, )


@app.route("/deploy_status_stream")
def deploy_status_stream():
    def stream():
        credentials = ClientSecretCredential(
            client_id=AZURE_CLIENT_ID,
            client_secret=AZURE_CLIENT_SECRET,
            tenant_id=AZURE_TENANT_ID,
        )

        resource_client = ResourceManagementClient(
            credentials, AZURE_SUBSCRIPTION_ID
        )

        deployment = resource_client.deployments.get(
            resource_group_name=resource_group, deployment_name=deployment_name
        )

        while True:
            status = deployment.properties.provisioning_state
            yield f"data: {status}\n\n"

            if status == "Succeeded" or status == "Failed" or status == "Canceled":
                break

            time.sleep(5)
            deployment = resource_client.deployments.get(
                resource_group_name=resource_group, deployment_name=deployment_name
            )

    return Response(stream(), mimetype="text/event-stream")



@app.route("/deploy_status")
def deploy_status():
    credentials = ClientSecretCredential(
        client_id=AZURE_CLIENT_ID,
        client_secret=AZURE_CLIENT_SECRET,
        tenant_id=AZURE_TENANT_ID,
    )

    resource_client = ResourceManagementClient(
        credentials, AZURE_SUBSCRIPTION_ID
    )

    deployment = resource_client.deployments.get(
        resource_group_name=resource_group, deployment_name=deployment_name
    )

    status = deployment.properties.provisioning_state

    if status == "Succeeded":
        return redirect(url_for("result"))

    return render_template("deploy_status.html", status=status)


@app.route("/result")
def result():
    credentials = ClientSecretCredential(
        client_id=AZURE_CLIENT_ID,
        client_secret=AZURE_CLIENT_SECRET,
        tenant_id=AZURE_TENANT_ID,
    )

    resource_client = ResourceManagementClient(
        credentials, AZURE_SUBSCRIPTION_ID
    )

    deployment = resource_client.deployments.get(
        resource_group_name=resource_group, deployment_name=deployment_name
    )

    status = deployment.properties.provisioning_state
    output = deployment.properties.outputs

    elapsed_time = deployment.properties.duration

    return render_template("result.html", status=status, output=output, elapsed_time=elapsed_time)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port="8080", debug=True)
