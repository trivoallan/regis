"""Tests for the URL parser."""

import pytest

from regis_cli.registry.parser import RegistryRef, parse_image_url


class TestParseDockerHubUrls:
    """Test parsing Docker Hub web UI URLs."""

    def test_official_image_with_library(self):
        ref = parse_image_url("https://hub.docker.com/library/nginx")
        assert ref == RegistryRef("registry-1.docker.io", "library/nginx", "latest")

    def test_official_image_with_underscore(self):
        ref = parse_image_url("https://hub.docker.com/_/nginx")
        assert ref == RegistryRef("registry-1.docker.io", "library/nginx", "latest")

    def test_user_image_with_r_prefix(self):
        ref = parse_image_url("https://hub.docker.com/r/nginxinc/nginx-unprivileged")
        assert ref == RegistryRef(
            "registry-1.docker.io", "nginxinc/nginx-unprivileged", "latest"
        )

    def test_user_image_without_r_prefix(self):
        ref = parse_image_url("https://hub.docker.com/nginxinc/nginx-unprivileged")
        assert ref == RegistryRef(
            "registry-1.docker.io", "nginxinc/nginx-unprivileged", "latest"
        )


class TestParseBareReferences:
    """Test parsing bare image references."""

    def test_bare_image_name(self):
        ref = parse_image_url("nginx")
        assert ref == RegistryRef("registry-1.docker.io", "library/nginx", "latest")

    def test_bare_image_with_tag(self):
        ref = parse_image_url("nginx:alpine")
        assert ref == RegistryRef("registry-1.docker.io", "library/nginx", "alpine")

    def test_bare_user_image(self):
        ref = parse_image_url("nginxinc/nginx-unprivileged:latest")
        assert ref == RegistryRef(
            "registry-1.docker.io", "nginxinc/nginx-unprivileged", "latest"
        )

    def test_private_registry(self):
        ref = parse_image_url("myregistry.example.com/org/image:v1.0")
        assert ref == RegistryRef("myregistry.example.com", "org/image", "v1.0")


class TestRegistryRef:
    """Test RegistryRef properties."""

    def test_image_name(self):
        ref = RegistryRef("registry-1.docker.io", "library/nginx", "latest")
        assert ref.image_name == "nginx"

    def test_image_name_with_org(self):
        ref = RegistryRef(
            "registry-1.docker.io", "nginxinc/nginx-unprivileged", "latest"
        )
        assert ref.image_name == "nginx-unprivileged"


class TestInvalidUrls:
    """Test that invalid URLs raise ValueError."""

    def test_empty_path_url(self):
        with pytest.raises(ValueError):
            parse_image_url("https://myregistry.example.com/")
