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
import com.diffplug.gradle.spotless.SpotlessExtension
import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.plugins.quality.Checkstyle
import org.gradle.api.plugins.quality.CheckstyleExtension
import org.gradle.api.tasks.javadoc.Javadoc
import org.gradle.configurationcache.extensions.capitalized
import org.gradle.external.javadoc.JavadocMemberLevel
import org.gradle.external.javadoc.StandardJavadocDocletOptions
import org.gradle.kotlin.dsl.configure
import org.gradle.kotlin.dsl.dependencies
import org.gradle.kotlin.dsl.named
import org.gradle.kotlin.dsl.register
import org.jetbrains.dokka.gradle.DokkaTask
import org.jetbrains.kotlin.gradle.tasks.KotlinCompile
import java.io.File
import org.gradle.api.GradleException

class AEPLibraryPlugin : Plugin<Project> {

    // The Kotlin binary compatibility validator doesn't function properly with multiple variants.
    // This check has been added to configure appropriately when validation tasks are run.
    private fun shouldConfigureForAPIValidationTask(project: Project): Boolean {
        return project.gradle.startParameter.taskNames.any {
            it.contains("apiDump") || it.contains("apiCheck")
        }
    }

    override fun apply(project: Project) {
        val extension = project.createAepLibraryConfiguration()

        // Generation of the Play Console verification file is deferred until after the project
        // has been fully evaluated so that build scripts have a chance to configure the
        // `enablePlayConsoleVerification` flag and required properties such as `namespace`.

        // These settings should be applied prior to the Android Gradle plugin evaluating the project.
        project.afterEvaluate {
            configureAndroidNamespace(project, extension)
            if (extension.compose.getOrElse(false)) {
                configureCompose(project)
            }
        }

        // Apply necessary plugins for this project.
        project.plugins.apply(BuildConstants.Plugins.ANDROID_LIBRARY)
        project.plugins.apply(BuildConstants.Plugins.KOTLIN_ANDROID)

        // Don't configure these plugins for validation tasks.
        if (!shouldConfigureForAPIValidationTask(project)) {
            project.plugins.apply(JacocoPlugin::class.java)
            project.plugins.apply(PublishPlugin::class.java)
        }

        // The Android library is set up when you apply this plugin.
        // If necessary, you can customize it in your project's build.gradle file.
        configureAndroidLibrary(project)
        configureKotlin(project)

        // Configure additional settings based on the project's configuration. 
        // These settings include Dokka documentation generation, Spotless code formatting, CheckStyle checks, and common dependencies.
        project.afterEvaluate {
            // Generate Play Console verification file once the DSL has been evaluated
            if (extension.enablePlayConsoleVerification.getOrElse(false)) {
                generatePlayConsoleVerificationFile(project, extension)
            }

            if (!extension.disableCommonDependencies.getOrElse(false)) {
                configureCommonDependencies(project, extension)
            }

            // Other configuration is not needed for validation tasks
            if (shouldConfigureForAPIValidationTask(project)) {
                return@afterEvaluate
            }

            if (extension.enableDokkaDoc.getOrElse(false)) {
                project.plugins.apply(BuildConstants.Plugins.DOKKA)
                configureDokkaDoc(project)
            } else {
                configureJavaDoc(project)
            }

            if (extension.enableSpotless.getOrElse(false)) {
                project.plugins.apply(BuildConstants.Plugins.SPOTLESS)
                configureSpotless(project, extension)
            }

            if (extension.enableCheckStyle.getOrElse(false)) {
                project.plugins.apply(BuildConstants.Plugins.CHECKSTYLE)
                configureCheckStyle(project)
            }

            // Always register the Play Console verification task for manual execution
            if (extension.enablePlayConsoleVerification.getOrElse(false)) {
                configurePlayConsoleVerification(project, extension)
            }

            configureTaskDependencies(project)
        }
    }

    private fun configureCompose(project: Project) {
        val android = project.extensions.getByType(LibraryExtension::class.java)
        android.apply {
            buildFeatures {
                compose = true
            }
            composeOptions {
                kotlinCompilerExtensionVersion = BuildConstants.Versions.COMPOSE_COMPILER
            }
        }
    }

    private fun configureAndroidNamespace(project: Project, extension: AEPLibraryExtension) {
        val android = project.extensions.getByType(LibraryExtension::class.java)
        android.namespace = extension.namespace.get()
    }

