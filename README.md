<a name="readme-top"></a>

[![LinkedIn][linkedin-shield]][linkedin-url]

# Jira export

Small program for exporting issues from Jira to pdf or html.


## Prerequisites

  wkhtmltopdf - https://wkhtmltopdf.org/ #Required to export issues to pdf. Without that you can still export issues to html.
  
  pandoc - https://pandoc.org/ #Required to run the program
  
  JIRA API key - https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage

  On the first run program will create settings.ini file where you can input all JIRA credentials (url, username, api token) and project you want to export.

[settings.ini](docs/settings.ini):

```ini
[JIRA_ACCESS]
jira_base_url = https://your_jira_instance/  #Here you should put url from your JIRA
jira_username = your_jira@username  #JIRA username
jira_api_token = your_jira_api_token #Jira API token -> look into https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/ on how to obtain API token.

[EXPORT_OPTIONS]
export_path = EXPORT/ #Folder to export files. Relative to path executing program.
save_to_html = True #Exports html files from JIRA issues
save_to_pdf = True #Exports pdf files from JIRA issue

[ISSUE_FILTER]
jira_project = TEST #Jira project from all issues will be imported
```

After correctly setting up your data, run program and it will export issues into provided folder (EXPORT as default).

Depending on the options selected program will:
+ Always download all attachments from issues with filename changed to 'Issue-number'-'filename'
+ If save_to_html=True will generate html file for each issue with filename being 'Issue-number'
+ If save_to_pdf=True will generate pdf file for each issue with filename being 'Issue-number'


<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Issue format
For both html and pdf all issues are imported with following format
- {Issue_Number}
- {Issue_Name}
- {Issue_Description}
- {Comments}
  - {Comment_date}
  - {Comment_author}
  - {Comment_body}
- {Attachments}
  - Links to attachments locally downloaded.  

[html example](docs/TEST-5.html) of exported issue:

![image](https://github.com/lukaszmach/jira-export/assets/149838491/b41deb78-f3a7-449c-894c-c815179dd194)


[pdf example](docs/TEST-5.pdf) of exported issue:

![image](https://github.com/lukaszmach/jira-export/assets/149838491/93f28093-029f-4fc2-a3c0-5acec2e57137)



<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Limitations

Please be aware that some JIRA Api limitations may occur https://developer.atlassian.com/server/hipchat/hipchat-rest-api-rate-limits/

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Roadmap

- [x] Download attachments
- [x] Export issues to html
- [x] Export issues to pdf
- [ ] Add linked issues
- [ ] Add more flexibility into settings(image size, fields to be shown in exported issue)
- [ ] Folder Tree download (for example Epic -> User story -> Task)
- [ ] GUI/ Dynamic Exported issue format creator with custom fields

<p align="right">(<a href="#readme-top">back to top</a>)</p>


<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/łukasz-machowski-11982154

