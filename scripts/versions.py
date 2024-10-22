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

import argparse
import os
import re
import subprocess
import sys

from argparse import Namespace
from dataclasses import dataclass
from string import Template
from typing import Callable

DIVIDER_STRING = "=" * 80
VERSION_REGEX = r"[0-9]+\.[0-9]+\.[0-9]+"
TEST_VERSION_REGEX = r"[1-9]+\.[0-9]+\.[0-9]+"
DEPENDENCY_FILE_TYPES = {'.properties', '.podspec', 'swift_spm'}
"""
A set of file types that contain dependency version declarations. This set is used to identify files 
that may require version updates for dependencies when processing the provided paths.

File Types:
    - '.properties': Gradle properties files containing dependency version information.
    - '.podspec': CocoaPods specification files that declare dependencies.
    - 'swift_spm': Swift Package Manager files that list dependencies.

Usage:
    Files with these extensions will trigger the application of dependency-specific regex patterns 
    to update the declared versions within them.
"""

@dataclass
class Dependency:
    """
    A data class representing a dependency with its name, version, and an optional list of 
    file paths where it applies.

    Attributes:
        name (str): 
            The name of the dependency. It is recommended to use the full dependency name 
            with the prefix 'AEP' (ex: 'AEPEdgeBridge').

        version (str): 
            The version of the dependency, following semantic versioning (ex: '3.1.1').
        
        absolute_file_paths (list[str] | None): 
            A list of absolute file paths where the dependency applies.
            - If `None`, the dependency applies to **all files**.
            - If a list of file paths is provided, the dependency applies **only to the specified files**.
    """
    name: str
    version: str
    absolute_file_paths: list[str] | None

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
    pattern: str
    description: str
    version: str | None = None

    def __iter__(self):
        return iter((self.pattern, self.version, self.description))

@dataclass
class RegexTemplate:
    """
    A data class representing a regex template used for generating patterns dynamically based on a dependency.

    Attributes:
        template (Callable[[Dependency], str]): 
            A callable function that takes a `Dependency` object as input and returns a regex 
            pattern as a string. This allows the pattern to be customized based on the dependency.

        description (str): 
            A human-readable description of what the pattern matches.
    """
    template: Callable[[Dependency], str]
    description: str

@dataclass
class FilePatternGroup:
    """
    A data class that groups a file path with its associated pattern type and regex patterns.

    Attributes:
        path (str): 
            The absolute path to the file being processed.

        file_pattern_type (str | None): 
            The specific pattern type for the file, if any. This allows files to be associated 
            with custom regex patterns beyond what their file extensions imply. If no pattern 
            type is provided, it defaults to `None`.

        patterns (list[RegexPattern]): 
            A list of `RegexPattern` objects representing the regex patterns applicable to the file. 
            These patterns are used to match and update version declarations in the file.
    """
    path: str
    file_pattern_type: str | None
    patterns: list[RegexPattern]

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
        print("ERROR: Not a git repository or unable to determine root directory.")
        sys.exit(1)

def get_dependency_name_for_gradle_properties(dependency: Dependency) -> str:
    """
    Extracts and returns the Gradle-compatible dependency name by removing the 'AEP' prefix 
    from the provided dependency's name. This ensures the dependency name aligns with the naming 
    convention used in Gradle properties files.

    Parameters:
        dependency (Dependency): 
            A `Dependency` object containing the full name of the dependency, which typically 
            starts with the prefix 'AEP'.

    Returns:
        str: 
            The dependency name with the 'AEP' prefix removed.

    Example:
        Input:
            Dependency(name='AEPCore', version='3.1.1')

        Output:
            "Core"
    """
    return dependency.name[3:]

