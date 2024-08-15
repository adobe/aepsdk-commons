#!/bin/bash

# Make this script executable from terminal:
# chmod 755 version.sh
set -e # Any subsequent(*) commands which fail will cause the shell script to exit immediately

ROOT_DIR=$(git rev-parse --show-toplevel)
LINE="================================================================================"
VERSION_REGEX="[0-9]+\.[0-9]+\.[0-9]+"

GRADLE_PROPERTIES_FILE="$ROOT_DIR/code/gradle.properties"

# Java files
JAVA_EXTENSION_VERSION_REGEX="^.*String EXTENSION_VERSION *= *"
# Kotlin files
KOTLIN_EXTENSION_VERSION_REGEX="^ +const val VERSION *= *"

help() {
    echo ""
    echo "Usage: $0 -v VERSION -d DEPENDENCIES -p PATHS [-g GRADLE_PROPERTIES_FILE] [-u]"
    echo ""
    echo -e "    -v\t- Version to update or verify for the extension. \n\t  Example: 3.0.2\n"
    echo -e "    -d\t- Comma separated dependencies to update along with their version. \n\t  Example: \"Core 3.1.1, Edge 3.2.1\"\n"
    echo -e "    -p\t- Comma separated file paths relative to the repository root to update. \n\t  Example: \"code/optimize/src/main/java/com/adobe/marketing/mobile/optimize/OptimizeConstants.java,code/optimize/src/androidTest/java/com/adobe/marketing/mobile/optimize/OptimizeTestConstants.java\"\n"
    echo -e "    -g\t- Path to the gradle.properties file relative to the repository root. Default: \$ROOT_DIR/code/gradle.properties\n"
    echo -e "    -u\t- Updates the version. If this flag is absent, the script instead verifies if the version is correct\n"
    exit 1 # Exit script after printing help
}

sed_platform() {
    # Use macOS vs Linux platform appropriate `sed` syntax.
    if [[ "$OSTYPE" == "darwin"* ]]; then
        sed -i '' "$@"
    else
        sed -i "$@"
    fi
}

