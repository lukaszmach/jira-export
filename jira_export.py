import configparser
from typing import Dict, Any
from pdfkit import from_string
from jira import JIRA
import pypandoc
from os import getcwd



EXPORT_PATH = f"EXPORT\\"



SETTINGS_FILE = 'settings.ini'


PROJECT_KEY = "TEST"


def create_default_settings():
    config = configparser.ConfigParser()
    config['JIRA_ACCESS'] = {'jira_base_url': 'https://your_jira_instance/',
                             'jira_username': 'your_jira@username',
                             'jira_api_token': 'yout_jira_api_token'}
    config['EXPORT_OPTIONS'] = {'export_path': f"EXPORT\\",
                                'save_to_html': True,
                                'save_to_pdf': True}
    
    with open(SETTINGS_FILE, "w") as save_stream:
        config.write(save_stream)


def load_settings() -> configparser.ConfigParser:
    config = configparser.ConfigParser()
    try:
        with open(SETTINGS_FILE, "r") as load_strem:
            config.read(SETTINGS_FILE)
    except FileNotFoundError:
        create_default_settings()
        config.read(SETTINGS_FILE)

    return config


def authenticate_jira(jira_url: str, jira_username: str, jira_api_token: str) -> JIRA:
    return JIRA(
        server=jira_url,
        # basic_auth=("admin", "admin"),  # a username/password tuple [Not recommended]
        # Jira Cloud: a username/token tuple
        basic_auth=(jira_username, jira_api_token),
        # token_auth="API token",  # Self-Hosted Jira (e.g. Server): the PAT token
        # auth=("admin", "admin"),  # a username/password tuple for cookie auth [Not recommended]
    )


def find_issues(jira_project_key: str, jira: JIRA) -> Dict[str, Any]:
    result_list = jira.search_issues(f'project={jira_project_key}')
    return result_list


def generate_pdf_from_html_string(html_content, jira_issue_key) -> None:
    options = {
        'enable-local-file-access': True,
        'keep-relative-links': True,
        'allow': getcwd(),
        'cache-dir': getcwd()
    }
    from_string(
        html_content, f"{EXPORT_PATH}{jira_issue_key}.pdf", options=options)


def populate_html_fields(jira_issue: str) -> str:
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


def populate_html_attachments(html_content: str, attachments: list[str], jira_issue: str) -> str:
    html_content += f'<h3>ATTACHMENTS:</h3>'
    for a in attachments:
        html_content += f'<a href="{a}">{a}</a><br />'
    return html_content


def download_attachments(jira_issue: str) -> list[str]:
    '''Downloads attachment to EXPORT_PATH and returns list of filenames'''
    attachments = []
    for a in jira_issue.fields.attachment:
        attachments.append(a.filename)
        with open(f'{EXPORT_PATH}{a.filename}', 'wb') as save_stream:
            save_stream.write(a.get())
        print (f'Attachment: {a} for issue {jira_issue} downloaded')
    return attachments


def convert_jira_wiki_markup(html_content: str) -> str:
    return pypandoc.convert_text(html_content, 'html', format='jira')


def save_to_html(html_content: str, filename: str) -> None:
    with open(f'{EXPORT_PATH}{filename}.html', 'w') as save_stream:
        save_stream.write(html_content)


def main():
    config = load_settings()
    jira = authenticate_jira(config.get('JIRA_ACCESS','jira_base_url'), config.get('JIRA_ACCESS','jira_username'), config.get('JIRA_ACCESS','jira_api_token'))
    result_list = find_issues(PROJECT_KEY, jira)

    for issue in result_list:
        attachments = download_attachments(issue)
        html_content = populate_html_fields(issue)
        html_content = populate_html_comments(html_content, issue, jira)
        html_content = populate_html_attachments(
            html_content, attachments, issue)
        if config.getboolean('EXPORT_OPTIONS','save_to_html'):
            save_to_html(html_content, issue)
            print(f"HTML generated for {issue}")
        if config.getboolean('EXPORT_OPTIONS','save_to_pdf'):
            generate_pdf_from_html_string(html_content, issue)
            print(f"PDF generated for {issue}")
        


if __name__ == '__main__':
    main()
