################################################################################
# S3 Backend Stub
#
# Uncomment and configure the block below to enable remote state storage.
# You must first create the S3 bucket and DynamoDB table, then run:
#   terraform init -reconfigure
################################################################################

# terraform {
#   backend "s3" {
#     bucket         = "subscription-offer-app-tfstate"
#     key            = "infra/terraform.tfstate"
#     region         = "us-east-1"
#     encrypt        = true
#     dynamodb_table = "subscription-offer-app-tflock"
#   }
# }