update() {
    echo "Changing version to $VERSION"

    # Replace version in each provided path
    IFS="," read -r -a pathsArray <<< "$PATHS"
    for relative_path in "${pathsArray[@]}"; do
        path="$ROOT_DIR/${relative_path#/}" # Remove leading '/' in relative_path if it exists
        
        # Determine the correct regex and version name based on the file extension
        if [[ "$path" == *.java ]]; then
            regex_pattern="$JAVA_EXTENSION_VERSION_REGEX"
            version_name="EXTENSION_VERSION"
        elif [[ "$path" == *.kt ]]; then
            regex_pattern="$KOTLIN_EXTENSION_VERSION_REGEX"
            version_name="VERSION"
        else
            echo "Unknown file type for '$path'. Skipping..."
            continue
        fi

        # Apply the update logic using the determined regex pattern and version name
        echo "Changing '$version_name' to '$VERSION' in '$path'"
        sed_platform -E "/$regex_pattern/{s/$VERSION_REGEX/$VERSION/;}" "$path"
    done

    # Replace version in gradle.properties
    echo "Changing 'moduleVersion' to '$VERSION' in '$GRADLE_PROPERTIES_FILE'"
    sed_platform -E "/^moduleVersion/{s/$VERSION_REGEX/$VERSION/;}" "$GRADLE_PROPERTIES_FILE"

    # Replace dependencies in gradle.properties
    if [ "$DEPENDENCIES" != "none" ]; then
        IFS="," 
        dependenciesArray=($(echo "$DEPENDENCIES"))

        IFS=" "
        for dependency in "${dependenciesArray[@]}"; do
            dependencyArray=(${dependency// / })
            dependencyName=${dependencyArray[0]}
            dependencyVersion=${dependencyArray[1]}

            if [ "$dependencyVersion" != "" ]; then
                echo "Changing 'maven${dependencyName}Version' to '$dependencyVersion' in '$GRADLE_PROPERTIES_FILE'"
                sed_platform -E "/^maven${dependencyName}Version/{s/$VERSION_REGEX/$dependencyVersion/;}" "$GRADLE_PROPERTIES_FILE"
            fi        
        done
    fi
}

verify() {    
    echo "Verifying version is $VERSION"

    # Loop through the paths provided via the -p flag
    IFS="," read -r -a pathsArray <<< "$PATHS"
    for relative_path in "${pathsArray[@]}"; do
        # Build the full path relative to the ROOT_DIR
        path="$ROOT_DIR/${relative_path#/}" # Remove leading '/' in relative_path if it exists
        file_name=$(basename "$path")

        # Check if the file name does NOT contain the word "Test" (case insensitive)
        if [[ ! "$file_name" =~ [Tt][Ee][Ss][Tt] ]]; then
            # Determine the correct regex based on the file extension
            if [[ "$file_name" == *.java ]]; then
                version_regex="$JAVA_EXTENSION_VERSION_REGEX\"$VERSION\""
                variable_name="EXTENSION_VERSION"
            elif [[ "$file_name" == *.kt ]]; then
                version_regex="$KOTLIN_EXTENSION_VERSION_REGEX\"$VERSION\""
                variable_name="VERSION"
            else
                echo "Unknown file type for '$path'. Skipping..."
                continue
            fi

            # Check if the version in the file matches the expected version
            if grep -E "$version_regex" "$path" >/dev/null; then
                echo "PASS $variable_name matches $VERSION in $file_name"
            else
                echo "FAIL $variable_name does NOT match $VERSION in $file_name"
                exit 1
            fi
        else
            echo "Skipping file '$file_name' because it contains the word 'Test'."
        fi
    done

    # Check the module version in the gradle.properties file
    if grep -E "^moduleVersion=.*$VERSION" "$GRADLE_PROPERTIES_FILE" >/dev/null; then
        echo "PASS moduleVersion matches $VERSION in $(basename "$GRADLE_PROPERTIES_FILE")"
    else
        echo "FAIL moduleVersion does NOT match $VERSION in $(basename "$GRADLE_PROPERTIES_FILE")"            
        exit 1
    fi

    # Check dependencies versions in the gradle.properties file
    if [ "$DEPENDENCIES" != "none" ]; then
        IFS="," 
        dependenciesArray=($(echo "$DEPENDENCIES"))

        IFS=" "
        for dependency in "${dependenciesArray[@]}"; do
            dependencyArray=(${dependency// / })
            dependencyName=${dependencyArray[0]}
            dependencyVersion=${dependencyArray[1]}

            if [ "$dependencyVersion" != "" ]; then
                if grep -E "^maven${dependencyName}Version=.*$dependencyVersion" "$GRADLE_PROPERTIES_FILE" >/dev/null; then
                    echo "PASS maven${dependencyName}Version matches $dependencyVersion in $(basename "$GRADLE_PROPERTIES_FILE")"
                else
                    echo "FAIL maven${dependencyName}Version does NOT match $dependencyVersion in $(basename "$GRADLE_PROPERTIES_FILE")"
                    exit 1
                fi
            fi        
        done
    fi

    echo "Success"
}

# Parse command line arguments
while getopts "v:d:p:g:uh" opt; do
    case "$opt" in    
        v) VERSION="$OPTARG" ;;
        d) DEPENDENCIES="$OPTARG" ;;
        p) PATHS="$OPTARG" ;;
        g) GRADLE_PROPERTIES_FILE="$ROOT_DIR/${OPTARG#/}" ;;
        u) UPDATE="true" ;;
        h) help ;;
        ?) help ;; # Print help in case parameter is non-existent
    esac
done

# Check if VERSION is set
if [ -z "$VERSION" ]; then
    echo "Error: Version (-v) is required."
    help
fi

echo "$LINE"
if [[ ${UPDATE} = "true" ]]; then
    update 
else 
    verify
fi
echo "$LINE"