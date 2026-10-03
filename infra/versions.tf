terraform {
  required_version = ">= 1.6"

  required_providers {
    aws     = { source = "hashicorp/aws", version = "~> 6.0" }
    archive = { source = "hashicorp/archive", version = "~> 2.4" }
  }
}

provider "aws" {
  region = "ap-southeast-2"

  default_tags {
    tags = {
      project    = "sre-lambda-lab"
      managed_by = "terraform"
    }
  }
}
