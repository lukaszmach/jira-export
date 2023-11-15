from unittest.mock import patch, MagicMock, Mock, mock_open
import pytest
import jira_export as j
import os


def test_generate_pdf_from_html_is_file_exist(tmpdir):
    with tmpdir.as_cwd():
        j.generate_pdf_from_html_string(
            html_content='TEST', jira_issue_key='Isuue-1', path_exp='')
        assert os.path.isfile(f'Isuue-1.pdf')


def test_load_settings_nofile_is_file_generated(tmpdir):
    with tmpdir.as_cwd():
        with pytest.raises(ValueError) as exc_info:
            config = j.load_settings()
        assert os.path.isfile(f'settings.ini')


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

        with patch('jira_export.is_server_reachable') as mock_is_server_reachable:
            mock_is_server_reachable.return_value = None
            jira = j.authenticate_jira(jira_url, username, api_token)
            my_user = jira.myself()

        assert my_user['displayName'] == 'John Doe'
        assert type(jira) == j.JIRA


def test_jira_authentication_failed_incorrect_server_adress():

    jira_url = 'https://your_jira_instance/'
    username = 'your-username'
    api_token = 'your_api_token'

    fake_user = {
        'key': username,
        'displayName': 'John Doe',
        'self': f'{jira_url}/rest/api/2/myself',
        'versionNumbers': [1, 2, 3]  # Add a mock 'versionNumbers' field
    }

    with patch('requests.Session.request') as mock_request:
        mock_request.return_value.json.return_value = fake_user
        mock_request.return_value.status_code = 400

        with pytest.raises(j.socket.gaierror,) as exec_info:
            j.authenticate_jira(jira_url, username, api_token)

        assert exec_info.type == j.socket.gaierror


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


class MockJira:
    def myself(self):
        pass


def test_authenticate_jira_are_fuctions_called():

    jira_url = 'https://your-mock-jira-server-url'
    username = 'your-username'
    api_token = 'your_api_token'

    with patch('jira_export.is_server_reachable') as mock_is_server_reachable:

        with patch('jira_export.JIRA', autospec=True) as mock_jira:
            mock_jira_instance = MockJira()
            mock_jira.return_value = mock_jira_instance

            j.authenticate_jira(jira_url, username, api_token)

            mock_is_server_reachable.assert_called_once_with(jira_url)

            mock_jira.assert_called_once_with(
                server=jira_url,
                basic_auth=(username, api_token)
            )


def test_jira_authentication_failed_incorrect_server_adress_format():

    jira_url = 'TEST1'
    username = 'your-username'
    api_token = 'your_api_token'

    fake_user = {
        'key': username,
        'displayName': 'John Doe',
        'self': f'{jira_url}/rest/api/2/myself',
        'versionNumbers': [1, 2, 3]  # Add a mock 'versionNumbers' field
    }

    with patch('requests.Session.request') as mock_request:
        mock_request.return_value.json.return_value = fake_user
        mock_request.return_value.status_code = 400

        with pytest.raises(IndexError) as exec_info:
            j.authenticate_jira(jira_url, username, api_token)

        assert exec_info.type == IndexError


def test_jira_authentication_failed_incorrect_credentials():
    jira_url = 'https://test.test.net/'
    username = 'your-username'
    api_token = 'your_api_token'

    with patch('jira_export.JIRA') as mock_jira_class:
        mock_jira_instance = MagicMock()
        mock_jira_instance.myself.side_effect = j.JIRAError(
            'JIRA authentication failed', status_code=401)
        mock_jira_class.return_value = mock_jira_instance

        with patch('jira_export.is_server_reachable') as mock_is_server_reachable:

            with pytest.raises(j.JIRAError) as exec_info:
                j.authenticate_jira(jira_url, username, api_token)

            assert exec_info.type == j.JIRAError
            assert 'JIRA authentication failed' in str(exec_info.value)


def test_convert_relative_to_absolute_absolute(tmpdir):
    html_str = '<img src="IMAGE.png">'
    path_exp = f'TESTEXP\\'
    issue = 'ISSUE-1'
    relative = False

    with tmpdir.as_cwd():
        html_processed = j.convert_relative_to_absolute(
            html_str, path_exp, issue, relative)
        assert f'<img src="{os.getcwd()}\\{path_exp}{issue}-IMAGE.png' in html_processed


def test_convert_relative_to_absolute_relative(tmpdir):
    html_str = '<img src="IMAGE.png">'
    path_exp = f'TESTEXP\\'
    issue = 'ISSUE-1'
    relative = True

    with tmpdir.as_cwd():
        html_processed = j.convert_relative_to_absolute(
            html_str, path_exp, issue, relative)
        assert f'<img src="{issue}-IMAGE.png' in html_processed


def test_populate_html_attachments_is_list_appended():
    attlist = ['first', 2, 'six']
    html_source = 'Row 1'
    html_processed = j.populate_html_attachments(html_source, attlist)

    assert 'ATTACHMENTS:' in html_processed
    for att in attlist:
        assert f'<a href="{att}">{att}</a>' in html_processed


class MockAttachment:
    def __init__(self, filename, content):
        self.filename = filename
        self.content = content

    def get(self):
        return self.content


class MockIssue:
    def __init__(self, attachments=None):
        self.fields = MagicMock()
        self.fields.attachment = attachments
        self.fields.summary = "Test Summary"
        self.fields.description = "Test Description"
        self.fields.comment.comments = ['comment1', 'comment2']

    def __str__(self):
        return 'ISSUE1'


