#!/usr/bin/env python3

#
# Copyright 2024 Adobe. All rights reserved.
# This file is licensed to you under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy
# of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
# OF ANY KIND, either express or implied. See the License for the specific language
# governing permissions and limitations under the License.
#

# Requires Python 3.10+

import argparse
import os
import re
import subprocess
import sys

from argparse import Namespace
from dataclasses import dataclass
from dataclasses import replace
from enum import Enum
from string import Template
from typing import Callable

class AnnotationType(Enum):
    ERROR = "error"
    WARNING = "warning"
    NOTICE = "notice"
    DEBUG = "debug"

def print_annotation(annotation_type: AnnotationType, title: str | None = None, message: str | None = None):
    annotation = f"::{annotation_type.value} file=versions.py"
    if title:
        annotation += f",title={title}"
    if message:
        annotation += f"::{message}"
    else:
        annotation += "::"

    print(annotation)

def log_error(title: str | None = None, message: str | None = None):
    print_annotation(AnnotationType.ERROR, title, message)

def log_warning(title: str | None = None, message: str | None = None):
    print_annotation(AnnotationType.WARNING, title, message)

def log_notice(title: str | None = None, message: str | None = None):
    print_annotation(AnnotationType.NOTICE, title, message)

def log_debug(title: str | None = None, message: str | None = None):
    print_annotation(AnnotationType.DEBUG, title, message)

def error_exit(title: str | None = None, message: str | None = None):
    """
    Prints an error message and exits the script with a status code of 1.

    Parameters:
        message (str): 
            The error message to display before exiting the script.

    Returns:
        None
    """
    log_error(title, message)
    sys.exit(1)

DIVIDER_STRING = "=" * 80
VERSION_REGEX = r"[0-9]+\.[0-9]+\.[0-9]+"
TEST_VERSION_REGEX = r"[1-9]+\.[0-9]+\.[0-9]+"
REST_OF_LINE_REGEX = r".*$"

@dataclass(frozen=True) # Make the class immutable for hashability
class RegexPattern:
    """
    A data class representing a regex pattern used to match version-related strings in files.

    Attributes:
        pattern (str): 
            The regex pattern as a string, used to identify specific version strings within a file.

        description (str): 
            A human-readable description of what the pattern matches.
        
        version (str): 
            The version to use, following semantic versioning (ex: '3.1.1').

    Methods:
        __iter__() -> Iterator[tuple[str, str]]:
            Allows the `RegexPattern` object to be iterable, yielding a tuple containing the 
            pattern and its description.
    """
    description: str
    pattern: str
    version: str | None = None
    # Allows overriding the version regex to be used for the pattern
    version_pattern: str | None = None

    def __iter__(self):
        return iter((self.pattern, self.version, self.description))

@dataclass(frozen=True)
class RegexTemplate:
    """
    A class that represents either a static regex pattern or a dynamic regex template.

    Attributes:
        description (str):
            A human-readable description of what the pattern matches.

        pattern_template (str | Callable[[str], str]):
            A regex pattern string (static) or a callable function that generates a pattern dynamically.

        version (str | None):
            The version to use, following semantic versioning (e.g., '3.1.1').

        version_pattern (str | None):
            Allows overriding the version regex used for the pattern.
    """

    description: str
    pattern_template: str | Callable[[str], str]
    version: str | None = None
    version_pattern: str | None = None

    def generate_pattern(self, dependency_name: str | None = None) -> str:
        """
        Generates or retrieves the regex pattern.

        Returns:
            str: The final regex pattern.

        Raises:
            ValueError: If `pattern_template` is a callable function but no `dependency_name` is provided.
        """
        if isinstance(self.pattern_template, str):
            return self.pattern_template  # Static pattern case

        # If dependency_name is None or ""
        if not dependency_name:
            error_exit(title="Name required", message=f"Name is required for dynamic pattern generation in '{self.description}'.")
        
        return self.pattern_template(dependency_name)  # Generated pattern case

    def __iter__(self):
        """
        Allows the object to be iterable, yielding a tuple containing the pattern, version, and description.
        """
        return iter((self.pattern_template, self.version, self.description))