    private fun configureAndroidLibrary(project: Project) {
        val android = project.extensions.getByType(LibraryExtension::class.java)
        android.apply {
            compileSdk = BuildConstants.Versions.COMPILE_SDK_VERSION
            defaultConfig {
                minSdk = BuildConstants.Versions.MIN_SDK_VERSION
                testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
                consumerProguardFiles("consumer-rules.pro")
            }
            buildFeatures.buildConfig = true

            compileOptions {
                sourceCompatibility = BuildConstants.Versions.JAVA_SOURCE_COMPATIBILITY
                targetCompatibility = BuildConstants.Versions.JAVA_TARGET_COMPATIBILITY
            }

            // This workaround enables the Kotlin binary compatibility validator to function correctly.
            if (shouldConfigureForAPIValidationTask(project)) {
                sourceSets.named(BuildConstants.SourceSets.MAIN) {
                    java {
                        srcDirs("src/phone/java")
                    }
                }
                return
            }

            flavorDimensionList.add(BuildConstants.BuildDimensions.TARGET)
            productFlavors {
                create(BuildConstants.ProductFlavors.PHONE) {
                    dimension = BuildConstants.BuildDimensions.TARGET
                }
            }

            buildTypes {
                getByName(BuildConstants.BuildTypes.DEBUG) {
                    enableAndroidTestCoverage = true
                    enableUnitTestCoverage = true
                }

                getByName(BuildConstants.BuildTypes.RELEASE) {
                    isMinifyEnabled = false
                    proguardFiles(getDefaultProguardFile("proguard-android.txt"), "proguard-rules.pro")
                }
            }
            publishing {
                singleVariant(BuildConstants.BuildTypes.RELEASE) {
                    withSourcesJar()
                }
            }
            testOptions {
                unitTests.isReturnDefaultValues = true
                unitTests.isIncludeAndroidResources = true

                animationsDisabled = false
                targetSdk = BuildConstants.Versions.TARGET_SDK_VERSION
            }
        }
    }

    private fun configureKotlin(project: Project) {
        // Don't have access to android.kotlinOptions inside the plugin.
        project.tasks.withType(KotlinCompile::class.java).configureEach {
            kotlinOptions {
                jvmTarget = BuildConstants.Versions.KOTLIN_JVM_TARGET
                languageVersion = BuildConstants.Versions.KOTLIN_LANGUAGE_VERSION
                apiVersion = BuildConstants.Versions.KOTLIN_API_VERSION
            }
        }
    }

    private fun configureJavaDoc(project: Project) {
        val android = project.extensions.getByType(LibraryExtension::class.java)
        android.libraryVariants.forEach { variant ->
            project.tasks.register<Javadoc>("create${variant.name.capitalized()}Javadoc") {
                dependsOn(variant.javaCompileProvider)
                source = variant.javaCompileProvider.get().source
                classpath = project.files(variant.javaCompileProvider.get().classpath.files) + project.files(project.androidJarPath)
                exclude(BuildConstants.Path.BUILD_CONFIG_CLASS,
                        BuildConstants.Path.R_CLASS,
                        BuildConstants.Path.INTERNAL_PACKAGES
                        )

                val options = options as StandardJavadocDocletOptions
                options.apply {
                    memberLevel = JavadocMemberLevel.PUBLIC
                    source = "8"
                    links = listOf("https://developer.android.com/reference", "https://docs.oracle.com/javase/8/docs/api/")
                }
            }
        }

        //This task generates a JAR file containing Javadoc documentation to be bundled with the AAR.
        project.javadocJar.configure {
            from(project.tasks.named(BuildConstants.Tasks.CREATE_PHONE_RELEASE_JAVADOC))
            archiveClassifier.set("javadoc")
        }
    }

