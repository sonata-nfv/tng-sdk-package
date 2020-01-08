#!groovy

pipeline {
    agent any
    stages {
        stage('Checkout') {
            steps {
                echo 'Stage: Checkout...'
                checkout scm
            }
        }
        stage('Container build') {
            steps {
                echo 'Stage: Building...'
                sh "pipeline/build/build.sh"
            }
        }
        stage('Unittests') {
            steps {
                echo 'Stage: Testing...'
                sh "pipeline/unittest/test.sh"
            }
        }
        stage('Style check') {
            steps {
                echo 'Stage: Style check...'
                sh "pipeline/checkstyle/check.sh"
            }
        }
        stage('Smoke tests') {
            steps {
                echo 'Stage: Smoke test... (not implemented)'
            }
        }
        stage('Promoting/deploying containers to pre-int env') {
            steps {
                echo 'Stage: Promoting containers to pre-integration env'
                sh "pipeline/promote/promote-pre-int.sh"
                sh 'rm -rf tng-devops || true'
                sh 'git clone https://github.com/sonata-nfv/tng-devops.git'
                dir(path: 'tng-devops') {
                    sh 'ansible-playbook roles/sp.yml -i environments -e "target=pre-int-sp component=packager"'
                    sh 'ansible-playbook roles/vnv.yml -i environments -e "target=pre-int-vnv component=packager"'
                }
            }
        }
        stage('Promoting/deploying containers to integration env') {
            when {
                branch 'master'
            }
            steps {
                echo 'Stage: Promoting containers to integration env'
                sh "pipeline/promote/promote-int.sh"
                sh 'rm -rf tng-devops || true'
                sh 'git clone https://github.com/sonata-nfv/tng-devops.git'
                dir(path: 'tng-devops') {
                    sh 'ansible-playbook roles/sp.yml -i environments -e "target=int-sp component=packager"'
                    //sh 'ansible-playbook roles/vnv.yml -i environments -e "target=int-vnv component=packager"'		# no vnv int environment yet
                }
            }
        }
        stage('Container publication') {
            steps {
                echo 'Stage: Container publication...'
                sh "pipeline/publish/publish.sh"
            }
        }
		stage('Promoting release v5.1') {
        when {
            branch 'v5.1'
        }
        stages {
            stage('Generating release') {
                steps {
                    sh 'docker tag registry.sonata-nfv.eu:5000/tng-sdk-package:latest registry.sonata-nfv.eu:5000/tng-sdk-package:v5.1'
                    sh 'docker tag registry.sonata-nfv.eu:5000/tng-sdk-package:latest sonatanfv/tng-sdk-package:v5.1'
                    sh 'docker push registry.sonata-nfv.eu:5000/tng-sdk-package:v5.1'
                    sh 'docker push sonatanfv/tng-sdk-package:v5.1'
                }
            }
        }
    }

    }

    post {
         success {
                 emailext(from: "jenkins@sonata-nfv.eu", 
                 to: "manuel.peuster@upb.de", 
                 subject: "SUCCESS: ${env.JOB_NAME}/${env.BUILD_ID} (${env.BRANCH_NAME})",
                 body: "${env.JOB_URL}")
         }
         failure {
                 emailext(from: "jenkins@sonata-nfv.eu", 
                 to: "manuel.peuster@upb.de", 
                 subject: "FAILURE: ${env.JOB_NAME}/${env.BUILD_ID} (${env.BRANCH_NAME})",
                 body: "${env.JOB_URL}")
         }
    }
}
