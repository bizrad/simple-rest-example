terraform {
  required_version = "~> 1.0"

  required_providers {
    docker = {
      source  = "kreuzwerker/docker"
      version = "2.23.1"
    }
  }
}

provider "docker" {
  //  host = "unix:///var/run/docker.sock"
}