def get_root_dir():
    """
    Retrieves the root directory of the current Git repository by running a Git command. 
    If the current directory is not part of a Git repository or if the command fails, 
    the function prints an error message and exits the script.

    Returns:
        str: 
            The absolute path to the root directory of the Git repository.

    Raises:
        SystemExit: 
            If the command fails, indicating that the current directory is not part 
            of a Git repository or the root directory cannot be determined.

    Example:
        Output:
            "/path/to/repository/root"
    """
    try:
        root_dir = subprocess.check_output(["git", "rev-parse", "--show-toplevel"]).decode().strip()
        return root_dir
    except subprocess.CalledProcessError:
        error_exit(title="Git repository not found", message="Not a git repository or unable to determine root directory.")

def lowercase_first_char(s: str) -> str:
    return s[:1].lower() + s[1:] if s else s

def get_ios_repo_name(name: str) -> str:
    """
    Generates the GitHub repository URL for the specified iOS dependency based on its name.
    If the dependency is one of the Core dependencies, the Core repo URL is returned.

    Parameters:
        name (str): 
            A string representing the name of the iOS dependency. Expected to follow the naming 
            convention "AEP<DependencyName>".

    Returns:
        str: 
            The GitHub repository URL for the specified iOS dependency.

    Example:
        Input:
            name = 'AEPEdgeIdentity'

        Output:
            "https://github.com/adobe/aepsdk-edgeidentity-ios.git"
    """
    
    core_dependencies = {'AEPCore', 'AEPIdentity', 'AEPLifecycle', 'AEPServices', 'AEPSignal'}
    if name in core_dependencies:
        return 'https://github.com/adobe/aepsdk-core-ios.git'
    else:
        if name.startswith('AEP'):
            repo_name = name[3:].lower()
            return f'https://github.com/adobe/aepsdk-{repo_name}-ios.git'
        else:
            error_exit(title="Unknown dependency", message=f"Unknown dependency name '{name}'. Cannot construct iOS repo URL. Please use format 'AEP<DependencyName>' (ex: 'AEPCore').")

def gradle_properties_template(name: str) -> str:
    """
    Generates a regex pattern for matching a dependency version declaration within a Gradle properties file.

    Parameters:
        name (str): 
            A string representing the name of the dependency.

    Returns:
        str: 
            A regex pattern as a string.

    Example:
        Input:
            name = 'Core'

        Output:
            "^[\\s\\S]*mavenCoreVersion\\s*=\\s*"
    """
    template = Template(r'^[\s\S]*maven${dependency_name}Version\s*=\s*')
    escaped_name = re.escape(name)
    return template.substitute(dependency_name=escaped_name)

def gradle_properties_core_template(name: str) -> str:
    """
    Generates a regex pattern for matching a dependency version declaration within a Gradle properties file in the Core repo.

    Parameters:
        name (str): 
            A string representing the name of the dependency.

    Returns:
        str: 
            A regex pattern as a string.

    Example:
        Input:
            name = 'AEPCore'

        Output:
            '^[\s\S]*coreExtensionVersion\s*=\s*'
    """
    template = Template(r'^[\s\S]*${dependency_name}ExtensionVersion\s*=\s*')
    gradle_dependency_name = lowercase_first_char(name)
    escaped_name = re.escape(gradle_dependency_name)
    return template.substitute(dependency_name=escaped_name)

