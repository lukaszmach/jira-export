import configparser
import re
import socket
import sys
from dataclasses import dataclass
from os import getcwd, mkdir, path

import keyboard
import pypandoc
from jira import JIRA, client, resources
from jira.exceptions import JIRAError
from pdfkit import configuration, from_string

SETTINGS_FILE = 'settings.ini'


@dataclass
class Settings:
    jira_base_url: str = 'https://your_jira_instance/'
    jira_username: str = 'your_jira@username'
    jira_api_token: str = 'your_jira_api_token'
    export_path: str = 'EXPORT\\'
    save_to_html: bool = True
    save_to_pdf: bool = True
    jira_project: str = 'TEST'


def is_server_reachable(server_url: str) -> None:
    # Extract the hostname or IP address from the server URL
    hostname = server_url.split('//')[1].split('/')[0]

    # Check if the hostname can be resolved to an IP address
    socket.gethostbyname(hostname)


def validate_settings(config: configparser.ConfigParser) -> configparser.ConfigParser:
    '''Validates settings.ini (loaded ConfigParser object), checks if all required fields are present, add missing entries and returns ConfigParser object'''

    # Creating default settings structure
    settings = Settings()
    config_default = configparser.ConfigParser()
    config_default['JIRA_ACCESS'] = {'jira_base_url': settings.jira_base_url,
                                     'jira_username': settings.jira_username,
                                     'jira_api_token': settings.jira_api_token}
    config_default['EXPORT_OPTIONS'] = {'export_path': settings.export_path,
                                        'save_to_html': settings.save_to_html,
                                        'save_to_pdf': settings.save_to_pdf}
    config_default['ISSUE_FILTER'] = {'jira_project': settings.jira_project}

    # Going through loaded settings file, and adding missing Sections/options
    settings_changed = False

    for section in config_default.sections():
        for option in config_default.options(section):
            if not config.has_option(section, option):
                settings_changed = True
                try:
                    config.set(section, option,
                               config_default.get(section, option))
                # if no provided SECTION is found, creates one.
                except configparser.NoSectionError:
                    config.add_section(section)
                    config.set(section, option,
                               config_default.get(section, option))

    # Validate if boolean options have proper values
    section = 'EXPORT_OPTIONS'
    option = ['save_to_html', 'save_to_pdf']

    for opt in option:
        try:
            config.getboolean(section, opt)
        except ValueError:
            config.set(section, opt,
                       config_default.get(section, opt))
            settings_changed = True

    # Notifications if settings changed -> exit program
    if settings_changed:
        with open(SETTINGS_FILE, "w") as save_stream:
            config.write(save_stream)
        raise ValueError
    return config


def load_settings_to_dataclass(config: configparser.ConfigParser) -> Settings:
    '''Loads settings.ini to dataclass'''

    settings = Settings()
    settings.jira_base_url = config.get('JIRA_ACCESS', 'jira_base_url')
    settings.jira_username = config.get('JIRA_ACCESS', 'jira_username')
    settings.jira_api_token = config.get('JIRA_ACCESS', 'jira_api_token')
    settings.export_path = config.get('EXPORT_OPTIONS', 'export_path')
    settings.save_to_html = config.getboolean('EXPORT_OPTIONS', 'save_to_html')
    settings.save_to_pdf = config.getboolean('EXPORT_OPTIONS', 'save_to_pdf')
    settings.jira_project = config.get('ISSUE_FILTER', 'jira_project')
    return settings


def load_settings() -> Settings:
    '''Loads settings.ini from file, validates it and returns Settings object'''

    config = configparser.ConfigParser()
    config.read(SETTINGS_FILE)
    config = validate_settings(config)
    settings = load_settings_to_dataclass(config)
    return settings


def authenticate_jira(jira_url: str, jira_username: str, jira_api_token: str) -> JIRA:
    '''Set up JIRA object. Others method of authentication left commented (They are not tested)'''

    is_server_reachable(jira_url)
    jira = JIRA(
        server=jira_url,
        # basic_auth=("admin", "admin"),  # a username/password tuple [Not recommended]
        # Jira Cloud: a username/token tuple
        basic_auth=(jira_username, jira_api_token),
        # token_auth="API token",  # Self-Hosted Jira (e.g. Server): the PAT token
        # auth=("admin", "admin"),  # a username/password tuple for cookie auth [Not recommended]
    )
    jira.myself()  # to trigger jira authentication, without that even if connection is not succesfull it will not trigger any error
    return jira


