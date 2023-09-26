from __future__ import absolute_import, division, print_function, annotations

import json

import filelock
import pytest
import yaml
from _pytest.monkeypatch import MonkeyPatch

from ansible_collections.famedly.base.plugins.modules import gpg_secretstore
from ansible_collections.famedly.base.tests.unit.mock_filelock import MockFileLock
from ansible_collections.famedly.base.tests.unit.mock_secretstore import MockSecretStore
from ansible_collections.famedly.base.tests.unit.utils import (
    AnsibleExitJson,
    set_module_args,
    exit_json,
    fail_json,
)


def mock_commit_changes(repo_path: str, file_path: str, remove: bool = False):
    pass


class TestGPGSecretstore:
    @staticmethod
    def patchSecretstore(monkeypatch: MonkeyPatch, mock: type(MockSecretStore)):
        # Mock ansible functions
        monkeypatch.setattr(gpg_secretstore.AnsibleModule, "exit_json", exit_json)
        monkeypatch.setattr(gpg_secretstore.AnsibleModule, "fail_json", fail_json)
        # Mock secretstore functions
        monkeypatch.setattr(gpg_secretstore.SecretStore, "get", mock.get)
        monkeypatch.setattr(gpg_secretstore.SecretStore, "put", mock.put)
        monkeypatch.setattr(gpg_secretstore.SecretStore, "remove", mock.remove)
        monkeypatch.setattr(
            gpg_secretstore.SecretStore,
            "get_recipients_from_encrypted_file",
            mock.get_recipients_from_encrypted_file,
        )
        monkeypatch.setattr(
            gpg_secretstore.SecretStore, "get_recipients", mock.get_recipients
        )
        monkeypatch.setattr(gpg_secretstore.SecretStore, "__init__", mock.__init__)
        # Mock git function
        monkeypatch.setattr(gpg_secretstore, "_commit_changes", mock_commit_changes)
        # Mock filelock functions
        monkeypatch.setattr(filelock, "UnixFileLock", MockFileLock)
        monkeypatch.setattr(filelock, "WindowsFileLock", MockFileLock)
        monkeypatch.setattr(filelock, "SoftFileLock", MockFileLock)

    def test_secret_present_no_changes(self, monkeypatch):
        self.patchSecretstore(monkeypatch, MockSecretStore)
        set_module_args(
            {
                "password_slug": "secret/exists",
                "password_store_path": "/home/jadyn/famedly/git/environments/local/secret_storage/",
                "state": "present",
            }
        )
        with pytest.raises(AnsibleExitJson) as result:
            gpg_secretstore.main()
        ansible_result = result.value.result

        assert ansible_result["changed"] is False
        assert ansible_result["password_slug"] == "secret/exists"
        assert ansible_result["secret"] == "secretdata"
        assert (
            ansible_result["diff"]["before"] == "recipient1\nrecipient2\nrecipient3\n"
        )
        assert ansible_result["diff"]["after"] == "recipient1\nrecipient2\nrecipient3\n"

    def test_secret_not_present(self, monkeypatch):
        self.patchSecretstore(monkeypatch, MockSecretStore)
        set_module_args(
            {
                "password_slug": "secret/not-present",
                "password_store_path": "/home/jadyn/famedly/git/environments/local/secret_storage/",
                "state": "present",
            }
        )
        with pytest.raises(AnsibleExitJson) as result:
            gpg_secretstore.main()
        ansible_result = result.value.result

        assert ansible_result["changed"] is True
        assert ansible_result["password_slug"] == "secret/not-present"
        assert ansible_result["diff"]["before"] == "\n"
        assert ansible_result["diff"]["after"] == "recipient1\nrecipient2\nrecipient3\n"

    def test_secret_recipient_missmatch(self, monkeypatch):
        self.patchSecretstore(monkeypatch, MockSecretStore)
        set_module_args(
            {
                "password_slug": "secret/recipient-missmatch",
                "password_store_path": "/home/jadyn/famedly/git/environments/local/secret_storage/",
                "state": "present",
            }
        )
        with pytest.raises(AnsibleExitJson) as result:
            gpg_secretstore.main()
        ansible_result = result.value.result

        assert ansible_result["changed"] is True
        assert ansible_result["secret"] == "secretdata"
        assert ansible_result["password_slug"] == "secret/recipient-missmatch"
        assert ansible_result["diff"]["before"] == "recipient1\nrecipient3\n"
        assert ansible_result["diff"]["after"] == "recipient1\nrecipient2\nrecipient3\n"

    def test_secret_deletion(self, monkeypatch):
        self.patchSecretstore(monkeypatch, MockSecretStore)
        set_module_args(
            {
                "password_slug": "secret/delete",
                "password_store_path": "/home/jadyn/famedly/git/environments/local/secret_storage/",
                "state": "absent",
            }
        )
        with pytest.raises(AnsibleExitJson) as result:
            gpg_secretstore.main()
        ansible_result = result.value.result

        assert ansible_result["changed"] is True
        assert ansible_result["password_slug"] == "secret/delete"
        assert (
            ansible_result["diff"]["before"] == "recipient1\nrecipient2\nrecipient3\n"
        )
        assert ansible_result["diff"]["after"] == "\n"


class TestSecretGenerator:
    def test_plain_random_secret(self, monkeypatch):
        generator = gpg_secretstore.SecretGenerator(
            secret_type="random", length=30, letter_pattern="([A-Za-z0-9])"
        )
        secret = generator.getSecret()
        assert len(secret) == 30

    def test_plain_user_supplied_secret(self, monkeypatch):
        generator = gpg_secretstore.SecretGenerator(
            secret_type="user_supplied", user_supplied_secret="secretdata"
        )
        secret = generator.getSecret()
        assert secret == "secretdata"

    def test_plain_binary_secret(self, monkeypatch):
        generator = gpg_secretstore.SecretGenerator(
            secret_type="binary", binary="echo -n secret"
        )
        secret = generator.getSecret()
        assert secret == "secret"

    def test_json_user_supplied_secret(self, monkeypatch):
        data = """
        {
            "glossary": {
                "title": "example glossary",
                "GlossDiv": {
                    "title": "S",
                    "GlossList": {
                        "GlossEntry": {
                            "ID": "SGML",
                            "SortAs": "SGML",
                            "GlossTerm": "Standard Generalized Markup Language",
                            "Acronym": "SGML",
                            "Abbrev": "ISO 8879:1986",
                            "GlossDef": {
                                "para": "A meta-markup language, used to create markup languages such as DocBook.",
                                "GlossSeeAlso": ["GML", "XML"]
                            },
                            "GlossSee": "markup"
                        }
                    }
                }
            }
        }
        """
        generator = gpg_secretstore.SecretGenerator(
            secret_type="user_supplied", data_type="json", user_supplied_secret=data
        )
        assert generator.getSecretData() == json.loads(data)

    def test_yaml_user_supplied_secret(self, monkeypatch):
        data = """
        key: value
        integerValue: 1
        floatingValue: 1
        stringValue: "456"
        stringValue: 'abc'
        stringValue: wer
        booleanValue: true
        string1: |
           Line1
           line2
           "line3"
           line4
        string1: >
           Line1
           line2
           "line3"
           line4
        sequence1:
           - One
           - two
           - Three
        sequence2: [one, two , three]
        mysqldatabase:
          hostname: localhost
          port: 3012
          username: root
          password: root
        """
        generator = gpg_secretstore.SecretGenerator(
            secret_type="user_supplied", data_type="yaml", user_supplied_secret=data
        )
        assert generator.getSecretData() == yaml.safe_load(data)
