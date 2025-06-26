/*
  Copyright 2024 Adobe. All rights reserved.
  This file is licensed to you under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License. You may obtain a copy
  of the License at http://www.apache.org/licenses/LICENSE-2.0
  Unless required by applicable law or agreed to in writing, software distributed under
  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
  OF ANY KIND, either express or implied. See the License for the specific language
  governing permissions and limitations under the License.
*/

package com.adobe.marketing.mobile.gradle

import org.gradle.api.JavaVersion

/**
 * A collection of constants used throughout the build scripts in this project.
 */
object BuildConstants {
    object Versions {
        const val MIN_SDK_VERSION = 21
        const val COMPILE_SDK_VERSION = 34
        const val TARGET_SDK_VERSION = 34

        const val VERSION_CODE = 1
        const val VERSION_NAME = "1"

        val JAVA_SOURCE_COMPATIBILITY: JavaVersion = JavaVersion.VERSION_1_8
        val JAVA_TARGET_COMPATIBILITY: JavaVersion = JavaVersion.VERSION_1_8

        const val KOTLIN_LANGUAGE_VERSION = "1.5"
        const val KOTLIN_API_VERSION = "1.5"
        const val KOTLIN_JVM_TARGET = "1.8"


        const val AGP = "8.2.0"
        const val KOTLIN = "1.8.20"
        const val KOTLIN_COROUTINES = "1.6.0"
        const val KTLINT = "0.42.1"
        const val GOOGLE_JAVA_FORMAT = "1.15.0"
        const val PRETTIER = "2.7.1"
        const val PRETTIER_JAVA_PLUGIN = "1.6.2"
        const val CHECKSTYLE_TOOLS = "8.36.1"

        const val COMPOSE_COMPILER = "1.4.6"
        const val COMPOSE = "1.4.3"
        const val COMPOSE_MATERIAL = "1.4.3"
        const val ANDROIDX_ACTIVITY_COMPOSE = "1.5.0"

        const val ANDROIDX_APPCOMPAT = "1.0.0"
        const val ANDROIDX_CORE_KTX = "1.3.2"
        const val ANDROIDX_LIFECYCLE_KTX = "2.3.1"
        const val DOKKA = "1.9.10"
        const val DEXMAKER_MOKITO_INLINE = "2.28.3"
        const val SPOTLESS = "6.12.0"
        const val JUNIT = "4.13.2"
        const val MOCKITO = "4.5.1"
        const val MOCKK = "1.13.11"
        const val COMMONS_CODEC = "1.15"
        const val ROBOLECTRIC = "4.12.2"
        const val MOCKITO_KOTLIN = "3.2.0"
        const val JSON = "20160810"
        const val ANDROIDX_TEST_RULES = "1.4.0"
        const val ANDROIDX_TEST_RUNNER = "1.4.0"
        const val ANDROIDX_TEST_ORCHESTRATOR = "1.4.2"
        const val ANDROIDX_TEST_EXT_JUNIT = "1.1.3"
        const val ANDROIDX_TEST_UIAUTOMATOR = "2.3.0"
        const val ESPRESSO_CORE = "3.5.0"
    }

    object Dependencies {
        // Android Dependencies
        const val ANDROIDX_APPCOMPAT = "androidx.appcompat:appcompat:${Versions.ANDROIDX_APPCOMPAT}"
        const val KOTLIN_STDLIB_JDK8 = "org.jetbrains.kotlin:kotlin-stdlib-jdk8:${Versions.KOTLIN}"
        const val ANDROIDX_CORE_KTX = "androidx.core:core-ktx:${Versions.ANDROIDX_CORE_KTX}"
        const val ANDROIDX_LIFECYCLE_KTX = "androidx.lifecycle:lifecycle-runtime-ktx:${Versions.ANDROIDX_LIFECYCLE_KTX}"