def swift_spm_template(name: str) -> str:
    """
    Generates a regex pattern for matching a Swift Package Manager dependency declaration using `.upToNextMajor(from:)`.

    Parameters:
        name (str): 
            A string representing the name of the dependency.

    Returns:
        str: 
            A regex pattern as a string.

    Example:
        Input:
            name = 'AEPCore'

        Output:
            "^[\\s\\S]*\\.package\\(\\s*url:\\s*\"https://github.com/adobe/aepsdk-core-ios.git\"\\s*,\\s*\\.upToNextMajor\\(\\s*from:\\s*\""
    """
    template = Template(r'^[\s\S]*\.package\(\s*url:\s*"${dependency_url}"\s*,\s*\.upToNextMajor\(\s*from:\s*"')
    ios_dependency_repo = get_ios_repo_name(name)
    escaped_name = re.escape(ios_dependency_repo)
    return template.substitute(dependency_url=escaped_name)

def podspec_template(name: str) -> str:
    """
    Generates a regex pattern for matching a dependency declaration within a CocoaPods podspec file
    using `s.dependency` and `'>='` operator.

    Parameters:
        name (str): 
            A string representing the name of the dependency.

    Returns:
        str: 
            A regex pattern as a string.

    Example:
        Input:
            name = 'AEPCore'

        Output:
            "^[\\s\\S]*s\\.dependency\\s*['\"]AEPCore['\"]\\s*,\\s*['\"]>=\\s*"
    """
    # Triple quote used to avoid escaping single quotes in the template
    template = Template(r'''^[\s\S]*s\.dependency\s*["']${dependency_name}["']\s*,\s*["']>=\s*''')
    escaped_name = re.escape(name)
    return template.substitute(dependency_name=escaped_name)

def yml_uses_template(name: str) -> str:
    """
    Generates a regex pattern to match a dependency declaration in a YAML file with the 'uses:' syntax 
    in GitHub Actions workflows.

    The pattern matches the dependency name followed by the `@` symbol. The name does not need to be
    escaped for regex syntax, as this is handled automatically.

    Parameters:
        name (str): 
            A string representing the name of the dependency.

    Returns:
        str: 
            A regex pattern as a string.

    Example:
        Input:
            name = 'actions\/checkout'

        Output:
            "^[\\s\\S]*uses:\\s*actions\/checkout@"
    """
    template = Template(r'''^[\s\S]*uses:\s*${dependency_name}@''')
    escaped_name = re.escape(name)
    return template.substitute(dependency_name=escaped_name)

ROOT_DIR = get_root_dir()

EXTENSION_REGEX_PATTERNS: dict[str, list[RegexPattern]] = {
    # Android project regex patterns
    '.properties': [
        RegexTemplate(
            description='moduleVersion',
            pattern_template=r'^[\s\S]*moduleVersion\s*=\s*',
        ),
    ],
    # Use with gradle.properties in the Core repo
    # Special format for Android Core repo extension versions
    'properties_multi_module': [
        RegexTemplate(
            description='<library>ExtensionVersion (ex: coreExtensionVersion)',
            pattern_template=gradle_properties_core_template,
        )
    ],
    '.java': [
        RegexTemplate(
            description='EXTENSION_VERSION',
            pattern_template=r'^[\s\S]*String EXTENSION_VERSION\s*=\s*"',
        )
    ],
    '.kt': [
        RegexTemplate(
            description='VERSION',
            pattern_template=r'^[\s\S]*const val VERSION\s*=\s*"',
        )
    ],
    # iOS project regex patterns
    '.pbxproj': [
        RegexTemplate(
            description='MARKETING_VERSION',
            pattern_template=r'^[\s\S]*MARKETING_VERSION = ',
        )
    ],
    '.podspec': [
        RegexTemplate(
            description='s.version',
            pattern_template=r'^[\s\S]*s\.version\s*=\s*"',
        )
    ],
    '.swift': [
        RegexTemplate(
            description='EXTENSION_VERSION',
            pattern_template=r'^[\s\S]*static let EXTENSION_VERSION\s*=\s*"',
        )
    ],
    # For Swift files that use VERSION_NUMBER instead of EXTENSION_VERSION
    # Ex: EventHubConstants.swift
    'swift_version_number': [
        RegexTemplate(
            description='VERSION_NUMBER',
            pattern_template=r'^[\s\S]*static let VERSION_NUMBER\s*=\s*"',
        )
    ],
    # For Swift test files that define version in JSON
    # This also uses the TEST_VERSION_REGEX instead of the VERSION_REGEX
    # Ex: MobileCoreTests.swift
    'swift_test_version': [
        RegexTemplate(
            description='version',
            pattern_template=r'^[\s\S]*\"version\"\s*:\s*"',
            version_pattern=TEST_VERSION_REGEX
        )
    ],
}
"""
A dictionary mapping file extensions and pattern types to a list of `RegexTemplate`s used for the primary extension. 
The regex patterns aim to be permissive with whitespace to avoid blocking different formatting styles and access levels.

Key:
    - File extension or pattern type as a string (e.g., '.properties', 'swift_test_version').

Value:
    - A list of RegexPattern objects
"""