    private fun configureDokkaDoc(project: Project) {
        val dokkaJavadoc = project.tasks.named<DokkaTask>(BuildConstants.Tasks.DOKKA_JAVADOC)
        dokkaJavadoc.configure {
            dokkaSourceSets.named(BuildConstants.SourceSets.MAIN) {
                jdkVersion.set(8)
                noAndroidSdkLink.set(false)
                perPackageOption {
                    matchingRegex.set(".*\\.internal.*") // proper setting
                    suppress.set(true)
                }
            }

            dokkaSourceSets.named(BuildConstants.SourceSets.PHONE) {
                dependsOn(BuildConstants.SourceSets.MAIN)
                jdkVersion.set(8)
                noAndroidSdkLink.set(false)
                perPackageOption {
                    matchingRegex.set(".*\\.internal.*") // proper setting
                    suppress.set(true)
                }
            }
        }

        // This task generates a JAR file containing Javadoc documentation to be bundled with the AAR.
        project.javadocJar.configure {
            dependsOn(dokkaJavadoc)
            archiveClassifier.set("javadoc")
            from(dokkaJavadoc.get().outputDirectory)
        }

        // This dependency is added specifically for Dokka
        project.dependencies.add(BuildConstants.ProjectConfig.DOKKA, BuildConstants.Dependencies.DOKKA_PLUGIN)

    }

    private fun configureCommonDependencies(project: Project, extension: AEPLibraryExtension) {
        project.dependencies {
            add(BuildConstants.ProjectConfig.IMPLEMENTATION, BuildConstants.Dependencies.ANDROIDX_APPCOMPAT)
            add(BuildConstants.ProjectConfig.IMPLEMENTATION, BuildConstants.Dependencies.KOTLIN_STDLIB_JDK8)

            if (extension.compose.getOrElse(false)) {
                // Jetpack Compose runtime
                add(BuildConstants.ProjectConfig.IMPLEMENTATION, BuildConstants.Dependencies.COMPOSE_RUNTIME)
                // Material UI 1.x
                add(BuildConstants.ProjectConfig.IMPLEMENTATION, BuildConstants.Dependencies.COMPOSE_MATERIAL)
                // Jetpack + Activity integration
                add(BuildConstants.ProjectConfig.IMPLEMENTATION, BuildConstants.Dependencies.ANDROIDX_ACTIVITY_COMPOSE)
                // Jetpack Compose tooling
                add(BuildConstants.ProjectConfig.DEBUG_IMPLEMENTATION, BuildConstants.Dependencies.COMPOSE_UI_TOOLING)

                add(BuildConstants.ProjectConfig.ANDROID_TEST_IMPLEMENTATION, BuildConstants.Dependencies.COMPOSE_UI_TEST_JUNIT4)
                add(BuildConstants.ProjectConfig.ANDROID_TEST_IMPLEMENTATION, BuildConstants.Dependencies.COMPOSE_UI_TEST_MANIFEST)
            }

            add(BuildConstants.ProjectConfig.TEST_IMPLEMENTATION, BuildConstants.Dependencies.JUNIT)
            add(BuildConstants.ProjectConfig.TEST_IMPLEMENTATION, BuildConstants.Dependencies.MOCKITO_CORE)
            add(BuildConstants.ProjectConfig.TEST_IMPLEMENTATION, BuildConstants.Dependencies.MOCKITO_INLINE)
            add(BuildConstants.ProjectConfig.TEST_IMPLEMENTATION, BuildConstants.Dependencies.JSON)
            add(BuildConstants.ProjectConfig.TEST_IMPLEMENTATION, BuildConstants.Dependencies.COMMONS_CODEC)
            add(BuildConstants.ProjectConfig.TEST_IMPLEMENTATION, BuildConstants.Dependencies.ROBOLECTRIC)

            // These dependencies are intended for testing purposes and are included regardless of the Kotlin flag setting.
            add(BuildConstants.ProjectConfig.TEST_IMPLEMENTATION, BuildConstants.Dependencies.MOCKITO_KOTLIN)
            add(BuildConstants.ProjectConfig.TEST_IMPLEMENTATION, BuildConstants.Dependencies.KOTLIN_TEST)
            add(BuildConstants.ProjectConfig.TEST_IMPLEMENTATION, BuildConstants.Dependencies.KOTLINX_COROUTINES_TEST)


            add(BuildConstants.ProjectConfig.ANDROID_TEST_IMPLEMENTATION, BuildConstants.Dependencies.ANDROIDX_TEST_RULES)
            add(BuildConstants.ProjectConfig.ANDROID_TEST_IMPLEMENTATION, BuildConstants.Dependencies.ANDROIDX_TEST_EXT_JUNIT)
            add(BuildConstants.ProjectConfig.ANDROID_TEST_IMPLEMENTATION, BuildConstants.Dependencies.ESPRESSO_CORE)
        }
    }

