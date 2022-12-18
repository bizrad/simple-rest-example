data "external" "git" {
  program = [
    "git",
    "log",
    "--pretty=format:{ \"sha\": \"%H\" }",
    "-1",
    "HEAD"
  ]
}

resource "docker_image" "api-example-app" {
  name = "api_example_app"

  build {
    path = "./api_example_app"
    tag  = ["api_example_app:${data.external.git.result.sha}"]
  }
}

resource "docker_network" "test" {
  name   = "test"
  driver = "bridge"
}

resource "docker_container" "api-example-app" {
  name  = "api-example-app"
  image = "api_example_app:${data.external.git.result.sha}"

  networks_advanced {
    name = docker_network.test.name
  }

  ports {
    internal = 8080
    external = 8080
  }

}