DEPENDENCY_REGEX_PATTERNS: dict[str, list[RegexTemplate]] = {
    # Android project regex patterns
    '.properties': [
        RegexTemplate(
            description='maven<dependencyName>Version (ex: mavenCoreVersion)',
            pattern_template=gradle_properties_template,
        )
    ],
    # Use with gradle.properties in the Core repo
    # Special format for Android Core repo extension versions
    'properties_multi_module': [
        RegexTemplate(
            description='<library>ExtensionVersion (ex: coreExtensionVersion)',
            pattern_template=gradle_properties_core_template,
        )
    ],
    # iOS project regex patterns
    'swift_spm': [
        RegexTemplate(
            description='.upToNextMajor(from:)',
            pattern_template=swift_spm_template,
        )
    ],
    '.podspec': [
        RegexTemplate(
            description='s.dependency',
            pattern_template=podspec_template,
        )
    ],
    # General regex patterns
    # Use with YAML files, particularly GitHub Actions workflow actions
    'yml_uses': [
        RegexTemplate(
            description='uses:',
            pattern_template=yml_uses_template,
            version_pattern=REST_OF_LINE_REGEX
        )
    ]
}
"""
A dictionary mapping file extensions and pattern types to a list of `RegexTemplate`s used for dependencies. 
The regex patterns aim to be permissive with whitespace to avoid blocking different formatting styles and access levels.

Key:
    - File extension or pattern type as a string (e.g., '.properties', 'swift_spm').

Value:
    - A list of RegexTemplate objects.
"""

