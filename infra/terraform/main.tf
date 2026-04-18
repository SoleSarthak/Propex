terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# VPC Module (Simplifying with a standard VPC for brevity)
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "5.0.0"

  name = "propex-staging-vpc"
  cidr = "10.0.0.0/16"

  azs             = ["${var.aws_region}a", "${var.aws_region}b", "${var.aws_region}c"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24", "10.0.3.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24", "10.0.103.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true

  tags = {
    Environment = "staging"
    Project     = "PropEx"
  }
}

# EKS Cluster
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "19.15.0"

  cluster_name    = "propex-staging-cluster"
  cluster_version = "1.30"

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  eks_managed_node_groups = {
    staging = {
      min_size     = 1
      max_size     = 3
      desired_size = 3

      instance_types = ["t3.medium"]
      capacity_type  = "ON_DEMAND"
    }
  }

  tags = {
    Environment = "staging"
    Project     = "PropEx"
  }
}

# RDS PostgreSQL
resource "aws_db_instance" "postgres" {
  identifier           = "propex-staging-db"
  allocated_storage    = 20
  storage_type         = "gp2"
  engine               = "postgres"
  engine_version       = "16.1"
  instance_class       = "db.t3.micro"
  db_name              = "propex"
  username             = "propex_admin"
  password             = var.db_password
  parameter_group_name = "default.postgres16"
  skip_final_snapshot  = true
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  db_subnet_group_name   = module.vpc.database_subnet_group_name

  tags = {
    Environment = "staging"
    Project     = "PropEx"
  }
}

# Security Group for RDS
resource "aws_security_group" "db_sg" {
  name        = "propex-db-sg"
  description = "Allow inbound traffic to Postgres"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ElastiCache Redis
resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "propex-staging-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  port                 = 6379
  subnet_group_name    = aws_elasticache_subnet_group.redis_subnet_group.name
  security_group_ids   = [aws_security_group.redis_sg.id]

  tags = {
    Environment = "staging"
    Project     = "PropEx"
  }
}

resource "aws_elasticache_subnet_group" "redis_subnet_group" {
  name       = "propex-redis-subnet-group"
  subnet_ids = module.vpc.private_subnets
}

resource "aws_security_group" "redis_sg" {
  name        = "propex-redis-sg"
  description = "Allow inbound traffic to Redis"
  vpc_id      = module.vpc.vpc_id

  ingress {
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [module.vpc.vpc_cidr_block]
  }
}

# S3 Bucket
resource "aws_s3_bucket" "propex_storage" {
  bucket = "propex-staging-storage-2026"

  tags = {
    Environment = "staging"
    Project     = "PropEx"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "propex_storage_lifecycle" {
  bucket = aws_s3_bucket.propex_storage.id

  rule {
    id      = "archive-old-data"
    status  = "Enabled"

    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }

    transition {
      days          = 90
      storage_class = "GLACIER"
    }

    expiration {
      days = 365
    }
  }
}

# Secrets Manager
resource "aws_secretsmanager_secret" "propex_secrets" {
  name = "propex/staging/secrets"
}

resource "aws_secretsmanager_secret_version" "propex_secrets_placeholder" {
  secret_id     = aws_secretsmanager_secret.propex_secrets.id
  secret_string = jsonencode({
    DB_PASSWORD = "placeholder-change-me"
    GH_TOKEN    = "placeholder-change-me"
  })
}
