val PLUGIN_VERSION = "3.4.0"

object Plugins {
    const val ANDROID_GRADLE_PLUGIN_VERSION = "8.2.0"
    const val KOTLIN_GRADLE_PLUGIN_VERSION = "1.8.20"
    const val SPOTLESS_GRADLE_PLUGIN_VERSION = "6.12.0"
    const val DOKKA_GRADLE_PLUGIN_VERSION = "1.9.10"
    const val LICENSE_GRADLE_PLUGIN_VERSION = "0.16.1"
}

plugins {
    `java-gradle-plugin`
    `kotlin-dsl`
    `maven-publish`
    signing
}

repositories {
    gradlePluginPortal()
    google()
    mavenCentral()
    maven {
        url = uri("https://plugins.gradle.org/m2/")
    }
}

dependencies {
    implementation("org.jetbrains.kotlin:kotlin-gradle-plugin:${Plugins.KOTLIN_GRADLE_PLUGIN_VERSION}")
    implementation("com.diffplug.spotless:spotless-plugin-gradle:${Plugins.SPOTLESS_GRADLE_PLUGIN_VERSION}")
    implementation("com.android.tools.build:gradle:${Plugins.ANDROID_GRADLE_PLUGIN_VERSION}")
    implementation("org.jetbrains.dokka:dokka-gradle-plugin:${Plugins.DOKKA_GRADLE_PLUGIN_VERSION}")
    implementation("gradle.plugin.com.hierynomus.gradle.plugins:license-gradle-plugin:${Plugins.LICENSE_GRADLE_PLUGIN_VERSION}")
}

gradlePlugin {
    plugins {
        register("AEPLibraryPlugin") {
            id = "aep-library"
            implementationClass = "com.adobe.marketing.mobile.gradle.AEPLibraryPlugin"
        }
        register("AEPLicensePlugin") {
            id = "aep-license"
            implementationClass = "com.adobe.marketing.mobile.gradle.AEPLicensePlugin"
        }
    }
}

val sourcesJar = tasks.register<Jar>("sourcesJar") {
    archiveClassifier.set("sources")
    from(sourceSets.main.get().allSource)
}

publishing {
    publications {
        create<MavenPublication>("pluginJitpack") {
            groupId = "com.github.adobe.aepsdk-commons"
            artifactId = "aepsdk-gradle-plugin"
            version = PLUGIN_VERSION
            from(components["java"])
            artifact(sourcesJar)
        }
    }
}