def parse_arguments() -> Namespace:
    """
    Parses the command-line arguments for the script, providing options for version updates, dependencies, 
    paths, and the update mode. This function uses argparse to handle and validate the provided input.

    Returns:
        Namespace: An argparse.Namespace object containing the parsed arguments as attributes.

    Command-line Arguments:
        -v, --version (str): 
            The version to update or validate for the extension. 
            Example: 3.0.2. This argument is required.
        
        -d, --dependencies (str, optional): 
            A comma-separated list of dependencies with their versions. Each dependency can 
            optionally specify the semicolon-separated list of file or directory paths and associated pattern type where it 
            applies using the `@` symbol.
            - Syntax: 
                `<name> <version>[@file_path1[:pattern_type][;file_path2[:pattern_type];...]]`
            - If the `@` syntax is used, the paths provided in the `-p` argument will be overridden, and the dependency will only be applied to the specified files.
            - When specifying custom paths, you may provide either an absolute or relative path to each file.
            - If a dependency is missing a version, it will be skipped.
            - `<name>` does not have to be regex-escaped, this is handled automatically.
            Example: 
                iOS: `"AEPCore 3.1.1, AEPServices 8.9.10@AEPCore.podspec;Package.swift:swift_spm"`
                Android: `"AEPCore 7.8.9, AEPEdgeIdentity 8.9.10@code/gradle.properties;code/Constants.kt"`

        -p, --paths (str): 
            Comma-separated list of file or directory paths, either absolute or relative to the project root, to update or validate.
            Each path can optionally specify a pattern type using the syntax:
                `path[:pattern_type]`
            - Example: 
                `"Package.swift:swift_spm, AEPCore/Sources/configuration/ConfigurationConstants.swift, AEPCore/Tests/MobileCoreTests.swift:swift_test_version"`
                `"code/edge/src/main/java/com/adobe/marketing/mobile/EdgeConstants.java, code/gradle.properties"`
            This argument is required.

        -u, --update (flag): 
            If provided, the script will update the versions in the specified files. 
            If omitted, the script will validate the existing versions instead.

        -n, --name (str, optional): 
            Specifies the extension name. This is required if any regex patterns reference a template that depends on the extension name.
            - Some regex patterns may use the extension name as part of their matching criteria.
            - If the script encounters a regex pattern that requires the extension name but this argument is missing, it will exit with an error code.
            Example: `"Core"`

    Example Usage:
        iOS: 
        --update \ # Remove this flag if you want to validate the versions instead
        -v 6.7.8 \
        -p "Package.swift:swift_spm, AEPCore/Tests/MobileCoreTests.swift:swift_test_version, AEPCore/Sources/eventhub/EventHubConstants.swift:swift_version_number, AEPCore/Sources/configuration/ConfigurationConstants.swift, AEPCore.podspec, AEPCore.xcodeproj/project.pbxproj" \
        -d "AEPRulesEngine 7.8.9, AEPServices 8.9.10@AEPCore.podspec"

        Android:
        --update \ # Remove this flag if you want to validate the versions instead
        -v 6.7.8 \
        -p "code/edge/src/main/java/com/adobe/marketing/mobile/EdgeConstants.java, code/gradle.properties" \
        -d "AEPCore 7.8.9, AEPEdgeIdentity 8.9.10@code/gradle.properties"
        
        Example Explanation:
            - `Package.swift` will use the `swift_spm` regex patterns.
            - `MobileCoreTests.swift` will use the `swift_test_version` patterns.
            - `EventHubConstants.swift` will use the `swift_version_number` patterns.
            - `ConfigurationConstants.swift` will use the default patterns for `.swift` files.
            - `AEPCore.podspec` will use the regex patterns for `.podspec` files.
            - `project.pbxproj` will use the regex patterns for `.pbxproj` files.
            - The `AEPRulesEngine` dependency will be applied to all relevant files.
            - The `AEPServices` dependency will only be applied to the `AEPCore.podspec` file.
    """
    parser = argparse.ArgumentParser(
        description='Update or validate versions in project files.'
    )

    parser.add_argument(
        '-v', '--version',
        required=True,
        help='Version to update or validate for the extension. Example: 3.0.2'
    )
    parser.add_argument(
        '-d', '--dependencies',
        help='Comma-separated dependencies to update along with their version. Example: "Core 3.1.1, Edge 3.2.1"'
    )
    parser.add_argument(
        '-p', '--paths',
        help='Comma-separated list of file or directory paths, either absolute or relative to the project root, to update or validate.'
    )
    parser.add_argument(
        '-u', '--update',
        action='store_true',
        help='Updates the version. If this flag is absent, the script instead verifies if the version is correct.'
    )
    parser.add_argument(
        '-n', '--name',
        help='Specifies the extension name. Required if any regex patterns use a template that depends on the extension name. Example: "Core".'
    )

    args: Namespace = parser.parse_args()
    return args

def convert_to_absolute_path(file_path: str) -> str:
    # Convert relative paths to absolute by appending them to the root directory
    if not file_path.startswith('/'):
        file_path = os.path.join(ROOT_DIR, file_path)
    return file_path

