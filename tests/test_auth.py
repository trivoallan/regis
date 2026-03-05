import os
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from regis_cli.cli import main
from regis_cli.registry.client import RegistryClient


class TestRegistryAuth:
    """Test registry authentication logic."""

    @patch("regis_cli.registry.auth.Path.home")
    def test_resolve_credentials_aliases(self, mock_home):
        """Test resolve_credentials handles Docker Hub aliases."""
        from regis_cli.registry.auth import resolve_credentials

        # Test CLI override with alias
        user, pwd = resolve_credentials(
            "registry-1.docker.io", cli_auths=["docker.io=alias_user:alias_pass"]
        )
        assert user == "alias_user"
        assert pwd == "alias_pass"

        # Test Env Var with alias
        env = {
            "REGIS_AUTH_DOCKER_IO_USERNAME": "env_alias_user",
            "REGIS_AUTH_DOCKER_IO_PASSWORD": "env_alias_pass",
        }
        with patch.dict(os.environ, env, clear=True):
            user, pwd = resolve_credentials("registry-1.docker.io")
            assert user == "env_alias_user"
            assert pwd == "env_alias_pass"

    def test_client_init_with_credentials(self):
        """Test RegistryClient initialization with credentials."""
        client = RegistryClient(
            "registry.example.com",
            "library/nginx",
            username="user",
            password="password",
        )
        assert client.username == "user"
        assert client.password == "password"

    @patch("regis_cli.registry.client.requests.Session")
    def test_client_authentication_token_request(self, mock_session_cls):
        """Test that credentials are sent during token authentication."""
        mock_session = mock_session_cls.return_value

        # Mock 401 response for the initial request
        resp_401 = MagicMock()
        resp_401.status_code = 401

        # The WWW-Authenticate header that triggers auth
        resp_401.headers = {
            "WWW-Authenticate": 'Bearer realm="https://auth.docker.io/token",service="registry.docker.io",scope="repository:library/nginx:pull"'
        }

        # Mock 200 response for the token request
        token_resp = MagicMock()
        token_resp.status_code = 200
        token_resp.json.return_value = {"token": "fake-token"}

        # Mock 200 response for the retried request
        resp_200 = MagicMock()
        resp_200.status_code = 200
        resp_200.json.return_value = {}

        # Configure side_effects for session.get
        # 1. Initial request -> 401
        # 2. Token request -> 200
        # 3. Retried request -> 200
        mock_session.request.side_effect = [resp_401, resp_200]
        mock_session.get.return_value = token_resp

        client = RegistryClient(
            "registry.example.com",
            "library/nginx",
            username="myuser",
            password="mypassword",
        )

        # Trigger a request that requires auth
        client.list_tags()

        # Verify calls
        assert mock_session.request.call_count == 2
        assert mock_session.get.call_count == 1

        # Check the token request (only 1 call to get)
        token_call = mock_session.get.call_args_list[0]
        args, kwargs = token_call

        assert args[0] == "https://auth.docker.io/token"
        assert kwargs["auth"] == ("myuser", "mypassword")

    @patch("regis_cli.cli.jsonschema.validate")
    @patch("regis_cli.cli._discover_analyzers")
    @patch("regis_cli.cli.RegistryClient")
    def test_cli_passes_credentials(
        self, mock_client_cls, mock_discover, mock_validate
    ):
        """Test that CLI passes credentials from env vars."""
        runner = CliRunner()

        # Mock an analyzer setup
        mock_analyzer_cls = MagicMock()
        mock_analyzer_instance = mock_analyzer_cls.return_value
        mock_analyzer_instance.analyze.return_value = {"some": "data"}
        mock_discover.return_value = {"test_analyzer": mock_analyzer_cls}
        mock_client_cls.return_value.get_digest.return_value = None

        env = {
            "REGIS_USERNAME": "env_user",
            "REGIS_PASSWORD": "env_password",
        }

        with patch.dict(os.environ, env):
            result = runner.invoke(main, ["analyze", "nginx", "-a", "test_analyzer"])

        assert result.exit_code == 0

        # Verify RegistryClient was initialized with env credentials
        mock_client_cls.assert_called_once()
        _, kwargs = mock_client_cls.call_args

        assert kwargs["username"] == "env_user"
        assert kwargs["password"] == "env_password"

    @patch("regis_cli.registry.auth.Path.home")
    def test_resolve_credentials_precedence(self, mock_home):
        """Test resolve_credentials precedence: CLI > Domain Env > Global Env > config.json."""
        from regis_cli.registry.auth import resolve_credentials

        # 1. Test CLI overrides
        user, pwd = resolve_credentials(
            "registry.example.com", cli_auths=["registry.example.com=cli_user:cli_pass"]
        )
        assert user == "cli_user"
        assert pwd == "cli_pass"

        # 2. Test Domain-specific Env Vars
        env = {
            "REGIS_AUTH_REGISTRY_EXAMPLE_COM_USERNAME": "domain_user",
            "REGIS_AUTH_REGISTRY_EXAMPLE_COM_PASSWORD": "domain_pass",
            "REGIS_USERNAME": "global_user",
            "REGIS_PASSWORD": "global_pass",
        }
        with patch.dict(os.environ, env, clear=True):
            user, pwd = resolve_credentials("registry.example.com")
            assert user == "domain_user"
            assert pwd == "domain_pass"

        # 3. Test Global Env Vars
        env = {
            "REGIS_USERNAME": "global_user",
            "REGIS_PASSWORD": "global_pass",
        }
        with patch.dict(os.environ, env, clear=True):
            user, pwd = resolve_credentials("registry.example.com")
            assert user == "global_user"
            assert pwd == "global_pass"

        # 4. Test Docker config.json
        mock_path = MagicMock()
        mock_home.return_value = mock_path
        docker_path = MagicMock()
        (mock_path / ".docker" / "config.json").return_value = docker_path
        docker_path.exists.return_value = True

        mock_config = {
            "auths": {
                "registry.example.com": {
                    "auth": "ZG9ja2VyX3VzZXI6ZG9ja2VyX3Bhc3M="  # docker_user:docker_pass
                }
            }
        }
        with patch.dict(os.environ, {}, clear=True):
            with patch(
                "regis_cli.registry.auth.open", new_callable=MagicMock
            ) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = ""
                with patch("json.load", return_value=mock_config):
                    user, pwd = resolve_credentials("registry.example.com")
                    assert user == "docker_user"
                    assert pwd == "docker_pass"

    @patch("regis_cli.cli.jsonschema.validate")
    @patch("regis_cli.cli._discover_analyzers")
    @patch("regis_cli.cli.RegistryClient")
    def test_cli_passes_cli_auth_override(
        self, mock_client_cls, mock_discover, mock_validate
    ):
        """Test that CLI passes --auth overrides."""
        runner = CliRunner()

        # Mock an analyzer setup
        mock_analyzer_cls = MagicMock()
        mock_analyzer_instance = mock_analyzer_cls.return_value
        mock_analyzer_instance.analyze.return_value = {"some": "data"}
        mock_discover.return_value = {"test_analyzer": mock_analyzer_cls}
        mock_client_cls.return_value.get_digest.return_value = None

        result = runner.invoke(
            main,
            [
                "analyze",
                "registry.example.com/library/nginx",
                "-a",
                "test_analyzer",
                "--auth",
                "registry.example.com=override_user:override_pass",
            ],
        )

        assert result.exit_code == 0

        # Verify RegistryClient was initialized with override credentials
        mock_client_cls.assert_called_once()
        _, kwargs = mock_client_cls.call_args

        assert kwargs["username"] == "override_user"
        assert kwargs["password"] == "override_pass"
