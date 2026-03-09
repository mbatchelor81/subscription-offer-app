# ------------------------------------------------------------
# S3 Remote State Backend (stub)
# ------------------------------------------------------------
# Uncomment and configure once an S3 bucket + DynamoDB table
# have been provisioned for state locking.
#
# terraform {
#   backend "s3" {
#     bucket         = "subscription-offer-app-tfstate"
#     key            = "infra/terraform.tfstate"
#     region         = "us-east-1"
#     encrypt        = true
#     dynamodb_table = "subscription-offer-app-tflock"
#   }
# }
