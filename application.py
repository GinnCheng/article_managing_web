from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from azure.storage.blob import BlobServiceClient
from werkzeug.utils import secure_filename
import os
import uuid

app = Flask(__name__)

# Load configuration from environment variables
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('SQLALCHEMY_DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
AZURE_BLOB_CONNECTION_STRING = os.getenv('AZURE_BLOB_CONNECTION_STRING')
AZURE_BLOB_CONTAINER = os.getenv('AZURE_BLOB_CONTAINER')

# Initialize extensions
db = SQLAlchemy(app)
blob_service_client = BlobServiceClient.from_connection_string(AZURE_BLOB_CONNECTION_STRING)
container_client = blob_service_client.get_container_client(AZURE_BLOB_CONTAINER)

# Define the Article model
class Article(db.Model):
    id = db.Column(db.String, primary_key=True)
    title = db.Column(db.String(255))
    author = db.Column(db.String(255))
    body = db.Column(db.Text)
    image_url = db.Column(db.String)

@app.route('/')
@app.route('/articles')
def list_articles():
    articles = Article.query.all()
    return render_template('article_list.html', articles=articles)

@app.route('/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form['author']
        body = request.form['body']
        image = request.files.get('image')

        image_url = None
        if image and image.filename != '':
            filename = f"{uuid.uuid4()}-{secure_filename(image.filename)}"
            blob_client = container_client.get_blob_client(filename)
            blob_client.upload_blob(image, overwrite=True)
            image_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{AZURE_BLOB_CONTAINER}/{filename}"

        article = Article(
            id=str(uuid.uuid4()),
            title=title,
            author=author,
            body=body,
            image_url=image_url
        )
        db.session.add(article)
        db.session.commit()

        return redirect(url_for('view_article', article_id=article.id))

    return render_template('edit_post.html', article=None)

@app.route('/edit/<article_id>', methods=['GET', 'POST'])
def edit_post(article_id):
    article = Article.query.get(article_id)
    if not article:
        return "Article not found", 404

    if request.method == 'POST':
        article.title = request.form['title']
        article.author = request.form['author']
        article.body = request.form['body']
        image = request.files.get('image')

        if image and image.filename != '':
            filename = f"{uuid.uuid4()}-{secure_filename(image.filename)}"
            blob_client = container_client.get_blob_client(filename)
            blob_client.upload_blob(image, overwrite=True)
            article.image_url = f"https://{blob_service_client.account_name}.blob.core.windows.net/{AZURE_BLOB_CONTAINER}/{filename}"

        db.session.commit()
        return redirect(url_for('view_article', article_id=article.id))

    return render_template('edit_post.html', article=article)

@app.route('/article/<article_id>')
def view_article(article_id):
    article = Article.query.get(article_id)
    if not article:
        return "Article not found", 404
    return render_template('article_view.html', article=article)

@app.route('/delete/<article_id>', methods=['POST'])
def delete_article(article_id):
    article = Article.query.get(article_id)
    if not article:
        return "Article not found", 404

    # Optionally delete blob file
    if article.image_url:
        blob_name = article.image_url.split('/')[-1]
        try:
            container_client.delete_blob(blob_name)
        except Exception:
            pass

    db.session.delete(article)
    db.session.commit()
    return redirect(url_for('list_articles'))


@app.route('/logout')
def logout():
    session.clear()  # optional, in case you're storing anything locally

    aad_logout_url = (
        "https://login.microsoftonline.com/common/oauth2/v2.0/logout"
        "?post_logout_redirect_uri=https://udacitycms-ghesdmddfxbxgjcf.australiaeast-01.azurewebsites.net"
    )

    return redirect(aad_logout_url)


if __name__ == '__main__':
    app.run(debug=True)
