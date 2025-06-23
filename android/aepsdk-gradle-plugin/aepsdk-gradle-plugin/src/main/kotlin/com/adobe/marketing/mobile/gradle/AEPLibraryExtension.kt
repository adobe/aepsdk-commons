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

import org.gradle.api.Action
import org.gradle.api.model.ObjectFactory
import org.gradle.api.provider.Property
import org.gradle.api.provider.SetProperty
import org.gradle.kotlin.dsl.newInstance
import org.gradle.kotlin.dsl.property
import javax.inject.Inject

internal data class PublishDependency(
    val groupId: String,
    val artifactId: String,
    val version: String
)

open class PublishConfig @Inject constructor(objects: ObjectFactory) {
    /**
     * The Git repository name associated with your project. Ex) "aepsdk-core-android"
     * This name is used by the plugin to generate the Jitpack group id
     * and repository links in the generated POM file.
    */
    val gitRepoName: Property<String> = objects.property()

    /**
     * The Maven repository name associated with your project.
     * If absent, the plugin will search for this property in gradle properties.
     * The build will fail if this value is not provided.
     */
    val mavenRepoName: Property<String> = objects.property()

    /**
     * The Maven repository description associated with your project.
     * If absent, the plugin will search for this property in gradle properties.
     * The build will fail if this value is not provided.
     */
    val mavenRepoDescription: Property<String> = objects.property()

    internal val mavenDependencies: SetProperty<PublishDependency> = objects.setProperty(PublishDependency::class.java)

    /**
     * Adds Maven dependencies to the generated POM file for your project.
     */
    open fun addMavenDependency(groupId: String, artifactId: String, version: String) {
        mavenDependencies.add(PublishDependency(groupId, artifactId, version))
    }

    /**
     * Helpers for common AEP dependencies
     */
    open fun addCoreDependency(version: String) {
        addMavenDependency(BuildConstants.Publishing.ADOBE_GROUP_ID, "core", version)
    }

    open fun addIdentityDependency(version: String) {
        addMavenDependency(BuildConstants.Publishing.ADOBE_GROUP_ID, "identity", version)
    }

    open fun addEdgeDependency(version: String) {
        addMavenDependency(BuildConstants.Publishing.ADOBE_GROUP_ID, "edge", version)
    }

    open fun addEdgeIdentityDependency(version: String) {
        addMavenDependency(BuildConstants.Publishing.ADOBE_GROUP_ID, "edgeidentity", version)
    }
}

open class AEPLibraryExtension @Inject constructor(objects: ObjectFactory) {
    /**
     * Namespace for configuring Android library.
     *
     * This is a required property.
     */
    val namespace: Property<String> = objects.property()

    /**
     * Indicates whether the library uses Jetpack Compose.
     *
     * This property is optional and has a default value of `false`.
     * Set it to `true` if your library uses Jetpack Compose.
     */
    val compose: Property<Boolean> = objects.property()

    /**
     * The name of the module associated with your project. Ex) "core"
     * If absent, the plugin will search for this property in Gradle properties.
     * The build will fail if this value is not provided.
    */
    val moduleName: Property<String> = objects.property()

    /**
     * The version of the module associated with your project. Ex) "x.x.x"
     * If absent, the plugin will search for this property in Gradle properties.
     * The build will fail if this value is not provided.
     */
    val moduleVersion: Property<String> = objects.property()

    /**
     * Indicates whether DokkaDocs should be enabled for generating documentation.
     * If enabled, it sets up DokkaDocs instead of Javadocs.
     * Use this option if you want to generate documentation for Kotlin.
     *
     * This property is optional, and its default value is `false`.
    */
    val enableDokkaDoc: Property<Boolean> = objects.property()

    /**
     * Indicates whether to generate a verification.properties file.
     * If enabled, it creates verification.propeties file containing the token to verify SDK.
     * This can be useful for claiming the SDK on play console.
     *
     * This property is optional, and its default value is `false`.
    */
    val enableSDKVerification: Property<Boolean> = objects.property()

    /**
     * Enables Spotless for linting in your project with specific configurations.
     *
     * For Java files, it uses googleJavaFormat().aosp() for code formatting.
     * For Kotlin files, it uses KtLint for code formatting.
     *
     * This property is optional, and its default value is `false`.
     */
    val enableSpotless: Property<Boolean> = objects.property()

    /**
     * Configures Spotless to use Prettier for formatting Java code.
     *
     * * This property is optional, and its default value is `false`.
     */
    val enableSpotlessPrettierForJava: Property<Boolean> = objects.property()

    /**
     * Enables checkstyle in your project with specific configurations.
     *
     * This property is optional, and its default value is `false`.
     */
    val enableCheckStyle: Property<Boolean> = objects.property()

    /**
     * Disables adding common build dependencies to your project.
     *
     * This property is optional, and its default value is `false`.
     */
    val disableCommonDependencies: Property<Boolean> = objects.property()

    internal val publishing: PublishConfig = objects.newInstance(objects)

    /**
     * Set publishing settings
     */
    fun publishing(action: Action<PublishConfig>) {
        action.execute(publishing)
    }
}