def expand_paths(paths: list[str]) -> list[tuple[str, str | None]]:
    """
    Expands the provided paths into a list of absolute file paths with their associated pattern types.
    If a path is a directory, it includes all files within that directory (non-recursive).
    If a pattern type is specified, it is associated with each file within the directory or the file itself.

    Parameters:
        paths (list[str]):
            A list of paths (files or directories) with optional pattern types specified after a colon.

    Returns:
        list[tuple[str, Optional[str]]]:
            A list of tuples where each tuple contains an absolute file path and its associated pattern type.

    Raises:
        SystemExit:
            If a path does not exist or is neither a file nor a directory.
    """
    expanded_paths = []
    for path in paths:
        cleaned_path, pattern_type = path.split(':', 1) if ':' in path else (path, None)
        absolute_path = convert_to_absolute_path(cleaned_path)

        if os.path.isdir(absolute_path):
            # It's a directory; include all files within (non-recursive)
            try:
                for entry in os.scandir(absolute_path):
                    if entry.is_file():
                        file_path = entry.path
                        expanded_paths.append((file_path, pattern_type))
            except Exception as e:
                error_exit(title="Error reading directory", message=str(e))
        elif os.path.isfile(absolute_path):
            # It's a file
            expanded_paths.append((absolute_path, pattern_type))
        else:
            error_exit(
                title="Path not found",
                message=f"Path '{absolute_path}' does not exist or is not a file or directory."
            )
    return expanded_paths

def generate_extension_patterns(paths: list[str], version: str, name: str | None) -> dict[str, list[RegexPattern]]:
    """
    Generates regex patterns for the extension using a list of file paths, associating each pattern with the specified 
    version. Each path can optionally specify a pattern type by appending it after a colon (`:`). 
    If no type is specified, a default pattern based on the file's extension is applied. Uses patterns from `EXTENSION_REGEX_PATTERNS`.

    Parameters:
        paths (list[str]): 
            A list of file paths as strings.

        version (str): 
            The version string to use with each regex pattern.

        name (str | None):
            The name of the extension. Required if any regex patterns use a template that depends on the extension name.

    Returns:
        dict[str, list[RegexPattern]]: 
            A dictionary where each key is an absolute file path and each value is a list of `RegexPattern` 
            objects. Each `RegexPattern` in the list matches the specified version for the given path and type.

    Raises:
        SystemExit: 
            If a file path does not exist or is not a valid file, the function will call `error_exit` 
            with an appropriate message, causing the program to exit.

    Example:
        Input:
            paths = ["src/Package.swift:swift_spm", "src/Utils.swift", "src/Test.swift:swift_test_version"]
            version = "1.2.3"
        
        Output:
            {
                "/root/src/Package.swift": [RegexPattern(...), ...],
                "/root/src/Utils.swift": [RegexPattern(...), ...],
                "/root/src/Test.swift": [RegexPattern(...), ...]
            }
    """
    
    paths_to_patterns: dict[str, list[RegexPattern]] = {}
    expanded_paths = expand_paths(paths)

    for file_path, pattern_type in expanded_paths:
        if pattern_type:
            matching_templates = EXTENSION_REGEX_PATTERNS.get(pattern_type, [])
        else:
            file_extension = os.path.splitext(file_path)[1]
            matching_templates = EXTENSION_REGEX_PATTERNS.get(file_extension, [])
        for template in matching_templates:
            pattern = template.generate_pattern(name)
            regex_pattern = RegexPattern(
                description=template.description,
                pattern=pattern,
                version=version,
                version_pattern=template.version_pattern
            )
            paths_to_patterns.setdefault(file_path, []).append(regex_pattern)

    return paths_to_patterns

