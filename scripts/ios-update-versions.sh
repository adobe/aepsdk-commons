#!/bin/bash

# To make this script executable from terminal:
# $ chmod 755 ios-update-versions.sh

# [IMPORTANT]: This script must be run on macOS because of the `sed` command syntax used to update the files.

set -e # Any subsequent(*) commands which fail will cause the shell script to exit immediately

ROOT_DIR=$(git rev-parse --show-toplevel)
LINE="================================================================================"
VERSION_REGEX="[0-9]+\.[0-9]+\.[0-9]+"
DEPENDENCIES=none
# Flag to determine if the extension is part of a multi-extension repo
# Affects things like the path used for source files (nested directory structure) and SPM repo URL
IS_MULTI_EXTENSION_REPO=false

# make a "dictionary" to help us find the correct spm repo per dependency (if necessary)
# IMPORTANT - this will be used in a regex search so escape special chars
# usage :
# getRepo AEPCore

# Define the repo URL for target name - (var names = value)
declare "repos_AEPCore=https:\/\/github\.com\/adobe\/aepsdk-core-ios\.git"
declare "repos_AEPRulesEngine=https:\/\/github\.com\/adobe\/aepsdk-rulesengine-ios\.git"

# Returns the URL associated with the provided extension name
# See `declare` statements above for supported extension names
getRepo() {
    local extensionName=$1
    local url="repos_$extensionName"
    echo "${!url}"
}

help()
{
   echo ""
   echo "Usage: $0 -n EXTENSION_NAME -v NEW_VERSION -d \"PODSPEC_DEPENDENCY_1, PODSPEC_DEPENDENCY_2\""
   echo ""
   echo -e "    -n\t- Name of the extension getting a version update. \n\t  Example: Edge, Analytics\n"
   echo -e "    -v\t- New version to use for the extension. \n\t  Example: 3.0.2\n"
   echo -e "    -d (optional)\t- Dependency(ies) that require updating in the extension's podspec and Package.swift file. \n\t  Example: -d \"AEPCore 3.7.3\" (update the dependency on AEPCore to version 3.7.3 or newer)\n"
   
   # Exit with the provided status code if supplied, otherwise exit with 0
   exit ${1:-0}
}

# Print help (non-error case) if user explicitly asks for it with -h or --help
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
   help 0
fi

while getopts "n:v:d:" opt
do
   case "$opt" in
      n ) NAME="$OPTARG" ;;
      v ) NEW_VERSION="$OPTARG" ;;
      d ) DEPENDENCIES="$OPTARG" ;;      
      ? ) help 1 ;; # Print help (error case) in case parameter is non-existent
   esac
done

# If mandatory parameters are empty, print help (error case)
if [ -z "$NAME" ] || [ -z "$NEW_VERSION" ]
then
   echo "********** USAGE ERROR **********"
   echo "Some or all of the parameters are empty. See usage requirements below:";
   help 1
fi

# Begin script when all parameters are correct
echo ""
echo "$LINE"
echo "Changing version of AEP$NAME to $NEW_VERSION with the following minimum version dependencies: $DEPENDENCIES"
echo "$LINE"

#############################################
# Podspec + SPM version update
#############################################
PODSPEC_FILE=$ROOT_DIR"/AEP"$NAME.podspec
SPM_FILE=$ROOT_DIR/Package.swift

echo "Changing value of 's.version' to '$NEW_VERSION' in '$PODSPEC_FILE'"
sed -i '' -E "/^ *s.version/{s/$VERSION_REGEX/$NEW_VERSION/;}" $PODSPEC_FILE

