#!/bin/bash

REGION="eu-west-3"

echo "🔎 Liste des instances EC2 dans la région $REGION..."
echo
aws ec2 describe-instances \
  --region $REGION \
  --query "Reservations[*].Instances[*].[InstanceId,State.Name,Tags[?Key=='Name']|[0].Value]" \
  --output table

echo
read -p "👉 Entrez l'ID de l'instance à supprimer (ou tapez 'q' pour quitter) : " INSTANCE_ID

if [[ "$INSTANCE_ID" == "q" || "$INSTANCE_ID" == "Q" ]]; then
  echo "❌ Opération annulée."
  exit 0
fi

echo
read -p "⚠️ Voulez-vous vraiment supprimer l'instance $INSTANCE_ID ? (yes/no) : " CONFIRM

if [[ "$CONFIRM" != "yes" ]]; then
  echo "❌ Suppression annulée."
  exit 0
fi

echo "🛑 Suppression en cours de l'instance $INSTANCE_ID..."
aws ec2 terminate-instances --instance-ids "$INSTANCE_ID" --region $REGION

echo "⏳ Vérification de l'état..."
aws ec2 describe-instances \
  --instance-ids "$INSTANCE_ID" \
  --region $REGION \
  --query "Reservations[*].Instances[*].[InstanceId,State.Name]" \
  --output table

echo "✅ Terminé."
