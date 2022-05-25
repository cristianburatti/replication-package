def inject_mvn_dependency(pom_file: str, dependencies: list):
    """
    Inject the JaCoCo dependency/plugin into the pom.xml file if it does not already exist
    :param pom_file: the pom.xml file to inject the dependency into
    :param dependencies: the pre-parsed list of dependencies inside the pom file
    """

    for dependency in dependencies:
        if 'jacoco' in dependency:
            return

    with open(pom_file, 'r') as f:
        content = f.read()

    with open(pom_file, 'w') as f:
        f.write(content
                .replace('</plugins>', jacoco_mvn_plugin + '</plugins>')
                .replace('</dependencies>', jacoco_mvn_dependency + '</dependencies>'))


def inject_gradle_dependency(gradle_file: str):
    """
    Inject the JaCoCo dependency into the gradle file if it does not already exist
    :param gradle_file: the gradle file to inject the dependency into
    """

    with open(gradle_file, 'r') as f:
        content = f.read()
        for line in content.split('\n'):
            if 'jacoco' in line:
                return

    with open(gradle_file, 'a') as f:
        f.write(jacoco_gradle_dependency)


# Dependencies to inject
jacoco_mvn_dependency = """
<dependency>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.5</version>
</dependency>
"""

jacoco_mvn_plugin = """
<plugin>
    <groupId>org.jacoco</groupId>
    <artifactId>jacoco-maven-plugin</artifactId>
    <version>0.8.5</version>
    <executions>
        <execution>
            <goals>
                <goal>prepare-agent</goal>
            </goals>
        </execution>
        <execution>
            <id>report</id>
            <phase>test</phase>
            <goals>
                <goal>report</goal>
            </goals>
        </execution>
    </executions>
</plugin>
"""

jacoco_gradle_dependency = """
apply plugin: 'jacoco'


jacocoTestReport {
    dependsOn test
    reports {
        xml.enabled true
        csv.enabled true
    }
}

test {
    finalizedBy jacocoTestReport
}

jacoco {
    toolVersion = "0.8.7"
}
"""