def generate_dependency_patterns(base_paths: list[str], dependencies_str: str) -> dict[str, list[RegexPattern]]:
    """
    Generates regex patterns for specified dependencies, mapping each dependency and version to specified 
    or default file paths. Each dependency can optionally specify path(s) and a pattern type for each path.
    Paths can specify a pattern type by appending it after a colon (`:`). If no type is specified, 
    a default pattern based on the file's extension is applied. Uses patterns from `DEPENDENCY_REGEX_PATTERNS`.

    Parameters:
        base_paths (list[str]): 
            A list of default file paths to apply if a dependency does not specify paths.

        dependencies_str (str): 
            A comma-separated string of dependencies with their versions and optional paths and pattern type.

    Returns:
        dict[str, list[RegexPattern]]: 
            A dictionary where each key is an absolute file path and each value is a list of `RegexPattern` 
            objects.

    Raises:
        SystemExit: 
            If a file path does not exist or is not a valid file, the function will call `error_exit` 
            with an appropriate message, causing the program to exit.

    Example:
        Input:
            base_paths = ["src/Default.swift"]
            dependencies_str = "adobe/aepsdk-commons 1.2.3@src/Package.swift:swift_spm, adobe/aepsdk-core 1.1.1"

        Output:
            {
                "/root/src/Package.swift": [RegexPattern(...), ...],
                "/root/src/Default.swift": [RegexPattern(...), ...]
            }
    """
    paths_to_patterns: dict[str, list[RegexPattern]] = {}
    # Break into individual dependencies, removing empty string paths
    if dependencies_str:
        dependencies_input: list[str] = [
            dep.strip() 
            for dep in dependencies_str.split(',') 
            if dep.strip()
        ]
    else:
        dependencies_input = []

    for dependency in dependencies_input:
        dependency_parts = dependency.strip().split('@')
        base_parts = dependency_parts[0].split()
        if len(base_parts) != 2:
            log_notice(title=f"Skipping dependency '{dependency}'", message=f"The dependency '{dependency}' did not specify a version. Skipping...")
            continue

        dependency_name, dependency_version = base_parts

        paths = dependency_parts[1].split(';') if len(dependency_parts) > 1 else base_paths
        expanded_paths = expand_paths(paths)

        for file_path, pattern_type in expanded_paths:
            if pattern_type:
                matching_templates = DEPENDENCY_REGEX_PATTERNS.get(pattern_type, [])
            else:
                file_extension = os.path.splitext(file_path)[1]
                matching_templates = DEPENDENCY_REGEX_PATTERNS.get(file_extension, [])
            for template in matching_templates:
                pattern = template.generate_pattern(dependency_name)
                regex_pattern = RegexPattern(
                    description=template.description,
                    pattern=pattern,
                    version=dependency_version,
                    version_pattern=template.version_pattern
                )
                paths_to_patterns.setdefault(file_path, []).append(regex_pattern)

    return paths_to_patterns

