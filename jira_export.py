import configparser
import keyboard
from os import getcwd, path, mkdir
import socket
import sys

from jira import JIRA, client, resources
from jira.exceptions import JIRAError
from pdfkit import from_string
import pypandoc

SETTINGS_FILE = 'settings.ini'


def is_server_reachable(server_url: str) -> None:
    # Extract the hostname or IP address from the server URL
    try:
        hostname = server_url.split('//')[1].split('/')[0]
    except IndexError:
        print("Invalid server address format.")
        sys.exit(1)

    try:
        # Check if the hostname can be resolved to an IP address
        socket.gethostbyname(hostname)

    except socket.gaierror:
        print(f"Failed to resolve the hostname: {hostname}")
        sys.exit(1)


def validate_settings(config: configparser.ConfigParser) -> configparser.ConfigParser:
    '''Validates settings.ini (loaded ConfigParser object), checks if all required fields are prsent, add missing entries and returns ConfigParser object'''

    config_default = configparser.ConfigParser()
    config_default['JIRA_ACCESS'] = {'jira_base_url': 'https://your_jira_instance/',
                                     'jira_username': 'your_jira@username',
                                     'jira_api_token': 'yout_jira_api_token'}
    config_default['EXPORT_OPTIONS'] = {'export_path': f"EXPORT\\",
                                        'save_to_html': True,
                                        'save_to_pdf': True}
    config_default['ISSUE_FILTER'] = {'jira_project': "TEST"}

    # if not config.has_section('JIRA_ACCESS'):
    #     config.add_section('JIRA_ACCESS')

    # if not config.has_option('JIRA_ACCESS', 'jira_base_url'):
    #     config.set('JIRA_ACCESS', 'jira_base_url',
    #                'https://your_jira_instance/')

    # if not config.has_option('JIRA_ACCESS', 'jira_username'):
    #     config.set('JIRA_ACCESS', 'jira_username', 'your_jira@username')

    # if not config.has_option('JIRA_ACCESS', 'jira_api_token'):
    #     config.set('JIRA_ACCESS', 'jira_api_token', 'your_jira_api_token')

    # if not config.has_section('EXPORT_OPTIONS'):
    #     config.add_section('EXPORT_OPTIONS')

    # if not config.has_option('EXPORT_OPTIONS', 'export_path'):
    #     config.set('EXPORT_OPTIONS', 'export_path', f"EXPORT\\")

    # if not config.has_option('EXPORT_OPTIONS', 'save_to_html'):
    #     config.set('EXPORT_OPTIONS', 'save_to_html', 'True')

    # if not config.has_option('EXPORT_OPTIONS', 'save_to_pdf'):
    #     config.set('EXPORT_OPTIONS', 'save_to_pdf', 'True')

    # if not config.has_section('ISSUE_FILTER'):
    #     config.add_section('ISSUE_FILTER')

    # if not config.has_option('ISSUE_FILTER', 'jira_project'):
    #     config.set('ISSUE_FILTER', 'jira_project', 'TEST')

    settings_changed = False
    for section in config_default.sections():
        for option in config_default.options(section):
            if not config.has_option(section, option):
                settings_changed = True
                try:
                    config.set(section, option,
                               config_default.get(section, option))
                except configparser.NoSectionError:
                    config.add_section(section)
                    config.set(section, option,
                               config_default.get(section, option))

    if settings_changed:
        with open(SETTINGS_FILE, "w") as save_stream:
            config.write(save_stream)
        print(f'Settings inside {SETTINGS_FILE}  were incorrect. \n {SETTINGS_FILE} was updated. \n Please rerun program after updating manually values in {SETTINGS_FILE}')
        sys.exit(0)

    return config


def load_settings() -> configparser.ConfigParser:
    '''Loads settings.ini from file, validates it and returns ConfigParser object'''
    config = configparser.ConfigParser()
    try:
        with open(SETTINGS_FILE, "r") as load_strem:
            config.read(SETTINGS_FILE)
    except FileNotFoundError:
        config.read(SETTINGS_FILE)
    config = validate_settings(config)
    return config


def authenticate_jira(jira_url: str, jira_username: str, jira_api_token: str) -> JIRA:
    '''Set up JIRA object. Others method of authentication left commented (They are not tested)'''

    is_server_reachable(jira_url)
    try:
        return JIRA(
            server=jira_url,
            # basic_auth=("admin", "admin"),  # a username/password tuple [Not recommended]
            # Jira Cloud: a username/token tuple
            basic_auth=(jira_username, jira_api_token),
            # token_auth="API token",  # Self-Hosted Jira (e.g. Server): the PAT token
            # auth=("admin", "admin"),  # a username/password tuple for cookie auth [Not recommended]
        )
    except JIRAError as error:
        print(
            f"Failed to connect to Jira server: \nURL:{error.url}\n{error.response}\n{error.text}")
        sys.exit(1)