    private fun configureTaskDependencies(project: Project) {
        val assemblePhone = project.tasks.named(BuildConstants.Tasks.ASSEMBLE_PHONE)
        project.tasks.named(BuildConstants.Tasks.PUBLISH).configure { dependsOn(assemblePhone) }
        project.tasks.named(BuildConstants.Tasks.PUBLISH_MAVEN_LOCAL).configure { dependsOn(assemblePhone)}
        project.tasks.named(BuildConstants.Tasks.PUBLISH_RELEASE_MAVEN_LOCAL).configure { dependsOn(assemblePhone)}
    }

    private fun configureSpotless(project: Project, extension: AEPLibraryExtension) {
        project.extensions.configure<SpotlessExtension> {
            java {
                toggleOffOn(BuildConstants.Formatting.OFF, BuildConstants.Formatting.ON)
                target(BuildConstants.Formatting.JAVA_TARGETS)
                if (extension.enableSpotlessPrettierForJava.getOrElse(false)) {
                    prettier(BuildConstants.Formatting.PRETTIER_CONFIG).config(BuildConstants.Formatting.PRETTIER_FORMAT_OPTIONS)
                } else {
                    googleJavaFormat(BuildConstants.Versions.GOOGLE_JAVA_FORMAT).aosp().reflowLongStrings()
                }

                importOrder()
                removeUnusedImports()
                endWithNewline()
                formatAnnotations()
                licenseHeader(BuildConstants.ADOBE_LICENSE_HEADER)
            }
            kotlin {
                target(BuildConstants.Formatting.KOTLIN_TARGETS)
                ktlint(BuildConstants.Versions.KTLINT)
                endWithNewline()
                licenseHeader(BuildConstants.ADOBE_LICENSE_HEADER)
            }
        }
    }

    private fun configureCheckStyle(project: Project) {
        project.extensions.configure<CheckstyleExtension> {
            config = project.resources.text.fromString(BuildConstants.CheckStyle.CONFIG)
            isIgnoreFailures = false
            isShowViolations = true
            toolVersion = BuildConstants.Versions.CHECKSTYLE_TOOLS
        }

        /** Checkstyle task for new files (not in exclude list). Fail build if a check fails **/
        project.tasks.register<Checkstyle>(BuildConstants.Tasks.CHECKSTYLE) {
            source(BuildConstants.Path.SRC)
            include(BuildConstants.Path.JAVA_FILES)
            exclude(BuildConstants.Path.GEN_FILES)
            exclude(BuildConstants.Path.TEST_FILES)
            exclude(BuildConstants.Path.LEGACY_FILES)
            exclude(BuildConstants.Path.ANDROID_TEST_FILES)
            exclude(BuildConstants.Path.R_CLASS)
            exclude(BuildConstants.Path.BUILD_CONFIG_CLASS)
            classpath = project.files()
        }
    }

    private fun generatePlayConsoleVerificationFile(project: Project, extension: AEPLibraryExtension) {
        val sdkVerificationToken = BuildConstants.Publishing.GOOGLE_TOKEN
            ?: throw GradleException("Play Console verification token is not set. Please set the GOOGLE_TOKEN environment variable or provide it in gradle.properties as PLAY_CONSOLE_VERIFICATION_TOKEN.")

        val packageName = extension.namespace.get() 
            ?: throw GradleException("Android namespace is not set. Please configure the namespace in your build.gradle file.")
        
        val packagePath = packageName.replace(".", "/")
        val outputFile = project.file(BuildConstants.Path.PLAY_CONSOLE_VERIFICATION_PROPERTIES_DIR.format(packagePath))
        outputFile.parentFile.mkdirs()
        outputFile.writeText("token=$sdkVerificationToken\n")
        project.logger.lifecycle("Play Console verification file generated at: ${outputFile.absolutePath}")
    }

    private fun configurePlayConsoleVerification(project: Project, extension: AEPLibraryExtension) {
        project.tasks.register(BuildConstants.Tasks.CONFIGURE_PLAY_CONSOLE_VERIFICATION) {
            group = "verification"
            description = "Regenerates verification.properties for Play SDK verification"

            doLast {
                generatePlayConsoleVerificationFile(project, extension)
            }
        }
    }
}