def process_file_version(path: str, patterns: list[RegexPattern], is_update_mode: bool) -> bool | None:
    """
    Processes a single file to either update or validate version strings based on provided regex patterns.

    In **update mode**, the function replaces matching version strings with the new versions specified in the `RegexPattern` objects.
    In **validate mode**, it checks whether the existing versions in the file match the expected versions from the `RegexPattern` objects.

    Parameters:
        path (str):
            The file system absolute path to the file that needs to be processed.
        patterns (list[RegexPattern]):
            A list of `RegexPattern` instances.
        is_update_mode (bool): 
            If True, the function updates the version in the file. If False, the function verifies 
            that the versions are correct.

    Returns:
        bool | None: 
            - In **validate mode**, returns True if all versions match the expected value, otherwise False.
            - In **update mode**, returns None after updating the file content.

    Raises:
        FileNotFoundError: 
            If the specified file path does not exist or cannot be read.
        IOError: 
            If there is an issue reading or writing to the file.
    """
    
    file_name = os.path.basename(path)

    print(f"---- {'Updating' if is_update_mode else 'Validating'} versions in '{file_name}' ----")
    print(f"  * File path: {path}")
    
    # Read the file content
    with open(path, 'r') as file:
        content = file.readlines()

    matched_patterns = []  # List to keep track of patterns that have matched

    # Apply the update or validate logic to each line
    new_content = []
    for line in content:
        replaced_line = line
        for regex_pattern in patterns:
            pattern = regex_pattern.pattern
            description = regex_pattern.description
            version = regex_pattern.version
            version_pattern = regex_pattern.version_pattern or VERSION_REGEX

            # Compile regex with two capture groups: the pattern and the version
            # Notice the two parentheses added around the pattern and version regex
            pattern = re.compile(f"({pattern})({version_pattern})")
            match = pattern.match(line)
            if match:
                if is_update_mode:
                    # Use a named capture group to avoid incorrectly merging the group and version.
                    # Example without named capture group: (capture group) \\1 and (version) 6.7.8 -> \\16.7.8 (interpreted as capture group 16)
                    # Note that substitution only affects what is captured in the originally compiled pattern.
                    replaced_line = pattern.sub(f"\\g<1>{version}", line)
                    print(f"Updated '{description}' to '{version}' in '{file_name}' - pattern: `{pattern}`")
                else:
                    current_version = match.group(2)
                    # Validate the version
                    if current_version == version:
                        print(f"PASS '{description}' with pattern `{pattern}` matches '{version}' in '{file_name}'")
                        matched_patterns.append(regex_pattern)
        new_content.append(replaced_line)

    if is_update_mode:
        # Write the updated content back to the file
        with open(path, 'w') as file:
            file.writelines(new_content)
        return None
    # In validate mode, check if all required patterns have matched
    else:
        unmatched_patterns = set(patterns) - set(matched_patterns)
        for unmatched in unmatched_patterns:
            print(f"FAIL '{unmatched.description}' with pattern `{unmatched.pattern}` and version {unmatched.version} with version pattern `{unmatched.version_pattern if unmatched.version_pattern is not None else VERSION_REGEX}` did not match any content in '{file_name}'")
        return len(unmatched_patterns) == 0

def process(args: Namespace):
    """
    Processes the version update or validation of the extension and its dependencies 
    in the specified files. This function determines the mode (update or validate) based on 
    the provided arguments:
        - In update mode, the version will be replaced with the new version specified. 
        - In validate mode, the function checks whether all versions match the expected version 
          and prints the result.

    Parameters:
        args (Namespace): 
            An argparse.Namespace object containing the following attributes: version, paths,
            dependencies, and update. For more details, see the `parse_arguments()` function.

    Returns:
        None

    Raises:
        SystemExit: 
            - If version validation fails due to an invalid version format, the script exits 
              with status code 1.
            - If version validation fails during validate mode (mismatched versions), the script 
              exits with status code 1.
    """
    # Process the command-line arguments
    version = args.version
    # Break into individual paths, removing empty string paths
    if args.paths:
        paths = [
            path.strip() 
            for path in args.paths.split(',') 
            if path.strip()
        ]
    else:
        paths = []
    is_update_mode = args.update
    name = args.name

    print(f"{'Updating' if is_update_mode else 'Validating'} version {'to' if is_update_mode else 'is'} {version}")

    validation_passed = True

    paths_to_patterns = generate_extension_patterns(paths, version, name)
    dependency_paths_to_patterns = generate_dependency_patterns(paths, args.dependencies)
    # Merge the two dictionaries
    for key, value in dependency_paths_to_patterns.items():
        paths_to_patterns.setdefault(key, []).extend(value)

    for path, patterns in paths_to_patterns.items():
        validation_passed = process_file_version(path=path, patterns=patterns, is_update_mode=is_update_mode) and validation_passed
        print()
    if not is_update_mode:
        if validation_passed:
            print("All versions are correct!")
        else:
            error_exit(title="Version mismatch", message="One or more versions do not match the expected value.")
# endregion

def main():
    args = parse_arguments()
    print(DIVIDER_STRING)
    process(args)
    print(DIVIDER_STRING)

if __name__ == "__main__":
    main()