def find_issues(jira_project_key: str, jira: JIRA, start_at: int, max_results: int) -> client.ResultList:
    '''Returns jira.client.ResultList based on provided JIRA instance and jQL containing Project key'''

    try:
        result_list = jira.search_issues(
            f'project={jira_project_key}', startAt=start_at, maxResults=max_results)
        return result_list
    except JIRAError as error:
        print(
            f"Failed to find provided project name: {jira_project_key} \n{error.response}\n{error.text}")
        sys.exit(1)


def generate_pdf_from_html_string(html_content: str, jira_issue_key: resources.Issue, path_exp: str) -> None:
    '''Uses pdfkit to generate pdf to EXPORT_PATH from provided html_content string'''
    options = {
        'enable-local-file-access': True,
        'keep-relative-links': True,
        'allow': getcwd(),
        'cache-dir': getcwd(),
        'encoding': 'utf-8',
        'no-images': True
    }
    from_string(
        html_content, f"{path_exp}{jira_issue_key}.pdf", options=options)


def populate_html_fields(jira_issue: resources.Issue) -> str:
    summary = jira_issue.fields.summary
    description_raw = jira_issue.fields.description
    try:
        description = convert_jira_wiki_markup(description_raw)
    except AttributeError:
        description = 'DESCRIPTION EMPTY'
    html_content = f'<h1>{jira_issue}</h1><h2>{summary}</h2>{description}'
    return html_content


def populate_html_comments(html_content: str, jira_issue: str, jira: JIRA) -> str:
    html_content += f'<h3>COMMENTS:</h3>'
    for c in jira_issue.fields.comment.comments:
        html_content += f'{jira.comment(jira_issue,c).created} <br> '
        html_content += f'{jira.comment(jira_issue,c).author.displayName} <br>'
        comment_body_raw = jira.comment(jira_issue, c).body
        comment_body = convert_jira_wiki_markup(comment_body_raw)
        html_content += f'{comment_body} <br>'
    return html_content


def populate_html_attachments(html_content: str, attachments: list[str], jira_issue: resources.Issue) -> str:
    html_content += f'<h3>ATTACHMENTS:</h3>'
    for a in attachments:
        html_content += f'<a href="{a}">{a}</a><br />'
    return html_content


def download_attachments(jira_issue: resources.Issue, path_exp: str) -> list[str]:
    '''Downloads attachment to EXPORT_PATH and returns list of filenames'''
    attachments = []
    for a in jira_issue.fields.attachment:
        attachments.append(a.filename)
        with open(f'{path_exp}{a.filename}', 'wb') as save_stream:
            save_stream.write(a.get())
        print(f'Attachment: {a} for issue {jira_issue} downloaded')
    return attachments


def convert_jira_wiki_markup(html_content: str) -> str:
    '''Uses pypandoc to convert JIRA markups to HTML'''
    return pypandoc.convert_text(html_content, 'html', format='jira')


def save_to_html(html_content: str, filename: str, path_exp: str) -> None:
    with open(f'{path_exp}{filename}.html', 'w', encoding='utf-8') as save_stream:
        save_stream.write(html_content)


def validate_export_path(path_exp: str) -> None:
    if (path.exists(path_exp)):
        if not path.isdir(path_exp):
            print('There is File with the same Name as Directory specified in settings. Remove the file or change settings.')
            sys.exit(1)
    else:
        mkdir(path_exp)
        print(f'Created export folder {path_exp}')


def populate_html(issue, path_exp, jira):
    attachments = download_attachments(issue, path_exp)
    html_content = populate_html_fields(issue)
    html_content = populate_html_comments(html_content, issue, jira)
    html_content = populate_html_attachments(html_content, attachments, issue)
    return html_content


def main():
    config = load_settings()

    choice = input(
        f'Program will begin to export issues from JIRA based on values provided in {SETTINGS_FILE}. Continue? [y/n] :')

    if not choice.lower() == 'y':
        print('Aborted')
        sys.exit(0)

    path_exp = config.get('EXPORT_OPTIONS', 'export_path')
    validate_export_path(path_exp)

    jira = authenticate_jira(config.get('JIRA_ACCESS', 'jira_base_url'), config.get(
        'JIRA_ACCESS', 'jira_username'), config.get('JIRA_ACCESS', 'jira_api_token'))

    # Initialize startAt and maxResults
    startAt = 0
    maxResults = 50

    while True:
        # Get the issues using the Jira module's search method
        result_list = find_issues(config.get(
            'ISSUE_FILTER', 'jira_project'), jira, startAt, maxResults)

        # Break the loop if no more issues are returned
        if not result_list:
            break

        # Iterate through the results
        for issue in result_list:
            html_content = populate_html(issue, path_exp, jira)

            if config.getboolean('EXPORT_OPTIONS', 'save_to_html'):
                save_to_html(html_content, issue, path_exp)
                print(f"HTML generated for {issue}")
            if config.getboolean('EXPORT_OPTIONS', 'save_to_pdf'):
                generate_pdf_from_html_string(html_content, issue, path_exp)
                print(f"PDF generated for {issue}")

        # Update the startAt for the next iteration
        startAt += maxResults

    print("Press any key to exit...")
    keyboard.read_event(suppress=True)


if __name__ == '__main__':
    main()