def find_issues(jira_project_key: str, jira: JIRA, start_at: int, max_results: int) -> client.ResultList:
    '''Returns jira.client.ResultList based on provided JIRA instance and jQL containing Project key'''

    result_list = jira.search_issues(
        f'project={jira_project_key}', startAt=start_at, maxResults=max_results)
    return result_list


def generate_pdf_from_html_string(html_content: str, jira_issue_key: resources.Issue, path_exp: str) -> None:
    '''Uses pdfkit to generate pdf to EXPORT_PATH from provided html_content string'''

    options = {
        'enable-local-file-access': True,
        'keep-relative-links': True,
        'allow': path.join(getcwd(), path_exp),
        'cache-dir': path.join(getcwd(), path_exp),
        'encoding': 'utf-8',
    }
    # Validation of any errors that migth come from wkhtmltopdf. Current known issue if there are incorrect links in <img> - might happen if someone used Jira markup as plain text which is converted incorrectly to html markup
    try:
        from_string(
            html_content, path.join(path_exp, f"{jira_issue_key}.pdf"), options=options)
    except IOError:
        with open(path.join(path_exp, f"{jira_issue_key}-ERROR.pdf"), "w") as save_stream:
            save_stream.write("ERROR")


def populate_html_fields(jira_issue: resources.Issue) -> str:
    '''Initial creation of html formatted string. Added Issue number, Name and description from jira. Markup from Jira converted by pypandoc'''
    summary = jira_issue.fields.summary
    description_raw = jira_issue.fields.description
    try:
        description = convert_jira_wiki_markup(description_raw)
    except AttributeError:
        description = 'DESCRIPTION EMPTY'
    html_content = f'<h1>{jira_issue}</h1><h2>{summary}</h2>{description}'
    return html_content


def populate_html_comments(html_content: str, jira_issue: resources.Issue, jira: JIRA) -> str:
    ''' Appending Comments from JIRA (Created, Author, Comment body) to html formatted str.  Markup from Jira converted by pypandoc'''
    html_content += f'<h3>COMMENTS:</h3>'
    for c in jira_issue.fields.comment.comments:
        html_content += f'{jira.comment(jira_issue,c).created} <br> '
        html_content += f'{jira.comment(jira_issue,c).author.displayName} <br>'
        comment_body_raw = jira.comment(jira_issue, c).body
        comment_body = convert_jira_wiki_markup(comment_body_raw)
        html_content += f'{comment_body} <br>'
    return html_content


def populate_html_attachments(html_content: str, attachments: list[str]) -> str:
    '''Append links with attachments to html formatted str. Uses list of attachment.'''
    html_content += f'<h3>ATTACHMENTS:</h3>'
    for a in attachments:
        html_content += f'<a href="{a}">{a}</a><br>'
    return html_content


def download_attachments(jira_issue: resources.Issue, path_exp: str) -> list[str]:
    '''Downloads attachment to EXPORT_PATH and returns list of filenames'''

    attachments = []
    for a in jira_issue.fields.attachment:
        try:
            filename = f'{jira_issue}-{a.filename}'
            filepath = path.join(path_exp, filename)
            attachments.append(filename)
            with open(filepath, 'wb') as save_stream:
                save_stream.write(a.get())
            print(f'Attachment: {a} for issue {jira_issue} downloaded')
        except OSError:
            with open(path.join(path_exp, f'{jira_issue}-ATT_ERROR'), 'wb') as save_stream:
                save_stream.write(a.get())
    return attachments


def convert_jira_wiki_markup(html_content: str) -> str:
    '''Uses pypandoc to convert JIRA markups to HTML'''

    return pypandoc.convert_text(html_content, 'html', format='jira')


def save_to_html(html_content: str, filename: str, path_exp: str) -> None:
    '''Save html formatted str to path_exp\\filename'''

    file_path = path.join(path_exp, f'{filename}.html')
    with open(file_path, 'w', encoding='utf-8') as save_stream:
        save_stream.write(html_content)


def validate_export_path(path_exp: str) -> None:
    '''Validates if folder for Exporting file exists and is not a file of the same name'''

    if (path.exists(path_exp)):
        if not path.isdir(path_exp):
            raise FileExistsError

    else:
        mkdir(path_exp)
        print(f'Created export folder {path_exp}')


def populate_html(issue: resources.Issue, path_exp: str, jira: JIRA) -> str:
    '''Creates and populates str with html formatted content from JIRA fields. returns str '''

    attachments = download_attachments(issue, path_exp)
    html_content = populate_html_fields(issue)
    html_content = populate_html_comments(html_content, issue, jira)
    html_content = populate_html_attachments(html_content, attachments)
    return html_content


