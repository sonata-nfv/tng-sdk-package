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
        stage('Container publication') {
            steps {
                echo 'Stage: Container publication... (not implemented)'
            }
        }
        stage('Deploy in integration') {
            steps {
                echo 'Stage: Deploy in integration ... (not implemented)'
            }
        }
        stage('Smoke tests') {
            steps {
                echo 'Stage: Smoke test... (not implemented)'
            }
        }
        stage('Publication') {
            steps {
                echo 'Stage: Publication... (not implemented)'
                // Public container publication
                // Pypi publication
            }
        }
    }
    post {
         success {
                 mail(from: "jenkins@sonata-nfv.eu", 
                 to: "manuel.peuster@upb.de", 
                 subject: "SUCCESS: ${env.JOB_NAME}/${env.BUILD_ID} (${env.BRANCH_NAME})",
                 body: "${env.JOB_URL}")
         }
         failure {
                  mail(from: "jenkins@sonata-nfv.eu", 
                 to: "manuel.peuster@upb.de", 
                 subject: "FAILURE: ${env.JOB_NAME}/${env.BUILD_ID} (${env.BRANCH_NAME})",
                 body: "${env.JOB_URL}")
         }
    }
}
