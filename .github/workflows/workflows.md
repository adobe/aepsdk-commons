# Workflow documentation

This document covers how to use the workflows in Commons, and explains their requirements.

- [Workflow documentation](#workflow-documentation)
  - [General caller workflow tips](#general-caller-workflow-tips)
    - [Workflow booleans](#workflow-booleans)
    - [Secrets handling in reusable workflows](#secrets-handling-in-reusable-workflows)
    - [Implementing logical operations](#implementing-logical-operations)
- [General workflows](#general-workflows)
  - [Versions – update or validate (versions.yml)](#versions--update-or-validate-versionsyml)
- [Android workflows](#android-workflows)
  - [Android Maven release (android-maven-release.yml)](#android-maven-release-android-maven-releaseyml)
    - [Overview](#overview)
    - [Inputs](#inputs)
    - [Secrets required](#secrets-required)
    - [Makefile requirements](#makefile-requirements)
  - [Android Maven snapshot (android-maven-snapshot.yml)](#android-maven-snapshot-android-maven-snapshotyml)
    - [Inputs](#inputs-1)
    - [Secrets required](#secrets-required-1)
    - [Makefile requirements](#makefile-requirements-1)
- [iOS workflows](#ios-workflows)
  - [iOS release (ios-release.yml)](#ios-release-ios-releaseyml)
    - [Secrets required](#secrets-required-2)
    - [Makefile requirements](#makefile-requirements-2)
  - [iOS build and test (ios-build-and-test.yml)](#ios-build-and-test-ios-build-and-testyml)
    - [Requirements](#requirements)
    - [Secrets required](#secrets-required-3)
    - [Makefile requirements](#makefile-requirements-3)

## General caller workflow tips

### Workflow booleans

There is a key difference in how booleans are represented between GitHub Actions reusable workflows and manually triggered workflows:

- Reusable workflow input booleans are actual booleans and can be used directly in `if:` and other conditionals.
- Manually triggered workflow input booleans resolve to strings and require comparison with their string equivalents, `"true"` or `"false"`. Using these strings directly without comparison will result in unintended behavior, as both cases will evaluate as truthy, causing the condition to always pass.

When connecting a manually triggered workflow to a reusable workflow and passing booleans, the boolean must be evaluated in one of the following ways:

1. Use a comparison to `"true"`: `${{ github.event.inputs.update-mode == 'true' }}`
2. Use the JSON utility to evaluate the boolean: `${{ fromJSON(github.event.inputs.update-mode) }}`

### Secrets handling in reusable workflows

Reusable workflows rely on various implicitly required secrets, which are passed to job steps through the `env:` field. Callers must provide the required secrets by using `secrets: inherit`.

### Implementing logical operations

GitHub Actions does not support true ternary operations within `${{ }}` expressions. However, logical operators such as `&&` and `||` can be used to achieve similar behavior. 

Refer to the [GitHub documentation on evaluating expressions](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/evaluate-expressions-in-workflows-and-actions#example) for examples.

# General workflows

## Versions – update or validate (versions.yml)  

The update action automatically creates a pull request (PR), which requires the following GitHub repository settings:  

1. Navigate to **Settings** -> **Code and automation** -> **Actions** -> **General**  
2. Under **Workflow permissions**, select:  
   - **Allow GitHub Actions to create and approve pull requests**

# Android workflows

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

# iOS workflows

## iOS release (ios-release.yml)

### Secrets required  
Pass the required secrets using `secrets: inherit` from the caller workflow.

- `GITHUB_TOKEN`: Used to create a release on GitHub.  
- `COCOAPODS_TRUNK_TOKEN`: Used to publish a pod to Cocoapods.  

### Makefile requirements  
The Makefile in the caller repository must include the following rules:

- `make check-version VERSION=`  
- If `create-github-release` is `true`:
  - `make test-SPM-integration`  
    - Requires local `test-SPM.sh`
  - `make test-podspec`  
    - Requires local `test-podspec.sh`
  - `make archive`  
  - `make zip`  

The GitHub release job will look for the `.xcframework.zip` files using the pattern:
`./build/${DEP}.xcframework.zip#${DEP}-${DEP_VERSION}.xcframework.zip"`

## iOS build and test (ios-build-and-test.yml)

### Requirements
In order for Xcode code coverage to be uploaded by Codecov, Makefile test rules run using this workflow **must not** override the default location using the `-resultBundlePath` flag (ex: `-resultBundlePath build/reports/iosUnitResults.xcresult`).

The default base path that the Codecov action will look for test results on the GitHub Action runner is:
`/Users/runner/Library/Developer/Xcode/DerivedData`

### Secrets required
Pass the required secrets using `secrets: inherit` from the caller workflow.

- `CODECOV_TOKEN`: Used by Codecov to upload code coverage reports.  

### Makefile requirements  
The Makefile in the caller repository must include the following rules:

- `make lint`
- When `run-test-ios-unit` is `true`:
  - `make unit-test-ios`  
- When `run-test-ios-functional` is `true`:
  - `make functional-test-ios`  
- When `run-test-ios-integration` is `true`:
  - `make test-integration-upstream`  
- When `run-test-tvos-unit` is `true`:
  - `make unit-test-tvos`
- When `run-test-tvos-functional` is `true`:
  - `make functional-test-tvos`
- When `run-test-tvos-integration` is `true`:
  - `make integration-test-tvos`
- When `run-build-xcframework-and-app` is `true`:
  - `make archive`
  - `make build-app`

For device and OS matrix to work, the Makefile must support four new input properties:
- `IOS_DEVICE_NAME`
- `IOS_VERSION`
- `TVOS_DEVICE_NAME`
- `TVOS_VERSION`

```makefile
# At the top level of the Makefile:
# Values with defaults
IOS_DEVICE_NAME ?= iPhone 15
# If OS version is not specified, uses the first device name match in the list of available simulators
IOS_VERSION ?= 
ifeq ($(strip $(IOS_VERSION)),)
    IOS_DESTINATION = "platform=iOS Simulator,name=$(IOS_DEVICE_NAME)"
else
    IOS_DESTINATION = "platform=iOS Simulator,name=$(IOS_DEVICE_NAME),OS=$(IOS_VERSION)"
endif

TVOS_DEVICE_NAME ?= Apple TV
# If OS version is not specified, uses the first device name match in the list of available simulators
TVOS_VERSION ?=
ifeq ($(strip $(TVOS_VERSION)),)
	TVOS_DESTINATION = "platform=tvOS Simulator,name=$(TVOS_DEVICE_NAME)"
else
	TVOS_DESTINATION = "platform=tvOS Simulator,name=$(TVOS_DEVICE_NAME),OS=$(TVOS_VERSION)"
endif

...

# Usage example - update the `-destination` flag to use the new computed property `IOS_DESTINATION`:
xcodebuild test -workspace $(PROJECT_NAME).xcworkspace -scheme "UnitTests" -destination $(IOS_DESTINATION) -enableCodeCoverage YES ADB_SKIP_LINT=YES

```