def convert_relative_to_absolute(html_str: str, path_exp: str, issue: resources.Issue, relative: bool) -> str:
    '''Convert image links in html formatted str from relative path to absolute paths. Needed for properly saving pdf with images by pdfkit. As a PATH it uses export path defined in settings.ini.

    Additionally adding Jira issue number to links.

    Images are resized to width="300" height="200" '''

    # Get the current working directory
    current_directory = path.join(getcwd(), path_exp)

    # Define a regular expression pattern to match image tags
    img_pattern = re.compile(r'<img\s+[^>]*src="([^"]+)"[^>]*>')

    # Replace relative image links with absolute paths depending on relative switch. Add issue number to filename
    def replace_img(match):
        img_src = match.group(1)
        if not img_src.startswith(('http://', 'https://', 'file://')):
            if relative:
                abs_img_src = f'{issue}-{img_src}'
            else:
                abs_img_src = path.abspath(
                    path.join(current_directory, f'{issue}-{img_src}'))

            # migth provide later settings to change size of images
            return f'<img src="{abs_img_src}" width="300" height="200">'
        return match.group(0)

    # Use the regular expression pattern to find and replace image tags
    modified_html = img_pattern.sub(replace_img, html_str)

    return modified_html


def validate_wkhtmltopdf_exists():

    config = configuration()


def validate_pandoc_exists():

    pypandoc.get_pandoc_version()


def main():

    try:
        settings = load_settings()
    except ValueError as e:
        print(f'{SETTINGS_FILE} was created/updated with default values. \nPlease rerun program after updating manually values in {SETTINGS_FILE} \n {e}')
        sys.exit(0)

    try:
        validate_wkhtmltopdf_exists()
    except OSError:
        print('\nProgram wkhtmltopdf was not found in system. Export to pdf will not be possibble. Settings were changed: save_to_pdf = False\n')
        settings.save_to_pdf = False

    try:
        validate_pandoc_exists()
    except OSError:
        print('\nProgram pandoc was not found in system. It is required for program to properly work\n')
        sys.exit(0)

    choice = input(
        f'Program will begin to export issues from JIRA based on values provided in {SETTINGS_FILE}. Continue? [y/n] :')

    if not choice.lower() == 'y':
        print('Aborted')
        sys.exit(0)

    path_exp = settings.export_path
    # config.get('EXPORT_OPTIONS', 'export_path')

    try:
        validate_export_path(path_exp)
    except FileExistsError:
        print('There is File with the same Name as Directory specified in settings. Remove the file or change settings.')
        sys.exit(1)

    try:
        jira = authenticate_jira(
            settings.jira_base_url, settings.jira_username, settings.jira_api_token)

    except IndexError:
        print("Incorrect url adress format")
        sys.exit(1)
    except socket.gaierror as error:
        print(
            f"Cannot connect to url. Check if url is correct in {SETTINGS_FILE}")
        sys.exit(1)
    except JIRAError as error:
        print(
            f"Failed to connect to Jira server: \nURL:{error.url}\n{error.response}\n{error.text}")
        sys.exit(1)

    # Initialize startAt and maxResults
    startAt = 0
    maxResults = 50

    while True:

        # Get the issues using the Jira module's search method
        try:
            result_list = find_issues(
                settings.jira_project, jira, startAt, maxResults)
            # config.get( 'ISSUE_FILTER', 'jira_project')
        except JIRAError as error:
            print(
                f"Failed to find provided project name: {settings.jira_project}\n{error.response}\n{error.text}")
            sys.exit(1)

        # Break the loop if no more issues are returned
        if not result_list:
            break

        # Iterate through the results
        for issue in result_list:

            # Generate formatted html str
            html_content = populate_html(issue, path_exp, jira)

            # Save based on options values - formatting differently with convert_relative_to_absolute due to html working best with relative links and pdf with absolute ones (still need in both cases to modify images to have [Issue - filename] name)

            if settings.save_to_html:

                html_content_html = convert_relative_to_absolute(
                    html_content, path_exp, issue, True)
                save_to_html(html_content_html, issue, path_exp)
                print(f"HTML generated for {issue}")
            if settings.save_to_pdf:

                html_content_pdf = convert_relative_to_absolute(
                    html_content, path_exp, issue, False)
                generate_pdf_from_html_string(
                    html_content_pdf, issue, path_exp)
                print(f"PDF generated for {issue}")

        # Update the startAt for the next iteration
        startAt += maxResults

    print("Press any key to exit...")
    keyboard.read_event(suppress=True)


if __name__ == '__main__':
    main()
