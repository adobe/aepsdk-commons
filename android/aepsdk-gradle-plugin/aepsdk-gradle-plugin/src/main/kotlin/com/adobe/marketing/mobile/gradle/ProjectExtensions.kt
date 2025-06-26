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

import com.android.build.gradle.BaseExtension
import org.gradle.api.Project
import org.gradle.api.Task
import org.gradle.api.tasks.TaskProvider
import org.gradle.api.tasks.bundling.Jar
import org.gradle.kotlin.dsl.create
import org.gradle.kotlin.dsl.get
import org.gradle.kotlin.dsl.named
import org.gradle.kotlin.dsl.register

/**
 * Creates the AEP Library configuration extension for the project.
 */
internal fun Project.createAepLibraryConfiguration(): AEPLibraryExtension {
    val aepConfig = extensions.create<AEPLibraryExtension>("aepLibrary")

    //  Defaults
    aepConfig.compose.convention(false)
    aepConfig.enableSpotless.convention(false)
    aepConfig.enableDokkaDoc.convention(false)
    aepConfig.enableSpotlessPrettierForJava.convention(false)
    aepConfig.enableCheckStyle.convention(false)
    aepConfig.disableCommonDependencies.convention(false)
    aepConfig.enablePlayConsoleVerification.convention(false)

    // Our extensions includes these properties in the gradle.properties file and are relied upon by our build scripts.
    aepConfig.moduleName.convention(providers.gradleProperty(BuildConstants.Publishing.MODULE_NAME_PROPERTY))
    aepConfig.moduleVersion.convention(providers.gradleProperty(BuildConstants.Publishing.MODULE_VERSION_PROPERTY))
    aepConfig.publishing.mavenRepoName.convention(providers.gradleProperty(BuildConstants.Publishing.MAVEN_REPO_NAME_PROPERTY))
    aepConfig.publishing.mavenRepoDescription.convention(providers.gradleProperty(BuildConstants.Publishing.MAVEN_REPO_DESCRIPTION_PROPERTY))

    return aepConfig
}

/**
 * Retrieves the AEP Library configuration extension for the project.
 */
internal val Project.aepLibraryConfiguration: AEPLibraryExtension
    get() {
        return extensions["aepLibrary"] as AEPLibraryExtension
    }

/**
 * Retrieves the Javadoc Jar task for the project.
 */
internal val Project.javadocJar: TaskProvider<Jar>
    get() {
        return if (tasks.findByName(BuildConstants.Tasks.JAVADOC_JAR) != null) {
            tasks.named<Jar>(BuildConstants.Tasks.JAVADOC_JAR)
        } else {
            tasks.register<Jar>(BuildConstants.Tasks.JAVADOC_JAR)
        }
    }

/**
 * Retrieves the Source Jar task for the project.
 */
internal val Project.sourcesJar: Task?
    get() {
        return project.tasks[BuildConstants.Tasks.PHONE_RELEASE_SOURCES_JAR]
    }

/**
 * Retrieves the name of the module's AAR.
 */
internal val Project.moduleAARName: String
    get() {
        return "${aepLibraryConfiguration.moduleName.get()}${BuildConstants.Publishing.MODULE_AAR_NAME_SUFFIX}"
    }

/**
 * Retrieves the path to the module's AAR.
 */
internal val Project.moduleAARPath: String
    get() {
        return "${layout.buildDirectory.asFile.get()}/${BuildConstants.Publishing.MODULE_AAR_OUTPUT_PATH}$moduleAARName"
    }

// Publishing related project extensions.

/**
 * Retrieves the publishing configuration for the project.
 */
internal val Project.publishConfig: PublishConfig
    get() {
        return aepLibraryConfiguration.publishing
    }

/**
 * Verifies if the current build is a JitPack build.
 */
internal fun Project.isJitPackBuild(): Boolean = hasProperty(BuildConstants.Publishing.JITPACK_PROPERTY)

/**
 * Verifies if the current build is a release build.
 */
internal fun Project.isReleaseBuild(): Boolean = hasProperty(BuildConstants.Publishing.RELEASE_PROPERTY)

/**
 * Verifies if the current build is a snapshot build.
 */
internal fun Project.isSnapshotBuild(): Boolean = !isReleaseBuild()

/**
 * Returns the publish URL based on the build type.
 */
internal val Project.publishUrl: String
    get() {
        return if (isSnapshotBuild()) {
            BuildConstants.Publishing.SNAPSHOTS_URL
        } else {
            BuildConstants.Publishing.RELEASES_URL
        }
    }

/**
 * Retrieves the publish group id for the build.
 */
internal val Project.publishGroupId: String
    get() {
        return if (isJitPackBuild()) {
            "com.github.adobe.${publishConfig.gitRepoName.get()}"
        } else {
            BuildConstants.Publishing.ADOBE_GROUP_ID
        }
    }

/**
 * Retrieves the publish artifact id for the build.
 */
internal val Project.publishArtifactId: String
    get() {
        return aepLibraryConfiguration.moduleName.get()
    }

/**
 * Retrieves the publish version name for the build.
 */
internal val Project.publishVersion: String
    get() {
        val moduleVersion = aepLibraryConfiguration.moduleVersion.get()
        return if (isReleaseBuild()) {
            moduleVersion
        } else {
            "$moduleVersion-${BuildConstants.Publishing.SNAPSHOT_SUFFIX}"
        }
    }

/**
 * The android jar path based on the compile sdk version
 */
internal val Project.androidJarPath: String
    get() {
        val android = project.extensions.getByType(BaseExtension::class.java)
        return "${android.sdkDirectory}/platforms/android-${BuildConstants.Versions.COMPILE_SDK_VERSION}/android.jar"
    }

internal val Project.intermediatePathForAEP: String
    get() {
        return "${layout.buildDirectory.asFile.get()}/intermediates/javac/phoneDebug/classes/com/adobe/marketing/mobile"
    }