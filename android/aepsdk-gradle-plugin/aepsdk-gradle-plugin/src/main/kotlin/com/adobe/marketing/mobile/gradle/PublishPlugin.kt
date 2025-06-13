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

import org.gradle.api.Plugin
import org.gradle.api.Project
import org.gradle.api.publish.PublishingExtension
import org.gradle.api.publish.maven.MavenPublication
import org.gradle.kotlin.dsl.configure
import org.jreleaser.gradle.plugin.JReleaserExtension
import org.jreleaser.model.Http

class PublishPlugin : Plugin<Project> {
    override fun apply(project: Project) {
        // Apply necessary plugins
        project.plugins.apply(BuildConstants.Plugins.MAVEN_PUBLISH)
        project.plugins.apply(BuildConstants.Plugins.J_RELEASER)

        project.afterEvaluate {
            configurePublishing(project)
            configureSigningAndRelease(project)
        }
    }

    private fun configurePublishing(project: Project) {
        val publishingConfig = project.publishConfig
        val publishing = project.extensions.getByType(PublishingExtension::class.java)
        publishing.apply {
            publications {
                create("release", MavenPublication::class.java) {
                    groupId = project.publishGroupId
                    artifactId = project.publishArtifactId
                    version = project.publishVersion

                    artifact(project.moduleAARPath)
                    artifact(project.javadocJar)
                    artifact(project.sourcesJar)

                    pom {
                        name.set(publishingConfig.mavenRepoName.get())
                        description.set(publishingConfig.mavenRepoDescription.get())
                        url.set(BuildConstants.Publishing.DEVELOPER_DOC_URL)

                        licenses {
                            license {
                                name.set(BuildConstants.Publishing.LICENSE_NAME)
                                url.set(BuildConstants.Publishing.LICENSE_URL)
                                distribution.set(BuildConstants.Publishing.LICENSE_DIST)
                            }
                        }

                        developers {
                            developer {
                                id.set(BuildConstants.Publishing.DEVELOPER_ID)
                                name.set(BuildConstants.Publishing.DEVELOPER_NAME)
                                email.set(BuildConstants.Publishing.DEVELOPER_EMAIL)
                            }
                        }

                        val scmConnectionUrl = String.format(BuildConstants.Publishing.SCM_CONNECTION_URL_TEMPLATE, publishingConfig.gitRepoName.get())
                        val scmRepoUrl = String.format(BuildConstants.Publishing.SCM_REPO_URL_TEMPLATE, publishingConfig.gitRepoName.get())

                        scm {
                            connection.set(scmConnectionUrl)
                            developerConnection.set(scmConnectionUrl)
                            url.set(scmRepoUrl)
                        }

                        withXml {
                            val dependenciesNode = asNode().appendNode("dependencies")
                            publishingConfig.mavenDependencies.get().forEach { element ->
                                val dependencyNode = dependenciesNode.appendNode("dependency")
                                dependencyNode.appendNode("groupId", element.groupId)
                                dependencyNode.appendNode("artifactId", element.artifactId)
                                dependencyNode.appendNode("version", element.version)
                            }
                        }
                    }

                    repositories {
                        maven {
                            name = "sonatype"
                            url = project.layout.buildDirectory.dir("staging-deploy").get().asFile.toURI()
                        }
                    }
                }
            }
        }
    }

    private fun configureSigningAndRelease(project: Project) {
        project.extensions.configure<JReleaserExtension> {
            signing {
                setActive("ALWAYS")
                armored.set(true)
                verify.set(true)

                command {
                    executable.set(BuildConstants.Publishing.SIGNING_GNUPG_EXECUTABLE)
                }

                // TODO: Source and verify the PGP signature  parameters
                passphrase.set(BuildConstants.Publishing.SIGNING_GNUPG_PASSPHRASE)
                publicKey.set(BuildConstants.Publishing.SIGNING_GNUPG_KEY_NAME)
                secretKey.set(BuildConstants.Publishing.SIGNING_GNUPG_SECRET_KEYS)
            }

            deploy {
                maven {
                    mavenCentral {
                        create("sonatype") {
                            setActive("ALWAYS")
                            // URL where the MavenCentral service is enabled.
                            url.set(project.publishUrl)
                            authorization.set(Http.Authorization.BEARER)

                            // Signing configuration. See more in signing {}
                            sign.set(true)

                            // Verification of artifacts before publishing.
                            checksums.set(true)
                            sourceJar.set(true)
                            javadocJar.set(true)
                            verifyPom.set(true)
                            applyMavenCentralRules.set(true)

                            stagingRepository("staging-deploy")

                            namespace.set(project.publishGroupId)
                        }
                    }
                }
            }
        }
    }
}
