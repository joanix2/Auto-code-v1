# On CloudShell

## créer un utilisateur

aws iam create-user --user-name joanix

## lister les utilisateurs

aws iam list-users

## créer une pair de clé

aws iam create-access-key --user-name joanix

# On local Shell

## install aws Linux

curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

## Vérifier l’installation

aws --version

## configuration de la CLI

aws configure
AWS Access Key ID [None]: **\*\***\*\***\*\***
AWS Secret Access Key [None]: \***\*\*\*\*\*\*\***\*\*\*\*\***\*\*\*\*\*\*\***
Default region name [None]: eu-west-3
Default output format [None]: json

## Verify login

aws sts get-caller-identity

## Find a valid AMI ID for your region

aws ec2 describe-images

## Voir les Instances (en cours d'exécution)

https://eu-west-3.console.aws.amazon.com/ec2/home?region=eu-west-3#Instances:instanceState=running
