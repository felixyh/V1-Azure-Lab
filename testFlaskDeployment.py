import os
from azure.identity import ClientSecretCredential
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.compute import ComputeManagementClient

from azure.mgmt.resource.resources.models import Deployment, DeploymentMode
from azure.mgmt.resource.resources.models import DeploymentProperties

from msrestazure.azure_exceptions import CloudError

import json

AZURE_CLIENT_ID="966322c5-cb76-4bd2-bb1a-4d69cfe8d9b5"
AZURE_CLIENT_SECRET="-L98Q~TKOxRyxRRdI9sHBBlJxY_ZeGMCcSEn9cQO"
AZURE_TENANT_ID="3e04753a-ae5b-42d4-a86d-d6f05460f9e4"
AZURE_SUBSCRIPTION_ID="6b892183-b95d-42e5-b659-fa2bef8f11f7"

deployment_name='flasksre'
resource_group='felixRG'

def deploy():

    parameters_path = os.path.join(os.getcwd(), 'app', 'arm_template', 'srelab.vm.parameters.json')

    credentials = ClientSecretCredential(
        client_id=AZURE_CLIENT_ID,
        client_secret=AZURE_CLIENT_SECRET,
        tenant_id=AZURE_TENANT_ID
    )

    resource_client = ResourceManagementClient(credentials, AZURE_SUBSCRIPTION_ID)
    compute_client = ComputeManagementClient(credentials, AZURE_SUBSCRIPTION_ID)


    template_path = os.path.join(os.getcwd(), 'app', 'arm_template', 'srelab.vm.json')
    with open(template_path, 'r') as template_file:
        # template_file = template_file.read()
        template_file = json.load(template_file)

    with open(parameters_path, 'r') as parameters_file:
        # parameters_file = parameters_file.read()
        parameters_file = json.load(parameters_file)

    # deployment_properties = {
    #     'mode': 'incremental',
    #     'template': template_file,
    #     'parameters': parameters_file
    # }

    try:
        # deployment_async_operation = resource_client.deployments.begin_create_or_update(
        #     resource_group_name=resource_group,
        #     deployment_name=deployment_name,
        #     parameters=deployment_properties
        # )
###
        deployment_properties = DeploymentProperties(mode=DeploymentMode.incremental, template=template_file, parameters=parameters_file)
        deployment_async_operation = resource_client.deployments.begin_create_or_update(
            resource_group,
            deployment_name,
            Deployment(properties=deployment_properties)
        )
        deployment_async_operation.wait()
####
        # deployment_async_operation.wait()
        print('Deployment succeeded.')
    except CloudError as ex:
        print(f"Deployment failed with error message: {ex}")

if __name__ == '__main__':
    deploy()