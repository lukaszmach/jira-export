import configparser
from os import getcwd, path, mkdir
import sys


from jira import JIRA, client, resources
from pdfkit import from_string
import pypandoc


SETTINGS_FILE = 'settings.ini'


PROJECT_KEY = "TEST"


def validate_settings(config: configparser.ConfigParser) -> configparser.ConfigParser:
    '''Validates settings.ini (loaded ConfigParser object), checks if all required fields are prsent, add missing entries and returns ConfigParser object'''

    if not config.has_section('JIRA_ACCESS'):
        config.add_section('JIRA_ACCESS')

    if not config.has_option('JIRA_ACCESS', 'jira_base_url'):
        config.set('JIRA_ACCESS', 'jira_base_url',
                   'https://your_jira_instance/')

    if not config.has_option('JIRA_ACCESS', 'jira_username'):
        config.set('JIRA_ACCESS', 'jira_username', 'your_jira@username')

    if not config.has_option('JIRA_ACCESS', 'jira_api_token'):
        config.set('JIRA_ACCESS', 'jira_api_token', 'yout_jira_api_token')

    if not config.has_section('EXPORT_OPTIONS'):
        config.add_section('EXPORT_OPTIONS')

    if not config.has_option('EXPORT_OPTIONS', 'export_path'):
        config.set('EXPORT_OPTIONS', 'export_path', f"EXPORT\\")

    if not config.has_option('EXPORT_OPTIONS', 'save_to_html'):
        config.set('EXPORT_OPTIONS', 'save_to_html', 'True')

    if not config.has_option('EXPORT_OPTIONS', 'save_to_pdf'):
        config.set('EXPORT_OPTIONS', 'save_to_pdf', 'True')

    if not config.has_section('ISSUE_FILTER'):
        config.add_section('ISSUE_FILTER')

    if not config.has_option('ISSUE_FILTER', 'jira_project'):
        config.set('ISSUE_FILTER', 'jira_project', 'TEST')

    with open(SETTINGS_FILE, "w") as save_stream:
        config.write(save_stream)
    return config


# not used anymore -> to rmeove
# def create_default_settings() -> None:
#     config = configparser.ConfigParser()
#     config['JIRA_ACCESS'] = {'jira_base_url': 'https://your_jira_instance/',
#                              'jira_username': 'your_jira@username',
#                              'jira_api_token': 'yout_jira_api_token'}
#     config['EXPORT_OPTIONS'] = {'export_path': f"EXPORT\\",
#                                 'save_to_html': True,
#                                 'save_to_pdf': True}

#     with open(SETTINGS_FILE, "w") as save_stream:
#         config.write(save_stream)
# ###


def load_settings() -> configparser.ConfigParser:
    '''Loads settings.ini from file, validates it and returns ConfigParser object'''
    config = configparser.ConfigParser()
    try:
        with open(SETTINGS_FILE, "r") as load_strem:
            config.read(SETTINGS_FILE)
    except FileNotFoundError:
        # create_default_settings()
        config.read(SETTINGS_FILE)
    config = validate_settings(config)
    return config


def authenticate_jira(jira_url: str, jira_username: str, jira_api_token: str) -> JIRA:
    '''Set up JIRA object. Others method of authentication left commented (They are not tested)'''
    return JIRA(
        server=jira_url,
        # basic_auth=("admin", "admin"),  # a username/password tuple [Not recommended]
        # Jira Cloud: a username/token tuple
        basic_auth=(jira_username, jira_api_token),
        # token_auth="API token",  # Self-Hosted Jira (e.g. Server): the PAT token
        # auth=("admin", "admin"),  # a username/password tuple for cookie auth [Not recommended]
    )


def find_issues(jira_project_key: str, jira: JIRA) -> client.ResultList:
    '''Returns jira.client.ResultList based on provided JIRA instance and jQL containing Project key'''
    result_list = jira.search_issues(f'project={jira_project_key}')
    return result_list


def generate_pdf_from_html_string(html_content: str, jira_issue_key: resources.Issue, path_exp: str) -> None:
    '''Uses pdfkit to generate pdf to EXPORT_PATH from provided html_content string'''
    options = {
        'enable-local-file-access': True,
        'keep-relative-links': True,
        'allow': getcwd(),
        'cache-dir': getcwd(),
        'encoding': 'utf-8',
        'no-images':True 
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


def main():
    config = load_settings()

    choice = input(
        f'Program will begin to export issues from JIRA based on values provided in settings.ini . Continue? [y/n] :')

    if not choice.lower() == 'y':
        print('Aborted')
        sys.exit(0)

    path_exp = config.get('EXPORT_OPTIONS', 'export_path')
    validate_export_path(path_exp)

    jira = authenticate_jira(config.get('JIRA_ACCESS', 'jira_base_url'), config.get(
        'JIRA_ACCESS', 'jira_username'), config.get('JIRA_ACCESS', 'jira_api_token'))
    result_list = find_issues(config.get('ISSUE_FILTER', 'jira_project'), jira)

    for issue in result_list:
        attachments = download_attachments(issue, path_exp)
        html_content = populate_html_fields(issue)
        html_content = populate_html_comments(html_content, issue, jira)
        html_content = populate_html_attachments(
            html_content, attachments, issue)

        if config.getboolean('EXPORT_OPTIONS', 'save_to_html'):
            save_to_html(html_content, issue, path_exp)
            print(f"HTML generated for {issue}")
        if config.getboolean('EXPORT_OPTIONS', 'save_to_pdf'):
            generate_pdf_from_html_string(html_content, issue, path_exp)
            print(f"PDF generated for {issue}")
    input('Please Enter to exit')


if __name__ == '__main__':
    main()