@pytest.fixture
def mock_jira_issue_good_files():
    attachment1 = MockAttachment('file1.txt', b'content1')
    attachment2 = MockAttachment('file2.txt', b'content2')
    return MockIssue(attachments=[attachment1, attachment2])


@pytest.fixture
def mock_jira_issue_bad_files():
    attachment1 = MockAttachment('?!?/?!', b'content1')
    attachment2 = MockAttachment('file2.txt', b'content2')
    return MockIssue(attachments=[attachment1, attachment2])


def test_download_attachments_validate_files_and_contents_goodfiles(tmpdir, mock_jira_issue_good_files):
    path_exp = 'EXP/'
    with tmpdir.as_cwd():
        os.mkdir(path_exp)
        attachments = j.download_attachments(
            mock_jira_issue_good_files, path_exp)

        expected_filenames = [
            f'{mock_jira_issue_good_files}-file1.txt', f'{mock_jira_issue_good_files}-file2.txt']
        for attachment, expected_filename in zip(attachments, expected_filenames):
            assert attachment == expected_filename

        for attachment in mock_jira_issue_good_files.fields.attachment:
            attachment_path = f'{path_exp}{mock_jira_issue_good_files}-{attachment.filename}'
            with open(attachment_path, 'rb') as file:
                assert file.read() == attachment.content


def test_download_attachments_validate_files_and_contents_bad_files(tmpdir, mock_jira_issue_bad_files):
    path_exp = 'EXP/'
    with tmpdir.as_cwd():
        os.mkdir(path_exp)
        attachments = j.download_attachments(
            mock_jira_issue_bad_files, path_exp)

        expected_filenames = [
            f'{mock_jira_issue_bad_files}-ATT_ERROR', f'{mock_jira_issue_bad_files}-file2.txt']
        expected_attachments = [
            f'{mock_jira_issue_bad_files}-?!?/?!', f'{mock_jira_issue_bad_files}-file2.txt']
        for expected_filename in expected_filenames:
            assert os.path.isfile(f"{path_exp}{expected_filename}")
        for expected_attachment in expected_attachments:
            assert expected_attachment in attachments


@pytest.mark.parametrize('html_source,html_expected', [('*strong*', f'<p><strong>strong</strong></p>\r\n'),
                                                       (f'!attached-image.gif!',
                                                        f'<p><img src="attached-image.gif" /></p>\r\n'),
                                                       ('||heading 1||heading 2||heading 3|||col A1|col A2|col A3|',
                                                        '<table>\r\n<tbody>\r\n<tr class="odd">\r\n<td><p>heading 1</p></td>\r\n<td><p>heading 2</p></td>\r\n<td><p>heading 3</p></td>\r\n<td><p>col A1</p></td>\r\n<td><p>col A2</p></td>\r\n<td><p>col A3</p></td>\r\n</tr>\r\n</tbody>\r\n</table>\r\n'),
                                                       ('[^attachment.ext]', '<p><a href="attachment.ext" class="attachment">attachment.ext</a></p>\r\n'),
                                                       ("h1. Biggest heading", '<h1>Biggest heading</h1>\r\n')])
def test_convert_jira_wiki_markup(html_source, html_expected):
    html_processed = j.convert_jira_wiki_markup(html_source)
    assert html_processed == html_expected


@pytest.fixture
def jira_mock(mocker):
    return mocker.Mock()


def test_find_issues_is_called(jira_mock):

    jira_project_key = "YOUR_PROJECT_KEY"
    start_at = 0
    max_results = 10
    result_list_mock = Mock(spec=j.client.ResultList)
    jira_mock.search_issues.return_value = result_list_mock
    result = j.find_issues(jira_project_key, jira_mock, start_at, max_results)
    jira_mock.search_issues.assert_called_once_with(
        f'project={jira_project_key}', startAt=start_at, maxResults=max_results
    )
    assert isinstance(result, j.client.ResultList)


def test_populate_html_fields_description_filled():
    jira_issue_mock = MockIssue()
    jira_issue_mock.fields.summary = "Test Summary"
    jira_issue_mock.fields.description = "Test Description"
    result = j.populate_html_fields(jira_issue_mock)
    expected = f'<h1>ISSUE1</h1><h2>Test Summary</h2><p>Test Description</p>\r\n'
    assert result == expected


def test_populate_html_fields_description_empty():
    jira_issue_mock = MockIssue()
    jira_issue_mock.fields.summary = "Test Summary"
    jira_issue_mock.fields.description = None
    result = j.populate_html_fields(jira_issue_mock)
    expected = f'<h1>ISSUE1</h1><h2>Test Summary</h2>DESCRIPTION EMPTY'
    assert result == expected


def test_populate_html_comments():  # rewrite later to include test to multiple comments - problem with MOck - Jira setup
    jira_issue_mock = MockIssue()
    jira_mock = Mock(spec=j.JIRA)
    jira_mock.comment().created = '1'
    jira_mock.comment().author.displayName = 'John'
    jira_issue_mock.fields.comment.comments = ['comment1']
    convert_jira_wiki_markup_mock = Mock()
    convert_jira_wiki_markup_mock.return_value = "Formatted Comment Body"
    expected = "<h3>COMMENTS:</h3>1 <br> John <br>Formatted Comment Body <br>"
    with patch('jira_export.convert_jira_wiki_markup', convert_jira_wiki_markup_mock):
        result = j.populate_html_comments('', jira_issue_mock, jira_mock)
        assert result == expected
