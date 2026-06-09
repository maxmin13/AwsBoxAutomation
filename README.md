# AWS datacenter project

The project creates a datacenter in AWS.</br>
The datacenter consists of a VPC, a subnet, one security group, one Linux 2 instance with a DNS record associated.</br>
The VPC and all the other AWS artifacts are created with Python AWS SDK boto3.</br>
Updating OpenSSL to version 1.1.1u and Python to version 3.11.4, the installation of PostgreSQL server
and Nginx are done with Ansible.</br>

## Local work machine requirements: ##

- Fedora 38
- Python 3.12

## Configure the AWS credentials and default region in your work machine: ##

Log into AWS management console as root, go to IAM, Users, create a new user.</br>
Select the user and create the access keys.</br>
Associate the user with an identity-based policy that allows access to route53 webservices, for ex: AmazonRoute53FullAccess.</br>
Associate the user with an identity-based policy that allows access to ec2 webservices, for ex: AmazonEC2FullAccess.</br>
The access key, the secret access key, the AWS region associated with the user have to be exported before running the scripts.

## Clone the project: ##

git clone git@github.com:maxmin13/datacenter-prj.git

## Configure the project: ##

edit **config/datacenter.json** and **config/hostedzone.json** and set the Vpc and DNS values according to your AWS account: <br>

* VPC CIDR (eg: "Cidr": "10.0.0.0/16")<br>
* VPC region (eg: "Region": "eu-west-1")<br>
* Availability zone (eg: "Az": "eu-west-1a")<br>
* Subnet CIDR (eg: "Cidr": "10.0.20.0/24")<br>
* Instance private IP (eg: "PrivateIp": "10.0.20.35")<br>
* (Not mandatory) DNS registered domain (your domain registered with the AWS registrar, eg: "RegisteredDomain": "maxmin.it")<br>

## Create the AWS datacenter (VPC, security group, instance ...) and a DNS record associated to the instance: ##

```
export AWS_ACCESS_KEY_ID=<AWS IAM user credentials>
export AWS_SECRET_ACCESS_KEY=<AWS IAM user credentials>
export AWS_DEFAULT_REGION=<AWS IAM user credentials>

cd bin
sudo chmod -R -x make.sh 
./make.sh

```

## Upgrade Openssl to 1.1.1 version, install Python 3.11, PostgreSQL server, Nginx: ##

```
export AWS_ACCESS_KEY_ID=<AWS IAM user credentials>
export AWS_SECRET_ACCESS_KEY=<AWS IAM user credentials>
export AWS_DEFAULT_REGION=<AWS IAM user credentials>

cd bin
sudo chmod -R -x provision.sh 
./provision.sh

```

## Delete the datacenter: ##

```
export AWS_ACCESS_KEY_ID=<AWS IAM user credentials>
export AWS_SECRET_ACCESS_KEY=<AWS IAM user credentials>
export AWS_DEFAULT_REGION=<AWS IAM user credentials>

cd bin
sudo chmod -R -x delete.sh 
./delete.sh
```

## Log into the remote AWS instance: ##

```
// ssh into the remote instance, specifing the instance private key and the instance user:
cd datacenter-prj/access

rm -f ~/.ssh/known_hosts && ssh -v -i admin-box -p 22 dtcadmin@dtc.maxmin.it
```

## Access the Nginx page: ##

*http://dtc.maxmin.it:8080/index.html*
<br>
*https://dtc.maxmin.it:8443/index.html*
<br>

## Connect to the PostgreSql server: ##

```
// ssh into the remote instance, specifing the instance private key and the instance user:
cd datacenter-prj/access
rm -f ~/.ssh/known_hosts && ssh -v -i admin-box -p 22 dtcadmin@dtc.maxmin.it

// log into the PostgreSQL server
sudo su postgres
cd ~postgres
psql -U postgres

// check all currently active users:
\du

// list all databases
\l

// exit 	
\q

```
<br>

## Testing ##

This project uses pytest for unit testing and simple integration checks.

- Install test dependencies:

```bash
pip install -r requirements.txt
pip install pytest
```

- Basic `pytest` configuration can be added in a `pytest.ini` file with:

```ini
[pytest]
minversion = 6.0
testpaths = tests
```

- Place tests under the `tests/` tree mirroring the package layout (for example, `tests/src/comtest/...`).

- Run the test suite:

```bash
pytest -q
```

If you want, I can add `pytest` to `requirements.txt`, create `pytest.ini`, and add an example test to `tests/`.
