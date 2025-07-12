clean:
	(./gradlew -p sdk-bom clean)

# SDK size
sdk-size:
	(./gradlew -p sdk-bom computeSdkSize)

bom-project-refresh-dependencies:
	(./gradlew -p sdk-bom build --refresh-dependencies)

# SDK BOM artifact
bump-bom-version-and-update-bom-properties:
	(./gradlew -p sdk-bom bumpBomVersion)
	(./gradlew -p sdk-bom storeLatestExtensionInfo)

generate-bom-release-notes:
	(./gradlew -p sdk-bom bom_release_notes)

print-bom-version:
	(grep "^bomVersion=" ./gradle.properties | sed -e 's/.*=//')

generate-bom-pom:
	(./gradlew -p sdk-bom generatePomFileForReleasePublication)

print-bom-pom:
	(xmllint --format ./sdk-bom/build/publications/release/pom-default.xml)

bom-publish-maven-local:
	(./gradlew -p sdk-bom publishReleasePublicationToMavenLocal -x signReleasePublication)

bom-assemble-release:
	(./gradlew -p sdk-bom assembleRelease --stacktrace)

bom-publish-snapshot: clean bom-assemble-release
	(./gradlew -p sdk-bom --stacktrace)

bom-publish-main: clean bom-assemble-release
	(./gradlew -p sdk-bom -Prelease)
