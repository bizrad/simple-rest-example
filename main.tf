data "external" "git" {
  // This feels a bit backwards, but there's no CI/CD here
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
    tag  = ["api-example-app:${data.external.git.result.sha}"]
  }
}

resource "docker_network" "test" {
  name   = "test"
  driver = "bridge"
}

resource "docker_container" "api-example-app" {
  depends_on = [docker_network.test, docker_image.api-example-app]
  name       = "api-example-app"
  image      = "api-example-app:${data.external.git.result.sha}"

  networks_advanced {
    name = docker_network.test.name
  }

  ports {
    internal = 8080
    external = 8080
  }

}

output "api-example-app-docker-image" {
  value = "${docker_image.api-example-app.name}:${data.external.git.result.sha}@${docker_image.api-example-app.image_id}"
}
