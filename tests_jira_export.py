from unittest.mock import patch
import pytest
import jira_export as j
import os


def test_generate_pdf_from_html(tmpdir):
    with tmpdir.as_cwd():
        j.generate_pdf_from_html_string(
            html_content='TEST', jira_issue_key='Isuue-1', path_exp='')
        assert os.path.isfile(f'Isuue-1.pdf')


def test_load_settings_nofile(tmpdir):
    with tmpdir.as_cwd():
        with pytest.raises(SystemExit) as exc_info:          
            config = j.load_settings()
        assert os.path.isfile(f'settings.ini')
        assert exc_info.value.code == 0


def test_load_settings_file_exists(tmpdir):
    config_default = j.configparser.ConfigParser()
    config_default['JIRA_ACCESS'] = {'jira_base_url': 'https://your_jira_instance/',
                                     'jira_username': 'your_jira@username',
                                     'jira_api_token': 'yout_jira_api_token'}
    config_default['EXPORT_OPTIONS'] = {'export_path': f"EXPORT\\",
                                        'save_to_html': False,
                                        'save_to_pdf': True}
    config_default['ISSUE_FILTER'] = {'jira_project': "TEST"}
    with tmpdir.as_cwd():
        with open(j.SETTINGS_FILE, "w") as save_stream:
            config_default.write(save_stream)        
        config = j.load_settings()
        assert config == config_default
        

def test_jira_authentication_success():
    # Replace these with your test data
    jira_url = 'https://your-mock-jira-server-url'
    username = 'your-username'
    api_token = 'your_api_token'

    # Simulate a complete successful Jira authentication response
    fake_user = {
        'key': username,
        'displayName': 'John Doe',
        'self': f'{jira_url}/rest/api/2/myself',
        'versionNumbers': [1, 2, 3]  # Add a mock 'versionNumbers' field
    }

    with patch('requests.Session.request') as mock_request:
        mock_request.return_value.json.return_value = fake_user
        mock_request.return_value.status_code = 200

        # Create a Jira client and perform the authentication
        with patch('jira_export.is_server_reachable') as mock_is_server_reachable:
            mock_is_server_reachable.return_value = None
            jira = j.authenticate_jira(jira_url, username, api_token)
            my_user = jira.myself()

        # Assert that the authentication was successful
        assert my_user['displayName'] == 'John Doe'