        // Test Dependencies
        const val JUNIT = "junit:junit:${Versions.JUNIT}"
        const val DEXMAKER_MOKITO_INLINE = "com.linkedin.dexmaker:dexmaker-mockito-inline:${Versions.DEXMAKER_MOKITO_INLINE}"
        const val MOCKK = "io.mockk:mockk:${Versions.MOCKK}"
        const val MOCKITO_CORE = "org.mockito:mockito-core:${Versions.MOCKITO}"
        const val MOCKITO_INLINE = "org.mockito:mockito-inline:${Versions.MOCKITO}"
        const val COMMONS_CODEC = "commons-codec:commons-codec:${Versions.COMMONS_CODEC}"
        const val ROBOLECTRIC = "org.robolectric:robolectric:${Versions.ROBOLECTRIC}"
        const val MOCKITO_KOTLIN = "org.mockito.kotlin:mockito-kotlin:${Versions.MOCKITO_KOTLIN}"
        const val JSON = "org.json:json:${Versions.JSON}"
        const val KOTLIN_TEST = "org.jetbrains.kotlin:kotlin-test:${Versions.KOTLIN}"
        const val KOTLINX_COROUTINES_TEST = "org.jetbrains.kotlinx:kotlinx-coroutines-test:${Versions.KOTLIN_COROUTINES}"

        // Jetpack Compose Dependencies
        const val COMPOSE_RUNTIME = "androidx.compose.runtime:runtime:${Versions.COMPOSE}"
        const val COMPOSE_MATERIAL = "androidx.compose.material:material:${Versions.COMPOSE_MATERIAL}"
        const val ANDROIDX_ACTIVITY_COMPOSE = "androidx.activity:activity-compose:${Versions.ANDROIDX_ACTIVITY_COMPOSE}"
        const val COMPOSE_UI_TOOLING = "androidx.compose.ui:ui-tooling:${Versions.COMPOSE}"

        // Instrumentation Testing Dependencies
        const val ANDROIDX_TEST_RULES = "androidx.test:rules:${Versions.ANDROIDX_TEST_RULES}"
        const val ANDROIDX_TEST_EXT_JUNIT = "androidx.test.ext:junit:${Versions.ANDROIDX_TEST_EXT_JUNIT}"
        const val ANDROIDX_TEST_RUNNER = "androidx.test:runner:${Versions.ANDROIDX_TEST_RUNNER}"
        const val ANDROIDX_TEST_ORCHESTRATOR = "androidx.test:orchestrator:${Versions.ANDROIDX_TEST_ORCHESTRATOR}"
        const val ANDROIDX_TEST_UIAUTOMATOR = "androidx.test.uiautomator:uiautomator:${Versions.ANDROIDX_TEST_UIAUTOMATOR}"
        const val COMPOSE_UI_TEST_JUNIT4 = "androidx.compose.ui:ui-test-junit4:${Versions.COMPOSE}"
        const val COMPOSE_UI_TEST_MANIFEST = "androidx.compose.ui:ui-test-manifest:${Versions.COMPOSE}"
        const val ESPRESSO_CORE = "androidx.test.espresso:espresso-core:${Versions.ESPRESSO_CORE}"

        // Dokka Plugin Dependency
        const val DOKKA_PLUGIN = "org.jetbrains.dokka:kotlin-as-java-plugin:${Versions.DOKKA}"
    }

    internal object Plugins {
        const val ANDROID_LIBRARY = "com.android.library"
        const val ANDROID_APP = "com.android.application"
        const val KOTLIN_ANDROID = "kotlin-android"
        const val DOKKA = "org.jetbrains.dokka"
        const val SPOTLESS = "com.diffplug.spotless"
        const val CHECKSTYLE = "checkstyle"
        const val MAVEN_PUBLISH = "maven-publish"
        const val SIGNING = "signing"
        const val HIERYNOMUS_LICESNE = "com.github.hierynomus.license"
    }