def get_ios_repo_name(dependency: Dependency) -> str:
    """
    Generates the GitHub repository URL for the given iOS dependency based on its name. 
    If the dependency belongs to the core dependencies, a specific core repository URL is returned. 
    Otherwise, the repository name is constructed dynamically based on the dependency name.

    Parameters:
        dependency (Dependency): 
            A `Dependency` object containing the name of the iOS dependency.

    Returns:
        str: 
            The GitHub repository URL for the specified iOS dependency. If the dependency name is unknown 
            or does not follow the expected naming convention, it prints a warning and returns `None`.

    Example:
        Input:
            Dependency(name='AEPCore', version='3.1.1', absolute_file_paths=None)

        Output:
            "https://github.com/adobe/aepsdk-core-ios.git"
    """
    dependency_name = dependency.name
    core_dependencies = {'AEPCore', 'AEPIdentity', 'AEPLifecycle', 'AEPServices', 'AEPSignal'}
    if dependency_name in core_dependencies:
        return 'https://github.com/adobe/aepsdk-core-ios.git'
    else:
        if dependency_name.startswith('AEP'):
            repo_name = dependency_name[3:].lower()
            return f'https://github.com/adobe/aepsdk-{repo_name}-ios.git'
        else:
            print(f"Unknown dependency name '{dependency_name}'. Cannot construct repo URL.")
            return None

def gradle_properties_template(dependency: Dependency) -> str:
    """
    Generates a regex pattern for matching a dependency version declaration within a Gradle properties file.
    The pattern identifies the Maven version entry corresponding to the provided dependency.

    Parameters:
        dependency (Dependency): 
            A `Dependency` object containing the name of the dependency. The name is used to generate 
            the appropriate Maven property name for substitution in the regex pattern.

    Returns:
        str: 
            A regex pattern as a string, with the dependency name injected into the template to match 
            the Maven version entry.

    Example:
        Input:
            Dependency(name='AEPCore', version='3.1.1', absolute_file_paths=None)

        Output:
            "^[\\s\\S]*mavenCoreVersion\\s*=\\s*"
    """
    template = Template(r'^[\s\S]*maven${dependency_name}Version\s*=\s*')
    gradle_dependency_name = get_dependency_name_for_gradle_properties(dependency)
    return template.substitute(dependency_name=gradle_dependency_name)

def swift_spm_template(dependency: Dependency) -> str:
    """
    Generates a regex pattern for matching a Swift Package Manager dependency declaration. 
    The pattern identifies the package URL and ensures the version constraint uses the `.upToNextMajor(from:)` method.

    Parameters:
        dependency (Dependency): 
            A `Dependency` object containing the name of the dependency. The name is used to generate the 
            appropriate repository URL for substitution in the regex pattern.

    Returns:
        str: 
            A regex pattern as a string, with the dependency's repository URL injected into the template.

    Example:
        Input:
            Dependency(name='AEPCore', version='3.1.1', absolute_file_paths=None)

        Output:
            "^[\\s\\S]*\\.package\\(\\s*url:\\s*\"https://github.com/adobe/aepsdk-core-ios.git\"\\s*,\\s*\\.upToNextMajor\\(\\s*from:\\s*\""
    """
    template = Template(r'^[\s\S]*\.package\(\s*url:\s*"${dependency_url}"\s*,\s*\.upToNextMajor\(\s*from:\s*"')
    ios_dependency_repo = get_ios_repo_name(dependency)
    return template.substitute(dependency_url=ios_dependency_repo)

def podspec_template(dependency: Dependency) -> str:
    """
    Generates a regex pattern for matching a dependency declaration within a CocoaPods podspec file.
    The pattern matches the dependency name and ensures that the version constraint uses the '>=' operator.

    Parameters:
        dependency (Dependency): 
            A `Dependency` object containing the name of the dependency for which the regex pattern 
            will be generated.

    Returns:
        str: 
            A regex pattern as a string, with the dependency name injected into the pattern.

    Example:
        Input:
            Dependency(name='AEPCore', version='3.1.1', absolute_file_paths=None)

        Output:
            "^[\\s\\S]*s\\.dependency\\s*['\"]AEPCore['\"]\\s*,\\s*['\"]>=\\s*"
    """
    # Triple quote used to avoid escaping single quotes in the template
    template = Template(r'''^[\s\S]*s\.dependency\s*["']${dependency_name}["']\s*,\s*["']>=\s*''')
    name = dependency.name
    return template.substitute(dependency_name=name)

ROOT_DIR = get_root_dir()