# Replace dependencies in podspec and Package.swift
if [ "$DEPENDENCIES" != "none" ]; then
    IFS="," 
    dependenciesArray=($(echo "$DEPENDENCIES"))

    IFS=" "
    for dependency in "${dependenciesArray[@]}"; do
        dependencyArray=(${dependency// / })
        dependencyName=${dependencyArray[0]}
        dependencyVersion=${dependencyArray[1]}

        # Check if dependencyVersion is an empty string and continue to the next iteration if true
        if [ -z "$dependencyVersion" ]; then
            echo "Skipping $dependencyName for $NAME due to empty version"
            continue
        fi
        
        # Podspec version update
        echo "Changing value of 's.dependency' for '$dependencyName' to '>= $dependencyVersion' in '$PODSPEC_FILE'"
        sed -i '' -E "/^ *s.dependency +'$dependencyName'/{s/$VERSION_REGEX/$dependencyVersion/;}" $PODSPEC_FILE

        # Early exit path for targets that do not use/support SPM
        # Check if NAME is TestUtils and continue if true - TestUtils does not currently support SPM
        if [ "$NAME" == "TestUtils" ]; then 
            continue
        fi

        # SPM version update
        spmRepoUrl=$(getRepo $dependencyName)
        if [ "$spmRepoUrl" != "" ]; then
            echo "Changing value of '.upToNextMajor(from:)' for '$spmRepoUrl' to '$dependencyVersion' in '$SPM_FILE'"
            sed -i '' -E "/$spmRepoUrl\", \.upToNextMajor/{s/$VERSION_REGEX/$dependencyVersion/;}" $SPM_FILE
        fi
    done
fi

#############################################
# Constants files version update
#############################################
# Early exit path for targets that do not have constants files with versions to update
if [ "$NAME" == "Services" ] || [ "$NAME" == "TestUtils" ]; then
    echo "No constants to replace"
# Special handling cases
elif [ "$NAME" == "Core" ]; then
    # Core needs to update Event Hub and Configuration Constants
    CONSTANTS_FILE=$ROOT_DIR"/AEP$NAME/Sources/configuration/ConfigurationConstants.swift"
    echo "Changing value of 'EXTENSION_VERSION' to '$NEW_VERSION' in '$CONSTANTS_FILE'"
    sed -i '' -E "/^ +static let EXTENSION_VERSION/{s/$VERSION_REGEX/$NEW_VERSION/;}" $CONSTANTS_FILE

    EVENT_HUB_FILE=$ROOT_DIR"/AEP$NAME/Sources/eventhub/EventHubConstants.swift"
    echo "Changing value of 'VERSION_NUMBER' to '$NEW_VERSION' in '$EVENT_HUB_FILE'"
    sed -i '' -E "/^ +static let VERSION_NUMBER/{s/$VERSION_REGEX/$NEW_VERSION/;}" $EVENT_HUB_FILE
# General case
else
    if [ "$IS_MULTI_EXTENSION_REPO" == "true" ]; then
        CONSTANTS_FILE=$ROOT_DIR"/AEP$NAME/Sources/"$NAME"Constants.swift"
    else
        CONSTANTS_FILE=$ROOT_DIR"/Sources/"$NAME"Constants.swift"
    fi
    echo "Changing value of 'EXTENSION_VERSION' to '$NEW_VERSION' in '$CONSTANTS_FILE'"
    sed -i '' -E "/^ +static let EXTENSION_VERSION/{s/$VERSION_REGEX/$NEW_VERSION/;}" $CONSTANTS_FILE
fi

#############################################
# Test file version updates
#############################################
# Replace test version in Core's MobileCoreTests.swift
if [ "$NAME" == "Core" ]; then
    TEST_FILE=$ROOT_DIR"/AEP$NAME/Tests/MobileCoreTests.swift"
    echo "Changing value of 'version' to '$NEW_VERSION' in '$TEST_FILE'"
    sed -i '' -E "/^ +\"version\" : \"/{s/[1-9]+\.[0-9]+\.[0-9]+/$NEW_VERSION/;}" $TEST_FILE
fi

#############################################
# Xcode project marketing version updates
#############################################
# Early exit path for targets that do not affect the project's Xcode marketing version
if [ "$NAME" == "TestUtils" ]; then
    echo "TestUtils version is not matched with Core. Exiting."
    exit 0
fi

# Replace marketing versions in project.pbxproj
PROJECT_PBX_FILE="$ROOT_DIR/AEP$NAME.xcodeproj/project.pbxproj"
echo "Changing value of 'MARKETING_VERSION' to '$NEW_VERSION' in '$PROJECT_PBX_FILE'"
sed -i '' -E "/^\t+MARKETING_VERSION = /{s/$VERSION_REGEX/$NEW_VERSION/;}" $PROJECT_PBX_FILE