    internal object Tasks {
        const val CHECKSTYLE = "checkstyle"
        const val JAVADOC_JAR = "javadocJar"
        const val SOURCES_JAR = "sourcesJar"
        const val DOKKA_JAVADOC = "dokkaJavadoc"
        const val CREATE_PHONE_RELEASE_JAVADOC = "createPhoneReleaseJavadoc"
        const val PHONE_RELEASE_SOURCES_JAR = "phoneReleaseSourcesJar"
        const val ASSEMBLE_PHONE = "assemblePhone"
        const val PUBLISH = "publish"
        const val PUBLISH_MAVEN_LOCAL = "publishToMavenLocal"
        const val PUBLISH_RELEASE_MAVEN_LOCAL = "publishReleasePublicationToMavenLocal"
        const val SIGN_RELEASE = "signReleasePublication"

        const val FUNCTIONAL_TEST_COVERAGE_REPORT = "functionalTestsCoverageReport"
        const val CREATE_PHONE_DEBUG_COVERAGE_REPORT = "createPhoneDebugCoverageReport"
        const val UNIT_TEST_COVERAGE_REPORT = "unitTestCoverageReport"
        const val TEST_PHONE_DEBUG_UNIT_TEST = "testPhoneDebugUnitTest"

        const val LICENSE_FORMAT_PROJECT = "licenseFormatProject"
        const val LICENSE_FORMAT = "licenseFormat"
    }

    internal object ProjectConfig {
        const val IMPLEMENTATION = "implementation"
        const val DEBUG_IMPLEMENTATION = "debugImplementation"
        const val TEST_IMPLEMENTATION = "testImplementation"
        const val ANDROID_TEST_IMPLEMENTATION = "androidTestImplementation"
        const val DOKKA = "dokkaPlugin"
    }

    internal object Formatting {
        const val ON = "format:on"
        const val OFF = "format:off"
        const val JAVA_TARGETS = "src/*/java/**/*.java"
        const val KOTLIN_TARGETS = "src/*/java/**/*.kt"

        val PRETTIER_CONFIG = mapOf(
            "prettier" to BuildConstants.Versions.PRETTIER,
            "prettier-plugin-java" to BuildConstants.Versions.PRETTIER_JAVA_PLUGIN
        )
        val PRETTIER_FORMAT_OPTIONS = mapOf(
                "parser" to "java",
                "tabWidth" to 4,
                "useTabs" to true,
                "printWidth" to 120
        )
    }

    const val ADOBE_LICENSE_HEADER = """/*
  Copyright ${'$'}YEAR Adobe. All rights reserved.
  This file is licensed to you under the Apache License, Version 2.0 (the "License");
  you may not use this file except in compliance with the License. You may obtain a copy
  of the License at http://www.apache.org/licenses/LICENSE-2.0
  Unless required by applicable law or agreed to in writing, software distributed under
  the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
  OF ANY KIND, either express or implied. See the License for the specific language
  governing permissions and limitations under the License.
*/

"""

    const val ADOBE_LICENSE_HEADER_RESOURCES = """Copyright ${'$'}{year} Adobe. All rights reserved.
This file is licensed to you under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License. You may obtain a copy
of the License at http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software distributed under
the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR REPRESENTATIONS
OF ANY KIND, either express or implied. See the License for the specific language
governing permissions and limitations under the License.
"""
    internal object CheckStyle {
        const val CONFIG = """<?xml version="1.0"?>
<!DOCTYPE module PUBLIC
		"-//Puppy Crawl//DTD Check Configuration 1.2//EN"
		"http://www.puppycrawl.com/dtds/configuration_1_2.dtd">

<module name="Checker">	
 	<module name="SuppressWarningsFilter" />
	<module name="TreeWalker">
		<module name="SuppressWarningsHolder" />
		<module name="FinalParameters"/>
		<module name="BooleanExpressionComplexity"/>
		<module name="EqualsAvoidNull"/>
		<module name="FallThrough"/>
		<module name="NestedForDepth"/>
		<module name="NestedIfDepth"/>
		<module name="NestedTryDepth"/>
		<module name="MagicNumber"/>
		<module name="AvoidStaticImport"/>
		<module name="IllegalImport"></module> 
    	<module name="RedundantImport"></module> 
    	<module name="UnusedImports"></module> 
	</module>
</module>"""
    }

