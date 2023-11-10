<a name="readme-top"></a>

[![LinkedIn][linkedin-shield]][linkedin-url]

# Jira export

Small program for exporting issues from Jira to pdf or html


## Prerequisites

  wkhtmltopdf - https://wkhtmltopdf.org/
  
  pandoc - https://pandoc.org/
  
  JIRA API key - https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/

<p align="right">(<a href="#readme-top">back to top</a>)</p>

## Usage

  On the first run program will create settings.ini file where you can input all JIRA credentials (url, username, api token) and project you want to export.

  After correctly setting up your data, run program and it will export issues into provided folder (EXPORT as default).

  Please be aware that some JIRA Api limitations may occur https://developer.atlassian.com/server/hipchat/hipchat-rest-api-rate-limits/



<p align="right">(<a href="#readme-top">back to top</a>)</p>

<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[linkedin-shield]: https://img.shields.io/badge/-LinkedIn-black.svg?style=for-the-badge&logo=linkedin&colorB=555
[linkedin-url]: https://linkedin.com/in/łukasz-machowski-11982154

