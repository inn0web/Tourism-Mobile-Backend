pipeline {
    agent any

    environment {
        VIRTUAL_ENV = '/opt/myproject/bin/activate'
        PROJECT_DIR = '/opt/myproject/myproject'
        CLONED_PROJECT_DIR = '/opt/myproject/myproject/Tourism-Mobile-Backend'
        ENV_FILE = credentials('eurotrip-env')
    }

    stages {
        stage('Update Repository') {
            steps {
                script {
                    dir("${PROJECT_DIR}/Tourism-Mobile-Backend") {
                        sh '''
                        git pull origin main
                        '''
                    }
                }
            }
        }

        stage('Load .env file from Jenkins secrets') {
            steps {
                sh '''
                    echo "Using env file at $ENV_FILE"
                    cp "$ENV_FILE" /opt/myproject/myproject/Tourism-Mobile-Backend/.env
                '''
            }
        }

        stage('Install Dependencies') {
            steps {
                script {
                    dir(CLONED_PROJECT_DIR) {
                        sh '''#!/bin/bash
                        source /opt/myproject/bin/activate
                        pip install -r requirements.txt
                        '''
                    }
                }
            }
        }
        
        stage('Collect static') {
            steps {
                script {
                    dir(CLONED_PROJECT_DIR) {
                        sh '''#!/bin/bash
                        source /opt/myproject/bin/activate
                        python manage.py collectstatic --noinput
                        '''
                    }
                }
            }
        }

        stage('Run Migrations') {
            steps {
                script {
                    dir(CLONED_PROJECT_DIR) {
                        sh '''#!/bin/bash
                        source /opt/myproject/bin/activate
                        python manage.py makemigrations
                        python manage.py migrate
                        '''
                    }
                }
            }
        }

        stage('Restart Gunicorn') {
            steps {
                script {
                    sh '''#!/bin/bash
                    # Reload systemd to ensure updated service files are applied
                    sudo systemctl daemon-reload
        
                    # Restart Gunicorn services
                    sudo systemctl restart gunicorn-8000
                    sudo systemctl restart gunicorn-8001
                    sudo systemctl restart gunicorn-8002
                    '''
                }
            }
        }
        
        stage('Restart Daphne') {
            steps {
                script {
                    sh '''#!/bin/bash
                    # Reload systemd to ensure updated service files are applied
                    sudo systemctl daemon-reload
        
                    # Restart Gunicorn services
                    sudo systemctl restart daphne.service
                    
                    # sudo systemctl restart redis
                    '''
                }
            }
        }

    }
}