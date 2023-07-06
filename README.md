# Git Metrics
Git Metrics is a tool that helps in gathering code volume and quality metrics from multiple Git repositories. It comes as a Docker container that can be easily deployed and run in any environment. The tool collects data from given Git repositories and generates a report that shows a set of code quality and volume metrics.

Git Metrics should support (not tested so far!) every type of publicly available / self-hosted Git repository storage as well as locally cloned git repositories on the filesystem.

## Supported metrics
Metrics, collected by Git Metrics, include:

### Code volume
| Name | Description |
| --- | --- |
| Total lines | Total number of lines in the analyzed repositores' files |
| Lines of Code | Lines of code in the analyzed repositores' files |
| Number of files | Total number of files in the analyzed repositories |
| Languages in use | Programming languages, present in the analyzed repositories |

### Code quality
| Name | Description |
| --- | --- |
| Code churn | The rate of change of code over the last year, measured by the number of code modifications, additions, and deletions |
| Maintainability index | A metric that measures how maintainable code is over time; considers factors such as code complexity, code volume, and code documentation |
| Cyclomatic complexity |  A measure of the complexity of code by counting the number of independent paths through the code |
| Halstead metrics | A set of metrics that measure the complexity and readability of code based on the number of operators, operands, and unique operators and operands |

Code quality metrics' collection is based on the open-source [multimetric](https://github.com/priv-kweihmann/multimetric) toolkit by [priv-kweihmann](https://github.com/priv-kweihmann)

**Important**: Git Metrics will take "overall" values of code quality metrics for a given repository, returned by `multimetric`. If run on multiple repositories at once, as well as repositories that contain large amount of text data, the tool may produce invalid data, influenced by outlying metric values.


# Setup
Clone Git Metrics repository and build the Docker container
```
git clone https://github.com/Octal-Security/scoping-git-metrics
cd scoping-git-metrics
docker build -t gitmetrics:latest .
```

# Usage
## Running gitmetrics on local repositories

![filesystem_demo](https://github.com/Octal-Security/scoping-git-metrics/blob/main/filesystem_demo.gif)

0. Make sure that you are in the same directory where your local git repositories are located:
```
$ ls -l
total 24
drwxr-xr-x  16 user  staff    512 Jul  6 14:50 amass/      <--- local repos we will be scanning
drwxr-xr-x  16 user  staff    512 Jul  6 14:50 httpx/
drwxr-xr-x  16 user  staff    512 Jul  6 14:50 uncover/
...
```

<details>
<summary> <h3>Running Git Metrics on a single Git repository</h3> </summary>

1. Run the docker container. Mount the current directory that holds the repository folder to the container, and specify the **absolute path** of the repository folder inside the Docker container, and full JSON report filename:
```
$ docker run --rm -it -v $PWD:/pwd/ gitmetrics:latest filesystem -r /pwd/{REPOSITORY_FOLDER} -o /pwd/{DETAILED_OUTPUT_FILENAME}
```

</details>

<details>
<summary> <h3>Running Git Metrics on multiple Git repositories</h3> </summary>

1. Place **absolute filepaths** of the repositories inside the Docker container that need to be scanned into a file:
    ```
    $ cat <<EOF > {FILE_WITH_REPOS_LINKS}
    /pwd/uncover
    /pwd/amass
    /pwd/httpx
    /pwd/dnsx
    EOF
    ```
2. Run the docker container. Supply your Git credentials, mount the repositories, and file with the repository links into the docker container. Specify the output filename for the full JSON report:
    ```
    $ docker run --rm -it -v $PWD:/pwd/ gitmetrics:latest filesystem -f /pwd/{FILE_WITH_REPOS_LINKS} -o /pwd/{DETAILED_OUTPUT_FILENAME}
    ```

</details>

<br>
<br>
<br>

## Running gitmetrics on the remote repositories
![remote_demo](https://github.com/Octal-Security/scoping-git-metrics/blob/main/remote_demo.gif)

### Generating remote access credentials
In order to use Git Metrics with private repositories, one must supply a set of Git credentials (`--git-username`, `--git-password`) with read-only permissions for the target repositories.

**Important**: Git SSH authentication is not yet implemented. You can create a set of credentials for Git Metrics either by generating API tokens for all of the popular Git storages using the guides below, or trying a password-based authentication, if your Git storage supports it. 

If you encounter any AuthN/AuthZ issues when running the Git Metrics with your Git storage, feel free to open an issue!
<br>
<b>Github</b>
[How to generate an access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token#about-personal-access-tokens)
<br>
Required permissions:
- For classic access tokens: 
   1. [`repo`](https://docs.github.com/en/apps/oauth-apps/building-oauth-apps/scopes-for-oauth-apps#available-scopes)
   
- For fine-grained access tokens:
   1. [Repository access](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token#creating-a-fine-grained-personal-access-token): `All repositories`
   2. [Repository permissions](https://docs.github.com/en/rest/overview/permissions-required-for-fine-grained-personal-access-tokens?apiVersion=2022-11-28#contents): `Contents:Read-only`


<b>Gitlab</b>
[How to generate an access token](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#prefill-personal-access-token-name-and-scopes)
<br>
Required permission scopes:
   1. [`read_repository`](https://docs.gitlab.com/ee/user/profile/personal_access_tokens.html#personal-access-token-scopes)
   
<b>BitBucket</b>
[How to generate an access token](https://confluence.atlassian.com/bitbucketserver/personal-access-tokens-939515499.html)
<br>
Required permission scopes: 
   1. [Project read](https://confluence.atlassian.com/bitbucketserver/personal-access-tokens-939515499.html#HTTPaccesstokens-permissions)
   2. [Repository Read](https://confluence.atlassian.com/bitbucketserver/personal-access-tokens-939515499.html#HTTPaccesstokens-permissions)


## Usage
1. Create a set of access credentials using the guide above.

<details>
<summary> <h3>Running Git Metrics on a single Git repository</h3> </summary>

2. Run the docker container. Supply your Git credentials, and a repository clone link. Mount the current directory to the container, and specify the output filename for the full JSON report.
```
$ docker run --rm -it -v $PWD:/pwd/ gitmetrics:latest remote --git-username {YOUR_GIT_USERNAME} --git-password {YOUR_GIT_API_TOKEN_OR_PASS} -r {REPO_LINK} -o /pwd/{DETAILED_OUTPUT_FILENAME}
```

</details>

<details>
<summary> <h3>Running Git Metrics on multiple Git repositories</h3> </summary>

2. Place HTTP clone links to your repositories that need to be scanned into a file:
    ```
    $ cat <<EOF > {FILE_WITH_REPOS_LINKS}
    https://github.com/projectdiscovery/uncover
    https://github.com/owasp-amass/amass
    https://github.com/projectdiscovery/httpx
    https://github.com/projectdiscovery/dnsx
    EOF
    ```
3. Run the docker container. Supply your Git credentials, mount the file with the repository links into the docker container, and specify the output filename for the full JSON report.
    ```
    $ docker run --rm -it -v $PWD:/pwd/ gitmetrics:latest remote --git-username {YOUR_GIT_USERNAME} --git-password {YOUR_GIT_API_TOKEN_OR_PASS} -f /pwd/{FILE_WITH_REPOS_LINKS} -o /pwd/{DETAILED_OUTPUT_FILENAME}
    ```

</details>


# Viewing the results 
Condensed report can be seen in the console window. Detailed JSON report is available in the `$PWD/{DETAILED_OUTPUT_FILENAME}` file
