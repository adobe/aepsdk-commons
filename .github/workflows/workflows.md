# Workflow documentation

This document covers how to use the workflows in Commons, and explains their requirements.

- [Workflow documentation](#workflow-documentation)
  - [General caller workflow tips](#general-caller-workflow-tips)
    - [Workflow booleans](#workflow-booleans)
    - [Secrets handling in reusable workflows](#secrets-handling-in-reusable-workflows)
    - [Implementing logical operations](#implementing-logical-operations)
  - [Android Maven release (android-maven-release.yml)](#android-maven-release-android-maven-releaseyml)
    - [Overview](#overview)
    - [Inputs](#inputs)
    - [Secrets required](#secrets-required)
    - [Makefile requirements](#makefile-requirements)
  - [Android Maven snapshot (android-maven-snapshot.yml)](#android-maven-snapshot-android-maven-snapshotyml)
    - [Inputs](#inputs-1)
    - [Secrets required](#secrets-required-1)
    - [Makefile requirements](#makefile-requirements-1)
  - [iOS release (ios-release.yml)](#ios-release-ios-releaseyml)
    - [Secrets required](#secrets-required-2)
    - [Makefile requirements](#makefile-requirements-2)
  - [Versions – update or validate (versions.yml)](#versions--update-or-validate-versionsyml)

## General caller workflow tips

### Workflow booleans

There is a key difference in how booleans are represented between GitHub Actions reusable workflows and manually triggered workflows:

- Reusable workflow input booleans are actual booleans and can be used directly in `if:` and other conditionals.
- Manually triggered workflow input booleans resolve to strings and require comparison with their string equivalents, `"true"` or `"false"`. Using these strings directly without comparison will result in unintended behavior, as both cases will evaluate as truthy, causing the condition to always pass.

When connecting a manually triggered workflow to a reusable workflow and passing booleans, the boolean must be evaluated in one of the following ways:

1. Use a comparison to `"true"`: `${{ github.event.inputs.update-mode == 'true' }}`
2. Use the JSON utility to evaluate the boolean: `${{ fromJSON(github.event.inputs.update-mode) }}`

### Secrets handling in reusable workflows

Currently, the reusable workflows use various implicitly required secrets which are passed to job steps in their `env:`. Callers of the reusable workflows should provide the necessary secrets using `secrets: inherit`.

### Implementing logical operations

GitHub Actions does not support true ternary operations within `${{ }}` expressions. However, logical operators such as `&&` and `||` can be used to achieve similar behavior. 

Refer to the [GitHub documentation on evaluating expressions](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/evaluate-expressions-in-workflows-and-actions#example) for examples.

## Android Maven release (android-maven-release.yml)

### Overview  
- Android repository tags follow the `v1.2.3` format, and the workflow automatically adds the `v` prefix to the provided tag value.  
- Publishing to Maven Central Repository is required when running this action.  

### Inputs  
- `release-variant`: Controls the suffix of the GitHub release title and the Maven publish command.  
  - Example:  
    - Input: `core`  
      - GitHub release title: `v3.2.1-core`  
      - Maven publish command: `make core-publish-main`  
  - Default behavior:  
    - GitHub release title: `v3.2.1`  
    - Maven publish command: `make ci-publish`  

### Secrets required  
Pass the secrets using `secrets: inherit` from the caller workflow.  

- `GITHUB_TOKEN`: Used to create a release on GitHub.  
- `GPG_SECRET_KEYS`  
- `GPG_OWNERTRUST`  
- `SONATYPE_USERNAME`  
- `SONATYPE_PASSWORD`  

### Makefile requirements  
The Makefile in the caller repository must contain the following rules:

- **Single-extension repository:**  
  - `make ci-publish`  

- **Multi-extension repository:**  
  - `make <VARIANT_NAME>-publish-main`  
    - `<VARIANT_NAME>` is passed as the workflow input: `release-variant`  
    - Example: `core-publish-main`, `signal-publish-main`  

## Android Maven snapshot (android-maven-snapshot.yml)

### Inputs  
- `release-variant`: Controls the Maven publish command.  
  - Example:  
    - Input: `core`  
      - Maven publish command: `make core-publish-snapshot`  
  - Default behavior:  
    - Maven publish command: `make ci-publish-staging`  

### Secrets required  
Pass the required secrets using `secrets: inherit` from the caller workflow.

- `GITHUB_TOKEN`: Used for creating a release on GitHub  
- `GPG_SECRET_KEYS`  
- `GPG_OWNERTRUST`  
- `SONATYPE_USERNAME`  
- `SONATYPE_PASSWORD`  

### Makefile requirements  
The Makefile in the caller repository must include the following rules:

- **Single-extension repository**:  
  - `make ci-publish-staging`  

- **Multi-extension repository**:  
  - `make <VARIANT_NAME>-publish-snapshot`  
    - `<VARIANT_NAME>` is provided as the workflow input: `release-variant`  
    - Example: `core-publish-snapshot`, `signal-publish-snapshot`  

## iOS release (ios-release.yml)

### Secrets required  
Pass the required secrets using `secrets: inherit` from the caller workflow.

- `GITHUB_TOKEN`: Used to create a release on GitHub.  
- `COCOAPODS_TRUNK_TOKEN`: Used to publish a pod to Cocoapods.  

### Makefile requirements  
The Makefile in the caller repository must include the following rules:

- `make check-version VERSION=`  
- `make test-SPM-integration`  
- `make test-podspec`  
- `make archive`  
- `make zip`  

## Versions – update or validate (versions.yml)  

The update action automatically creates a pull request (PR), which requires the following GitHub repository settings:  

1. Navigate to **Settings** -> **Code and automation** -> **Actions** -> **General**  
2. Under **Workflow permissions**, select:  
   - **Allow GitHub Actions to create and approve pull requests**