STATIC_REGEX_PATTERNS: dict[str, list[RegexPattern]] = {
    # Android project regex patterns
    '.properties': [
        RegexPattern(
            pattern=r'^[\s\S]*moduleVersion\s*=\s*',
            description='moduleVersion'
        ),
    ],
    '.java': [
        RegexPattern(
            pattern=r'^[\s\S]*String EXTENSION_VERSION\s*=\s*"',
            description='EXTENSION_VERSION'
        )
    ],
    '.kt': [
        RegexPattern(
            pattern=r'^[\s\S]*const val VERSION\s*=\s*"',
            description='VERSION'
        )
    ],
    # iOS project regex patterns
    '.pbxproj': [
        RegexPattern(
            pattern=r'^[\s\S]*MARKETING_VERSION = ',
            description='MARKETING_VERSION'
        )
    ],
    '.podspec': [
        RegexPattern(
            pattern=r'^[\s\S]*s\.version\s*=\s*"',
            description='s.version'
        )
    ],
    '.swift': [
        RegexPattern(
            pattern=r'^[\s\S]*static let EXTENSION_VERSION\s*=\s*"',
            description='EXTENSION_VERSION'
        )
    ],
    # For Swift files that use VERSION_NUMBER instead of EXTENSION_VERSION
    # Ex: EventHubConstants.swift
    'swift_version_number': [
        RegexPattern(
            pattern=r'^[\s\S]*static let VERSION_NUMBER\s*=\s*"',
            description='VERSION_NUMBER'
        )
    ],
    # For Swift test files that define version in JSON
    # This also uses the TEST_VERSION_REGEX instead of the VERSION_REGEX
    # Ex: MobileCoreTests.swift
    'swift_test_version': [
        RegexPattern(
            pattern=r'^[\s\S]*\"version\"\s*:\s*"',
            description='version'
        )
    ],
}
"""
A dictionary mapping file extensions and pattern types to a list of RegexPattern objects. 
The regex patterns aim to be permissive with whitespace to avoid blocking different formatting styles.

Key:
    - File extension or pattern type as a string (e.g., '.properties', 'swift_test_version').

Value:
    - A list of RegexPattern objects
"""