    internal object Publishing {
        const val SNAPSHOTS_URL = "https://oss.sonatype.org/content/repositories/snapshots/"
        const val RELEASES_URL = "https://oss.sonatype.org/service/local/staging/deploy/maven2/"

        const val RELEASE_PROPERTY = "release"
        const val JITPACK_PROPERTY = "jitpack"
        const val SNAPSHOT_SUFFIX = "SNAPSHOT"

        const val LICENSE_NAME = "The Apache License, Version 2.0"
        const val LICENSE_URL = "https://www.apache.org/licenses/LICENSE-2.0.txt"
        const val LICENSE_DIST = "repo"

        const val DEVELOPER_ID = "adobe"
        const val DEVELOPER_NAME = "adobe"
        const val DEVELOPER_EMAIL = "adobe-mobile-testing@adobe.com"
        const val DEVELOPER_DOC_URL = "https://developer.adobe.com/client-sdks"

        const val SCM_CONNECTION_URL_TEMPLATE = "scm:git:github.com//adobe/%s.git"
        const val SCM_REPO_URL_TEMPLATE = "https://github.com/adobe/%s"

        const val ADOBE_GROUP_ID = "com.adobe.marketing.mobile"

        const val SIGNING_GNUPG_EXECUTABLE = "gpg"
        val SIGNING_GNUPG_KEY_NAME by lazy { System.getenv("GPG_KEY_ID") }
        val SIGNING_GNUPG_PASSPHRASE by lazy { System.getenv("GPG_PASSPHRASE") }

        const val MODULE_NAME_PROPERTY = "moduleName"
        const val MODULE_VERSION_PROPERTY = "moduleVersion"
        const val MAVEN_REPO_NAME_PROPERTY = "mavenRepoName"
        const val MAVEN_REPO_DESCRIPTION_PROPERTY = "mavenRepoDescription"

        const val MODULE_AAR_NAME_SUFFIX = "-phone-release.aar"
        const val MODULE_AAR_OUTPUT_PATH = "outputs/aar/"
    }

    internal  object Reporting {
        const val UNIT_TEST_EXECUTION_RESULTS_REGEX =
            "outputs/unit_test_code_coverage/phoneDebugUnitTest/*.exec"
        const val FUNCTIONAL_TEST_EXECUTION_RESULTS_REGEX =
            "outputs/code_coverage/phoneDebugAndroidTest/connected/*coverage.ec"
    }

    object BuildTypes {
        const val RELEASE = "release"
        const val DEBUG = "debug"
    }

    internal object SourceSets {
        const val MAIN = "main"
        const val PHONE = "phone"
    }

    internal object ProductFlavors {
        const val PHONE = "phone"
    }

    internal object BuildDimensions {
        const val TARGET = "target"
    }

    internal object Path {
        const val BUILD_CONFIG_CLASS = "**/BuildConfig.java"
        const val R_CLASS = "**/R.java"
        const val ADB_CLASS = "**/ADB*.class"

        const val INTERNAL_PACKAGES = "**/internal/*"
        const val SRC = "src"
        const val JAVA_FILES = "**/*.java"
        const val KOTLIN_FILES = "**/*.kt"
        const val GEN_FILES = "**/gen/**"
        const val TEST_FILES = "**/test/**"
        const val LEGACY_FILES = "**/legacy/**"
        const val ANDROID_TEST_FILES = "**/androidTest/**"
        const val PROPERTY_FILES = "**/*.properties"
        const val LOCAL_PROPERTY_FILES = "**/local.properties"
        const val XML_FILES = "**/*.xml"
        const val YML_FILES = "**/*.yml"
        const val GRADLE_KOTLIN_FILES = "**/*.gradle.kts"
        const val IDEA_DIR = "**/.idea/*"
        const val GIT_DIR = "**/.git/*"
        const val GRADLE_DIR = "**/.gradle/*"
        const val GRADLE_WRAPPER_DIR = "**/gradle/wrapper/*"
        const val BUILD_DIR = "**/build/*"
    }
}
