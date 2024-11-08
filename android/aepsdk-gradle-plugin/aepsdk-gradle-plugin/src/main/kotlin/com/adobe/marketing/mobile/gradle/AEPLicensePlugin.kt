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

import com.hierynomus.gradle.license.tasks.LicenseFormat
import nl.javadude.gradle.plugins.license.LicenseExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.plugins.ExtensionAware
import org.gradle.kotlin.dsl.get
import org.jetbrains.kotlin.gradle.plugin.extraProperties
import java.util.Calendar

class AEPLicensePlugin: Plugin<Project> {
    override fun apply(project: Project) {
        project.plugins.apply(BuildConstants.Plugins.HIERYNOMUS_LICESNE)

        val license = project.extensions.getByType(LicenseExtension::class.java)
        license.apply {
            header = project.resources.text.fromString(BuildConstants.ADOBE_LICENSE_HEADER_RESOURCES).asFile()
            // This plugin does not understand kts extension
            mapping(mapOf("kts" to "SLASHSTAR_STYLE"))
            skipExistingHeaders = true
        }

        (license as? ExtensionAware)?.extraProperties?.set("year",Calendar.getInstance().get(Calendar.YEAR))

        // Add and maintain licence header to all project files of type XML, YAML, Properties, and Gradle
        project.tasks.register(BuildConstants.Tasks.LICENSE_FORMAT_PROJECT, LicenseFormat::class.java).configure {
            // Todo:- Add additional safeguards. This assumes that the parent directory of project.rootDir is the parent directory of our project.
            source = project.fileTree(project.rootDir.parentFile)
            exclude(
                BuildConstants.Path.IDEA_DIR,
                BuildConstants.Path.BUILD_DIR,
                BuildConstants.Path.GIT_DIR,
                BuildConstants.Path.GRADLE_DIR,
                BuildConstants.Path.GRADLE_WRAPPER_DIR,
                BuildConstants.Path.LOCAL_PROPERTY_FILES,

                // These files are formatted using spotless
                BuildConstants.Path.JAVA_FILES,
                BuildConstants.Path.KOTLIN_FILES,
            )
            include(
                BuildConstants.Path.XML_FILES,
                BuildConstants.Path.YML_FILES,
                BuildConstants.Path.PROPERTY_FILES,
                BuildConstants.Path.GRADLE_KOTLIN_FILES,
            )
        }

        project.tasks[BuildConstants.Tasks.LICENSE_FORMAT].dependsOn(BuildConstants.Tasks.LICENSE_FORMAT_PROJECT)
        project.tasks[BuildConstants.Tasks.LICENSE_FORMAT_PROJECT].group = project.tasks[BuildConstants.Tasks.LICENSE_FORMAT].group
    }
}