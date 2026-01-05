# Créez une instance EC2 pour AutoCode
resource "aws_instance" "autocode" {
  ami           = "ami-06e02ae7bdac6b938" # Ubuntu 22.04 LTS for eu-west-3
  instance_type = "t3.medium" # 4 vCPU, 4GB RAM - better for Neo4j + Backend + Frontend
  key_name      = aws_key_pair.autocode.key_name
  vpc_security_group_ids = [aws_security_group.autocode.id]

  # Increase root volume size for Docker images and Neo4j data
  root_block_device {
    volume_size = 30 # GB
    volume_type = "gp3"
    encrypted   = true
    tags = {
      Name        = "AutoCode Root Volume"
      Project     = var.project_name
      Environment = var.environment
    }
  }

  # User data script to install Docker and Docker Compose
  user_data = <<-EOF
              #!/bin/bash
              set -e
              
              # Update system
              apt-get update
              apt-get upgrade -y
              
              # Install Docker
              curl -fsSL https://get.docker.com -o get-docker.sh
              sh get-docker.sh
              
              # Install Docker Compose v2
              apt-get install -y docker-compose-plugin
              
              # Start and enable Docker
              systemctl start docker
              systemctl enable docker
              
              # Add ubuntu user to docker group
              usermod -aG docker ubuntu
              
              # Install additional tools
              apt-get install -y git curl wget nano htop
              
              # Create application directory
              mkdir -p /home/ubuntu/app
              chown ubuntu:ubuntu /home/ubuntu/app
              
              # Create .env file placeholder
              touch /home/ubuntu/app/.env
              chown ubuntu:ubuntu /home/ubuntu/app/.env
              
              # Configure Git safe directory
              git config --global --add safe.directory /home/ubuntu/app
              
              # Increase vm.max_map_count for Neo4j
              sysctl -w vm.max_map_count=262144
              echo "vm.max_map_count=262144" >> /etc/sysctl.conf
              
              # Enable UFW firewall (optional security layer)
              ufw --force enable
              ufw allow 22/tcp
              ufw allow 80/tcp
              ufw allow 443/tcp
              ufw allow 81/tcp
              ufw allow 3000/tcp
              ufw allow 8000/tcp
              ufw allow 7474/tcp
              ufw allow 7687/tcp
              
              # Reboot to apply all changes
              # systemctl reboot
              EOF

  tags = {
    Name        = "AutoCode Application Server"
    Project     = var.project_name
    Environment = var.environment
    Purpose     = "AI-Powered Development Automation"
  }
}

# Allocate and associate Elastic IP for stable public address
resource "aws_eip" "autocode" {
  instance = aws_instance.autocode.id
  domain   = "vpc"

  tags = {
    Name        = "AutoCode Elastic IP"
    Project     = var.project_name
    Environment = var.environment
  }
}

# Outputs
output "instance_id" {
  description = "EC2 Instance ID"
  value       = aws_instance.autocode.id
}

output "public_ip" {
  description = "Elastic IP address"
  value       = aws_eip.autocode.public_ip
}

output "public_dns" {
  description = "Public DNS name"
  value       = aws_instance.autocode.public_dns
}

output "ssh_connection" {
  description = "SSH connection command"
  value       = "ssh -i ${var.private_key_path} ubuntu@${aws_eip.autocode.public_ip}"
}

output "application_urls" {
  description = "Application access URLs"
  value = {
    frontend    = "http://${aws_eip.autocode.public_ip}:3000"
    backend     = "http://${aws_eip.autocode.public_ip}:8000"
    neo4j       = "http://${aws_eip.autocode.public_ip}:7474"
    npm_admin   = "http://${aws_eip.autocode.public_ip}:81"
  }
}
