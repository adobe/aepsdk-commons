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

import com.android.build.gradle.LibraryExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.tasks.testing.Test
import org.gradle.kotlin.dsl.configure
import org.gradle.testing.jacoco.plugins.JacocoPlugin
import org.gradle.testing.jacoco.plugins.JacocoTaskExtension
import org.gradle.testing.jacoco.tasks.JacocoReport


internal class JacocoPlugin : Plugin<Project> {
    override fun apply(project: Project) {
        // Apply the Jacoco plugin to the project
        project.plugins.apply(JacocoPlugin::class.java)

        // Register a task for unit test coverage report
        project.tasks.register(BuildConstants.Tasks.UNIT_TEST_COVERAGE_REPORT, JacocoReport::class.java) {
            dependsOn(BuildConstants.Tasks.TEST_PHONE_DEBUG_UNIT_TEST)

            // Configure report formats and requirements
            reports {
                xml.required.set(true)
                html.required.set(true)
                csv.required.set(false)
            }

            // Add source sets for coverage analysis
            addSourceSets()

            // Set the execution data for unit tests
            executionData.setFrom(
                project.fileTree(
                    mapOf(
                        "dir" to "${project.layout.buildDirectory.asFile.get()}",
                        "includes" to listOf(BuildConstants.Reporting.UNIT_TEST_EXECUTION_RESULTS_REGEX)
                    )
                )
            )
        }

        // Register a task for functional test coverage report
        project.tasks.register(BuildConstants.Tasks.FUNCTIONAL_TEST_COVERAGE_REPORT, JacocoReport::class.java) {
            dependsOn(BuildConstants.Tasks.CREATE_PHONE_DEBUG_COVERAGE_REPORT)

            // Configure report formats and requirements
            reports {
                xml.required.set(true)
                html.required.set(true)
                csv.required.set(false)
            }

            // Add source sets for coverage analysis
            addSourceSets()

            // Set the execution data for functional tests
            executionData.setFrom(
                project.fileTree(
                    mapOf(
                        "dir" to "${project.layout.buildDirectory.asFile.get()}",
                        "includes" to listOf(BuildConstants.Reporting.FUNCTIONAL_TEST_EXECUTION_RESULTS_REGEX)
                    )
                )
            )
        }

        project.tasks.withType(Test::class.java) {
            this.extensions.configure(JacocoTaskExtension::class.java) {
                isIncludeNoLocationClasses = true
                excludes = listOf("jdk.internal.*")
            }
        }
    }
}

/**
 * Extension to add the sources to the Jacoco report
 */
private fun JacocoReport.addSourceSets() {
    val android = project.extensions.getByType(LibraryExtension::class.java)

    // Configure source sets for the main code
    val mainSourceSet = android.sourceSets.getByName(BuildConstants.SourceSets.MAIN)
    val mainSourceDir = mainSourceSet.java.srcDirs
    sourceDirectories.setFrom(project.files(mainSourceDir))

    // Configure additional class directories for coverage analysis
    val debugTree = project.fileTree(
        mapOf(
            "dir" to project.intermediatePathForAEP,
            "excludes" to listOf(BuildConstants.Path.ADB_CLASS, BuildConstants.Path.BUILD_CONFIG_CLASS)
        )
    )
    additionalClassDirs.setFrom(project.files(debugTree))

    // Configure source sets for the phone code
    val phoneSourceSet = android.sourceSets.getByName(BuildConstants.SourceSets.PHONE)
    val phoneSourceDir = phoneSourceSet.java.srcDirs
    additionalSourceDirs.setFrom(project.files(phoneSourceDir))
}