TEMPLATE_REGEX_PATTERNS: dict[str, list[RegexTemplate]] = {
    '.properties': [
        RegexTemplate(
            template=gradle_properties_template,
            description='maven<dependencyName>Version'
        )
    ],
    'swift_spm': [
        RegexTemplate(
            template=swift_spm_template,
            description='.upToNextMajor(from:)'
        )
    ],
    '.podspec': [
        RegexTemplate(
            template=podspec_template,
            description='s.dependency'
        )
    ],
}
"""
A dictionary mapping file extensions or pattern types to lists of RegexTemplate objects. These templates 
generate regex patterns dynamically based on the provided `Dependency` object, allowing dependency-specific 
version strings to be matched and updated in their corresponding files.

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
            The version to update or verify for the extension. 
            Example: 3.0.2. This argument is required.
        
        -d, --dependencies (str, optional): 
            A comma-separated list of dependencies with their versions. Each dependency can 
            optionally specify the file paths where it applies using the `@` symbol. 
            - Syntax: 
                `<name> <version>[@file_path1[,file_path2,...]]`
            - If the `@` syntax is used, the dependency will only be applied to the specified files.
            - When specifying custom files, you must provide either an absolute or relative path to each file.
            - If the `@` symbol is omitted, the dependency applies to all relevant files.
            Example: 
                `"AEPCore 3.1.1, AEPServices 8.9.10@AEPCore.podspec, Edge 3.2.1@Package.swift"`

        -p, --paths (str): 
            A comma-separated list of absolute or relative file paths to update or verify. 
            Each path can optionally specify a pattern type using the syntax:
                `path[:pattern_type]`
            - Example: 
                `"src/Package.swift:swift_spm, src/Utils.swift, src/Test.swift:swift_test_version"`
            This argument is required.

        -u, --update (flag): 
            If provided, the script will update the versions in the specified files. 
            If omitted, the script will verify the existing versions instead.

    Example Usage:
        --update -v 6.7.8 \
        -p "Package.swift:swift_spm, AEPCore/Tests/MobileCoreTests.swift:swift_test_version, AEPCore/Sources/eventhub/EventHubConstants.swift:swift_version_number, AEPCore/Sources/configuration/ConfigurationConstants.swift, AEPCore.podspec, AEPCore.xcodeproj/project.pbxproj" \
        -d "AEPRulesEngine 7.8.9, AEPServices 8.9.10@AEPCore.podspec"
        
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
        description='Update or verify versions in project files.'
    )

    parser.add_argument(
        '-v', '--version', 
        required=True, 
        help='Version to update or verify for the extension. Example: 3.0.2'
    )
    parser.add_argument(
        '-d', '--dependencies', 
        default='none', 
        help='Comma-separated dependencies to update along with their version. Example: "Core 3.1.1, Edge 3.2.1"'
    )
    parser.add_argument(
        '-p', '--paths', 
        required=True, 
        help='Comma-separated file paths relative to the repository root to update.'
    )
    parser.add_argument(
        '-u', '--update', 
        action='store_true', 
        help='Updates the version. If this flag is absent, the script instead verifies if the version is correct.'
    )

    args: Namespace = parser.parse_args()
    return args

def convert_to_absolute_path(file_path: str) -> str:
    # Convert relative paths to absolute by appending them to the root directory
    if not file_path.startswith('/'):
        file_path = os.path.join(ROOT_DIR, file_path)
    return file_path

# Example path: "src/Package.swift:swift_spm, src/Utils.swift, src/Test.swift:test"
def parse_paths(paths: str, version: str) -> list[FilePatternGroup]:
    """
    Parses a comma-separated list of file paths and their optional pattern types, returning a list 
    of `FilePatternGroup` objects. Each path can optionally specify a pattern type by separating it 
    with a colon (`:`). If no type is specified, the default pattern for the file's extension is used.

    Parameters:
        paths (str): 
            A comma-separated string containing file paths. Each path can optionally include 
            a pattern type using the format `path[:file_type]`. Example:
            "src/Package.swift:swift_spm, src/Utils.swift, src/Test.swift:test".

    Returns:
        list[FilePatternGroup]: 
            A list of `FilePatternGroup` objects, where each object represents a file path, 
            its pattern type (if any), and the associated regex patterns.

    Example:
        Input: "src/Package.swift:swift_spm, src/Utils.swift, src/Test.swift:swift_test_version"
        
        Output:
            [
                FilePatternGroup(path='/root/src/Package.swift', file_pattern_type='swift_spm', patterns=[...]),
                FilePatternGroup(path='/root/src/Utils.swift', file_pattern_type=None, patterns=[...]),
                FilePatternGroup(path='/root/src/Test.swift', file_pattern_type='swift_test_version', patterns=[...])
            ]
    """

    paths_list: list[FilePatternGroup] = []

    # Example input: "src/Package.swift:swift_spm, src/Utils.swift, src/Test.swift:test"
    for path in paths.split(','):
        file_path = path.strip() # Trim leading and trailing spaces from the path
        
        # Check if the path specifies a pattern type using a colon (':')
        if ':' in file_path:
            # Split the path into the file path and its associated pattern type
            file_path, file_type = file_path.split(':', 1)
        else:
            file_path = file_path
            file_type = None # No specific pattern type provided

        # Convert relative paths to absolute by appending them to the root directory
        file_path = convert_to_absolute_path(file_path)

        # Verify that the path points to a valid file; skip it if not
        if not os.path.isfile(file_path):
            print(f"File '{file_path}' does not exist or is not a file. Skipping...")
            continue
        
        # Determine the appropriate regex patterns for the file based on type or extension
        if file_type:
            applicable_patterns = STATIC_REGEX_PATTERNS.get(file_type, [])
        else:
            file_extension = os.path.splitext(path)[1]
            applicable_patterns = STATIC_REGEX_PATTERNS.get(file_extension, [])
        
        remapped_patterns = [
            RegexPattern(pattern=pattern.pattern, description=pattern.description, version=version)
            for pattern in applicable_patterns
        ]

        # Create a FilePatternGroup object with the path, type, and patterns, and store it
        paths_list.append(FilePatternGroup(
            path=file_path.strip(), 
            file_pattern_type=file_type.strip() if file_type else None,
            patterns=remapped_patterns
        ))

    return paths_list

def parse_dependencies(dependencies_str: str) -> list[Dependency]:
    """
    Parses a comma-separated string of dependencies and their versions, returning a list of 
    `Dependency` objects. 

    Dependencies that do not start with the prefix `AEP` are automatically standardized by adding 
    the `AEP` prefix to the name.

    Parameters:
        dependencies_str (str): 
            A comma-separated string of dependencies with their versions. See `parse_arguments()` 
            for more on dependency string formatting options.

    Returns:
        list[Dependency]: 
            A list of `Dependency` objects.

    Example:
        Input:
            "AEPCore 3.1.1, Edge 3.2.1@Package.swift, AEPRulesEngine 7.8.9"
        
        Output:
            [
                Dependency(name='AEPCore', version='3.1.1', file_paths=None),
                Dependency(name='AEPEdge', version='3.2.1', file_paths=['/path/to/Package.swift']),
                Dependency(name='AEPRulesEngine', version='7.8.9', file_paths=None)
            ]
    """
    dependencies_list: list[Dependency] = []
    dependencies_input: list[str] = [dep.strip() for dep in dependencies_str.split(',')]

    for dependency in dependencies_input:
        dep_parts = dependency.strip().split('@')
        base_parts = dep_parts[0].split()
        if len(base_parts) != 2:
            print(f"Invalid dependency format: '{dependency}'. Skipping...")
            continue

        dependency_name, dependency_version = base_parts
        files = dep_parts[1].split(',') if len(dep_parts) > 1 else None
        absolute_file_paths = None
        if files: 
            absolute_file_paths = []
            for file in files:
                absolute_file_paths.append(convert_to_absolute_path(file))

        # Standardize dependency name
        if not dependency_name.startswith('AEP'):
            dependency_name = f'AEP{dependency_name}'

        print(f"Dependency: name={dependency_name}, version={dependency_version}, files={absolute_file_paths}")

        dependencies_list.append(
            Dependency(name=dependency_name, version=dependency_version, absolute_file_paths=absolute_file_paths)
        )

    return dependencies_list

###################################################################
# region Update versions
###################################################################
# Updates the versions for the given file path for both the extension and its dependencies
# All of the regex patterns are evaluated for each line and if a match is found, the version is updated
def process_file_version(version: str, file_pattern_group: FilePatternGroup, dependencies: list[Dependency] | None, is_update_mode: bool) -> bool | None:
    """
    Processes a single file to either update or verify the version and dependencies.

    In update mode, the function replaces matching version strings with the new version. 
    In verify mode, it checks whether the existing versions in the file match the expected version. 
    Additionally, if the file supports dependencies, relevant patterns for the dependencies are applied 
    based on the file type.

    Parameters:
        version (str): 
            The version to apply or verify. Example: "6.7.8".
        file_pattern_group (FilePatternGroup): 
            An object representing the file path, pattern type (if any), and the regex patterns 
            associated with the file.
        dependencies (list[Dependency] | None): 
            A list of `Dependency` objects.
        is_update_mode (bool): 
            If True, the function updates the version in the file. If False, the function verifies 
            that the versions are correct.

    Returns:
        bool | None: 
            - In **verify mode**, returns True if all versions match the expected value, otherwise False.
            - In **update mode**, returns None after updating the file content.

    Raises:
        FileNotFoundError: 
            If the specified file path does not exist or cannot be read.
        IOError: 
            If there is an issue reading or writing to the file.
    """
    
    path = file_pattern_group.path
    file_extension = os.path.splitext(path)[1]
    file_name = os.path.basename(path)
    file_pattern_type = file_pattern_group.file_pattern_type
    # Combine extension version patterns and dependency patterns
    applicable_patterns = file_pattern_group.patterns

    print(f"---- {'Updating' if is_update_mode else 'Verifying'} versions in '{file_name}' ----")
    print(f"  * File path: {path}")
    
    # Filter dependencies for the current file
    applicable_dependencies: list[Dependency] = []
    for dependency in dependencies:
        if dependency.absolute_file_paths is None or path in dependency.absolute_file_paths:
            applicable_dependencies.append(dependency)

    # If the file may contain dependencies, set up dependency patterns
    if file_pattern_type in DEPENDENCY_FILE_TYPES or file_extension in DEPENDENCY_FILE_TYPES:
        print("Set up patterns for dependencies:")
        # Get dependency regex templates based on file type or extension
        dependency_regex_templates = (
            TEMPLATE_REGEX_PATTERNS.get(file_pattern_type, []) +
            TEMPLATE_REGEX_PATTERNS.get(file_extension, [])
        )
        if not dependency_regex_templates:
            print(f"  * WARNING: No dependency regex patterns defined for file type '{file_pattern_type}' in '{file_name}'. Skipping...")
        else:
            # Generate regex patterns for each dependency
            for dependency in applicable_dependencies:
                for regex_template in dependency_regex_templates:
                    generated_pattern = regex_template.template(dependency)
                    print(f"  * Template applied for dependency '{dependency.name}' - Pattern description: {regex_template.description} - Final pattern: {generated_pattern}")
                    applicable_patterns.append(RegexPattern(pattern=generated_pattern, version=dependency.version, description=regex_template.description))

    if not applicable_patterns:
        print(f"  * WARNING: No valid regex patterns defined for file type '{file_extension}' in '{file_name}'. Skipping...")
        return True # Considered successful since there's nothing to check or update

    # Read the file content
    with open(path, 'r') as file:
        content = file.readlines()

    matched_patterns = []  # List to keep track of patterns that have matched

    # Apply the update or verify logic to each line
    new_content = []
    for line in content:
        replaced_line = line
        for applicable_pattern in applicable_patterns:
            regex_pattern = applicable_pattern.pattern
            label = applicable_pattern.description
            pattern_version = applicable_pattern.version
            version_regex = TEST_VERSION_REGEX if label == 'version' else VERSION_REGEX
            # Compile regex with two capture groups: the pattern and the version
            # Notice the two parentheses added around the pattern and version regex
            pattern = re.compile(f"({regex_pattern})({version_regex})")
            match = pattern.match(line)
            if match:
                if is_update_mode:
                    # Use a named capture group to avoid incorrectly merging the group and version.
                    # ex without named capture group: capture group \\1 and version 6.7.8 -> \\16.7.8 (interpreted as capture group 16)
                    replaced_line = pattern.sub(f"\\g<1>{pattern_version}", line)
                    print(f"Updated '{label}' to '{pattern_version}' in '{file_name}'")
                else:
                    current_version = match.group(2)
                    # Verify the version
                    if current_version == pattern_version:
                        print(f"PASS '{label}' with pattern `{regex_pattern}` matches '{pattern_version}' in '{file_name}'")
                        matched_patterns.append(applicable_pattern)
        new_content.append(replaced_line)

    # In verify mode, check if all required patterns have matched
    if is_update_mode:
        # Write the updated content back to the file
        with open(path, 'w') as file:
            file.writelines(new_content)
        return None
    else:
        unmatched_patterns = set(applicable_patterns) - set(matched_patterns)
        for unmatched in unmatched_patterns:
            print(f"FAIL '{unmatched.description}' with pattern `{unmatched.pattern}` did not match any content in '{file_name}'")
        return len(unmatched_patterns) == 0

def process(args: Namespace):
    """
    Processes the version update or validation of the extension and its dependencies 
    in the specified files. This function determines the mode (update or verify) based on 
    the provided arguments:
        - In update mode, the version will be replaced with the new version specified. 
        - In verify mode, the function checks whether all versions match the expected version 
          and prints the result.

    Parameters:
        args (Namespace): 
            An argparse.Namespace object containing the following attributes: version, paths,
            dependencies, and update. For more details, see the `parse_arguments()` function.

    Returns:
        None

    Raises:
        SystemExit: 
            If version validation fails during verify mode, the function exits the script 
            with status code 1.
    """
    version = args.version
    paths = args.paths
    is_update_mode = args.update

    print(f"{'Updating' if is_update_mode else 'Verifying'} version {'to' if is_update_mode else 'is'} {version}")

    validation_passed = True

    file_pattern_groups = parse_paths(paths, version)
    dependencies = parse_dependencies(args.dependencies)
    for file_pattern_group in file_pattern_groups:
        validation_passed = process_file_version(version, file_pattern_group, dependencies, is_update_mode) and validation_passed
        print()
    if not is_update_mode:
        if validation_passed:
            print("All versions are correct!")
        else:
            print("Version validation failed.")
            sys.exit(1)
# endregion

def main():
    args = parse_arguments()
    print(DIVIDER_STRING)
    process(args)
    print(DIVIDER_STRING)

if __name__ == "__main__":
    main()