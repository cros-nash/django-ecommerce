# Define the AWS provider and region
provider "aws" {
  region = "us-east-1" # Or your desired region
}

# Create a key pair for SSH access (if you don't have one managed by Terraform)
data "aws_key_pair" "git" {
  key_name = "git"
}

# Create a security group to allow SSH and HTTP access
resource "aws_security_group" "django_sg" {
  name        = "django-app-security-group"
  description = "Allow SSH and HTTP traffic"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # IMPORTANT: Restrict SSH to your IP for security
    description = "Allow SSH from your IP"
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # Allow HTTP from anywhere
    description = "Allow HTTP from anywhere"
  }

  # If you need HTTPS, add this:
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTPS from anywhere"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow all outbound traffic"
  }

  tags = {
    Name = "django-app-sg"
  }
}

# Create the EC2 instance
resource "aws_instance" "django_app_instance" {
  ami           = "ami-0731becbf832f281e"
  instance_type = "t2.micro" # Free tier eligible
  key_name      = data.aws_key_pair.git.key_name
  vpc_security_group_ids = [aws_security_group.django_sg.id]

  tags = {
    Name = "EcommerceDjangoWebApp"
  }
}

# Output the public IP of the instance
output "instance_public_ip" {
  description = "The public IP address of the Django app instance."
  value       = aws_instance.django_app_instance.public_ip
}