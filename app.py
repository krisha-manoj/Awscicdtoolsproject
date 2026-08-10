from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html', title='AWS CI/CD Pipeline Project', message='End-to-end CI/CD pipeline built entirely using AWS native tools — CodeCommit, CodeBuild, CodeDeploy, CodePipeline, ECR, and ECS Fargate.')

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
