## Créer une clé SSH

ssh-keygen -t rsa -b 2048

## Trouver le Security Group attaché à votre instance

aws ec2 describe-instances --instance-ids i-0b8866944fb1eef0d --query "Reservations[*].Instances[*].SecurityGroups" --output json

## Ajouter une règle pour autoriser SSH

aws ec2 authorize-security-group-ingress \
 --group-id <security-group-id> \
 --protocol tcp \
 --port 22 \
 --cidr 0.0.0.0/0

## connexion SSH

### donner les permision sur le fichier de la clé SSH

chmod 400 <SSH private key file>

### connexion ssh

ssh -i <SSH private key> ubuntu@<DNS IPv4 public>
ex : ssh -i ~/.ssh/aws_key.pem ubuntu@ec2-13-39-47-165.eu-west-3.compute.amazonaws.com
