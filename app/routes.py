from flask import Flask, render_template, request
import subprocess
import json

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/deploy', methods=['POST'])
def deploy():
    num_vms = request.form['num_vms']
    params = {
        'location': 'eastus',
        'rgName': 'myResourceGroup',
        'vnetName': 'myVnet',
        'subnetName': 'mySubnet',
        'nsgName': 'myNsg',
        'ruleName': 'myNsgRule',
        'ipAddresses': [
            '4.71.171.82',
            '99.155.67.149'
        ],
        'ports': '22,80',
        'vmName': 'myVm',
        'vmSize': 'Standard_B1s',
        'adminUsername': 'myUsername',
        'adminPassword': 'myPassword'
    }
    params['vmName'] += '-'
    for i in range(int(num_vms)):
        params['vmName'] += str(i)
        cmd = ['az', 'deployment', 'group', 'create', '-n', params['vmName'], '-g', params['rgName'], '--template-file', 'arm_files/v1lab_deployment.json', '--parameters', json.dumps(params)]
        subprocess.run(cmd)
        params['vmName'] = params['vmName'][:-1]
        params['vmName'] += str(i+1)
    return render_template('success.html', num_vms=num_vms)

@app.route('/delete', methods=['POST'])
def delete():
    cmd = ['az', 'group', 'delete', '-n', 'myResourceGroup', '-y']
    subprocess.run(cmd)
    return render_template('deleted.html')

if __name__ == '__main__':
    app.run(debug=True)
